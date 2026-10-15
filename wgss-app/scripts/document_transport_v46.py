"""
document_transport_v46.py

Reviewed plain-document transport, validated against local synthetic servers.
Separate module from
the frozen collector_action_gate_v45 CTA/anchor gate; this module performs
NO automatic navigation and NO CTA actions. It only:

  1. Performs a single explicit read-only HTTPS GET of a human-approved
     root source URL (read_document).
  2. Verifies an externally produced, independently signed render record
     (Ed25519 signature over exact bytes hash + url + reviewer + reason +
     expiry) before ever allowing HTML to be displayed (render_verified).

No credentials, cookies, auth headers, or redirects are ever sent/followed.
No automatic doc approval. Tests performed no bank requests. No real key material shipped;
callers supply their own Ed25519 public key bytes.
"""

import hashlib
import html.parser
import json
import re
import socket
import time
import urllib.request
import urllib.error
from urllib.parse import urlsplit

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# Frozen gate's allowlist hash binding (reused only as a reference constant;
# we do NOT import/weaken the frozen gate here -- this module is read-only
# and separate).
EXPECTED_GATE_SHA256 = "2b1e91cf50a011a7483243e7c67f02dce35398a7bd32e36c92df4a99db902660"

MAX_BYTES = 2 * 1024 * 1024
MAX_EXPIRES_SECONDS = 300


class DocumentTransportError(Exception):
    pass


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Fail before urllib can request a redirect destination."""
    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        raise DocumentTransportError(f"redirect_refused_{code}")

    def http_error_302(self, req, fp, code, msg, hdrs):
        raise DocumentTransportError(f"redirect_refused_{code}")

    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302
    http_error_308 = http_error_302


class _MetaRefreshStripper(html.parser.HTMLParser):
    """Detects (does not execute) meta-refresh tags for upfront rejection."""

    def __init__(self):
        super().__init__()
        self.found_meta_refresh = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "meta":
            return
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if attr_map.get("http-equiv", "").lower() == "refresh":
            self.found_meta_refresh = True


_META_REFRESH_RE = re.compile(
    r"<meta[^>]+http-equiv\s*=\s*[\"']?refresh[\"']?[^>]*>", re.IGNORECASE
)


def _has_meta_refresh(html_text):
    if _META_REFRESH_RE.search(html_text):
        return True
    parser = _MetaRefreshStripper()
    try:
        parser.feed(html_text)
    except Exception:
        return True
    return parser.found_meta_refresh


def strip_meta_refresh(html_text):
    """Remove meta-refresh tags upfront (regex-based, HTMLParser verified).

    Raises if any remain detectable afterward (defense in depth).
    """
    cleaned = _META_REFRESH_RE.sub("", html_text)
    if _has_meta_refresh(cleaned):
        raise DocumentTransportError("meta_refresh_could_not_be_removed")
    return cleaned


def _reject_forbidden_url_parts(url):
    parts = urlsplit(url)
    if parts.username or parts.password:
        raise DocumentTransportError("credentials_in_url_rejected")
    if "@" in (parts.netloc or ""):
        raise DocumentTransportError("credentials_in_url_rejected")


def _is_loopback_host(host):
    try:
        return host in ("127.0.0.1", "localhost") or socket.inet_aton(host) == socket.inet_aton("127.0.0.1")
    except Exception:
        return host == "127.0.0.1"


def read_document(url, approved_source_url, test_mode=False):
    """Explicit, single, read-only GET. url MUST exactly equal
    approved_source_url (URL-exact human-approved allowrecord). No redirects
    permitted. GET only. No creds/cookies/auth headers. HTTPS required
    unless test_mode=True and host is loopback (explicit local test only).

    Returns dict: {bytes, status, content_type, url, fetched_at}
    """
    if url != approved_source_url:
        raise DocumentTransportError("url_not_exact_match_to_approved_source_url")

    _reject_forbidden_url_parts(url)

    parts = urlsplit(url)
    scheme = parts.scheme.lower()

    if scheme == "https":
        opener = urllib.request.build_opener(NoRedirectHandler)
    elif scheme == "http":
        if not test_mode:
            raise DocumentTransportError("plain_http_rejected_production_requires_https")
        if not _is_loopback_host(parts.hostname or ""):
            raise DocumentTransportError("test_mode_http_restricted_to_loopback_only")
        opener = urllib.request.build_opener(NoRedirectHandler)
    else:
        raise DocumentTransportError("unsupported_scheme")

    req = urllib.request.Request(url, method="GET")
    # No credentials, cookies, auth headers, custom headers of any kind.

    try:
        resp = opener.open(req, timeout=15)
    except urllib.error.HTTPError as e:
        raise DocumentTransportError(f"http_error_{e.code}")
    except DocumentTransportError:
        raise
    except Exception as e:
        raise DocumentTransportError(f"transport_error_{e}")

    try:
        status = resp.status
        content_type = resp.headers.get("Content-Type", "")
        raw = resp.read(MAX_BYTES + 1)
    finally:
        resp.close()

    if status != 200:
        raise DocumentTransportError(f"non_200_status_{status}")
    if "text/html" not in content_type.lower():
        raise DocumentTransportError("non_html_content_type_rejected")
    if len(raw) > MAX_BYTES:
        raise DocumentTransportError("response_exceeds_2mb_cap")

    return {
        "bytes": raw,
        "status": status,
        "content_type": content_type,
        "url": url,
        "fetched_at": time.time(),
    }


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def build_signed_record_payload(document_bytes, url, reviewer, reason, expires_at):
    """Canonical payload bytes to sign; used by test memory-signer and by
    verify_signed_record for exact-bytes consistency."""
    payload = {
        "sha256": sha256_hex(document_bytes),
        "url": url,
        "reviewer": reviewer,
        "reason": reason,
        "expires_at": expires_at,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_signed_record(document_bytes, url, signed_record, public_key_bytes):
    """signed_record: dict with keys sha256,url,reviewer,reason,expires_at,
    signature (hex). Verifies exact-bytes hash match, exact url match,
    expiry <= MAX_EXPIRES_SECONDS from now and not already expired, and
    Ed25519 signature validity. Raises DocumentTransportError on any
    failure. Never auto-approves."""
    required = ("sha256", "url", "reviewer", "reason", "expires_at", "signature")
    for k in required:
        if k not in signed_record:
            raise DocumentTransportError(f"signed_record_missing_field_{k}")

    actual_hash = sha256_hex(document_bytes)
    if signed_record["sha256"] != actual_hash:
        raise DocumentTransportError("signed_record_hash_mismatch")

    if signed_record["url"] != url:
        raise DocumentTransportError("signed_record_url_mismatch")

    if not signed_record.get("reviewer"):
        raise DocumentTransportError("signed_record_missing_reviewer")
    if not signed_record.get("reason"):
        raise DocumentTransportError("signed_record_missing_reason")

    now = time.time()
    expires_at = signed_record["expires_at"]
    if expires_at <= now:
        raise DocumentTransportError("signed_record_already_expired")
    if expires_at - now > MAX_EXPIRES_SECONDS:
        raise DocumentTransportError("signed_record_expiry_too_far_future")

    payload = build_signed_record_payload(
        document_bytes, url, signed_record["reviewer"], signed_record["reason"], expires_at
    )

    try:
        pubkey = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        signature = bytes.fromhex(signed_record["signature"])
        pubkey.verify(signature, payload)
    except InvalidSignature:
        raise DocumentTransportError("signed_record_signature_invalid")
    except Exception as e:
        raise DocumentTransportError(f"signed_record_signature_check_failed_{e}")

    return True


def render_verified(document, signed_record, public_key_bytes):
    """Only entry point allowed to produce 'renderable' sanitized HTML.
    document: result of read_document(). signed_record: externally produced
    signed review record (NOT produced by this module). Never auto-approves.
    """
    verify_signed_record(document["bytes"], document["url"], signed_record, public_key_bytes)

    html_text = document["bytes"].decode("utf-8", errors="replace")
    sanitized = strip_meta_refresh(html_text)

    csp = (
        "default-src 'none'; form-action 'none'; navigate-to 'none'; "
        "sandbox"
    )

    ledger_entry = {
        "url": document["url"],
        "sha256": sha256_hex(document["bytes"]),
        "reviewer": signed_record["reviewer"],
        "reason": signed_record["reason"],
        "approved_at": time.time(),
        "csp": csp,
    }

    return {
        "html": sanitized,
        "csp": csp,
        "javascript_enabled": False,
        "service_workers": "block",
        "bypass_csp": False,
        "ledger_entry": ledger_entry,
    }


class VerifiedDocumentView:
    """Owns a fresh restricted context; use close() after inspecting the page."""
    def __init__(self, context, page, ledger, blocked_requests):
        self.context, self.page = context, page
        self.ledger, self.blocked_requests = ledger, blocked_requests

    def close(self):
        self.context.close()


def render_verified_to_browser(browser, document, signed_record, public_key_bytes):
    """Render the reviewed bytes without fetching the URL in Chromium.

    A new JS-disabled context serves exactly one main-frame GET from memory.
    Every other browser request is denied. This is a plain-document mode;
    original CSS/images and dynamic financial applications are unsupported.
    """
    config = render_verified(document, signed_record, public_key_bytes)
    context = browser.new_context(java_script_enabled=False,
                                  service_workers="block", bypass_csp=False)
    page = context.new_page()
    remaining = [1]
    blocked = []

    def intercept(route):
        req = route.request
        if (remaining[0] == 1 and req.method == "GET" and
                req.url == document["url"] and req.is_navigation_request() and
                req.frame == page.main_frame):
            remaining[0] = 0
            route.fulfill(status=200, body=config["html"], headers={
                "Content-Type": "text/html; charset=utf-8",
                "Content-Security-Policy": config["csp"],
            })
        else:
            blocked.append({"method": req.method, "resource_type": req.resource_type})
            route.abort()

    context.route("**/*", intercept)
    try:
        response = page.goto(document["url"], wait_until="domcontentloaded")
        if response is None or response.status != 200:
            raise DocumentTransportError("verified_render_failed")
        return VerifiedDocumentView(context, page, config["ledger_entry"], blocked)
    except Exception:
        context.close()
        raise
