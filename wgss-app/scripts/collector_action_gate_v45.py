"""
scripts/collector_action_gate_v45.py

Pure-Python 3, no network, no secrets. Implements a strict human-reviewed
action gate for anchor-navigation CTA actions (goto/click_navigation only).

No automatic adoption of model output. No boolean "approved" fallback.
Everything is re-verified against freshly computed hashes and freshly
parsed HTML at gate time.
"""

import hashlib
import json
import re
import unicodedata
from html.parser import HTMLParser
from typing import NamedTuple
from urllib.parse import urlsplit

ALLOWED_OPS = ("goto", "click_navigation")
ALLOWED_KIND = "anchor_navigation"
# Reserved .example host supports local synthetic validation only.
OFFICIAL_HOSTS = frozenset({"bank.example", "www.capitalone.com", "www.discover.com",
    "www.ally.com", "secure.ally.com", "www.marcus.com", "www.americanexpress.com",
    "www.wellsfargo.com", "apply.wellsfargo.com", "www.natwest.com", "www.barclaycard.co.uk"})

def _normalize_for_review(value):
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[\u2018\u2019\u02BC\u00B4`]", "'", value)
    return re.sub(r"[\u200B-\u200D\uFEFF]", "", value)


FORBIDDEN_TOKEN_RE = re.compile(
    r"\b(button|input|type|fill|submit|login|auth)\b", re.I
)

CONSENT_CONTEXT_RE = re.compile(
    r"(authori[sz]e|consent|agreement"
    r"|by selecting.*disclose"
    r"|carry on.*happy.*(documents|statements)"
    r"|accept.*terms)",
    re.I | re.S,
)

URL_TOKEN_DENY_RE = re.compile(
    r"[?&#](token|credentials?|session[s]?)=", re.I
)


class GateDenied(Exception):
    def __init__(self, reason, boundary_log=None):
        super().__init__(reason)
        self.reason = reason
        self.boundary_log = boundary_log or {}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_text(s: str) -> str:
    return _sha(s.encode("utf-8"))


def _canonical_control_json(control: dict) -> str:
    return json.dumps(control, sort_keys=True, separators=(",", ":"))


def _sha_control(control: dict) -> str:
    return _sha_text(_canonical_control_json(control))


class _AnchorFinder(HTMLParser):
    """Finds whether an exact (href, text) anchor pair exists in HTML."""

    def __init__(self, href, text):
        super().__init__(convert_charrefs=True)
        self.target_href = href
        self.target_text = text
        self._in_target = False
        self._buf = []
        self.found = False
        self.matches = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        attrs_d = dict(attrs)
        href = attrs_d.get("href")
        if href == self.target_href:
            self._in_target = True
            self._buf = []

    def handle_data(self, data):
        if self._in_target:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._in_target:
            text = "".join(self._buf).strip()
            if text == self.target_text.strip():
                self.found = True
                self.matches += 1
            self._in_target = False


def _is_https(url: str) -> bool:
    try:
        parts = urlsplit(url)
    except Exception:
        return False
    return parts.scheme == "https" and bool(parts.netloc)


def _check_no_forbidden_tokens(*strings):
    for s in strings:
        if s and FORBIDDEN_TOKEN_RE.search(s):
            raise GateDenied(
                "forbidden_input_control_token",
                {"stage": "preflight"},
            )


def _check_url_no_tokens(url: str):
    if URL_TOKEN_DENY_RE.search(url or ""):
        raise GateDenied("url_contains_credential_or_session_token",
                          {"stage": "preflight"})


def _validate_snapshot_shape(snapshot: dict):
    required = (
        "source_html", "source_url", "view_text", "control",
        "op", "candidate_kind", "official",
    )
    for k in required:
        if k not in snapshot:
            raise GateDenied(f"snapshot_missing_field:{k}",
                              {"stage": "preflight"})

    if not isinstance(snapshot.get("source_html"), str) or not snapshot["source_html"]:
        raise GateDenied("source_html_required")
    if not isinstance(snapshot.get("view_text"), str) or not snapshot["view_text"].strip():
        raise GateDenied("visible_context_required")
    normalized_view = _normalize_for_review(snapshot["view_text"])
    if CONSENT_CONTEXT_RE.search(normalized_view):
        raise GateDenied("consent_boundary", {"stage": "preflight", "boundary": "consent_or_information_sharing"})
    declared = snapshot.get("source_sha256")
    if declared is not None and declared != _sha_text(snapshot["source_html"]):
        raise GateDenied("forged_declared_source_hash")
    control = snapshot["control"]
    if not isinstance(control, dict):
        raise GateDenied("control_not_dict", {"stage": "preflight"})

    if control.get("tag") != "A":
        raise GateDenied("control_tag_not_anchor", {"stage": "preflight"})

    if snapshot["candidate_kind"] != ALLOWED_KIND:
        raise GateDenied("candidate_kind_not_anchor_navigation",
                          {"stage": "preflight"})

    if snapshot["op"] not in ALLOWED_OPS:
        raise GateDenied("op_not_allowed", {"stage": "preflight"})

    if snapshot.get("official") is not True:
        raise GateDenied("snapshot_not_official", {"stage": "preflight"})

    href = control.get("href")
    text = control.get("text")

    if not isinstance(href, str) or not isinstance(text, str):
        raise GateDenied("control_href_or_text_not_str",
                          {"stage": "preflight"})

    if not _is_https(href):
        raise GateDenied("control_href_not_https", {"stage": "preflight"})

    if not _is_https(snapshot["source_url"]):
        raise GateDenied("source_url_not_https", {"stage": "preflight"})

    source_host = urlsplit(snapshot["source_url"]).hostname
    target_host = urlsplit(href).hostname
    if source_host not in OFFICIAL_HOSTS or target_host not in OFFICIAL_HOSTS:
        raise GateDenied("official_host_not_allowlisted")
    if urlsplit(href).netloc.lower() != urlsplit(snapshot["source_url"]).netloc.lower():
        raise GateDenied("cross_origin_requires_separate_review")
    if CONSENT_CONTEXT_RE.search(_normalize_for_review(text)):
        raise GateDenied("consent_boundary", {"stage": "preflight", "boundary": "consent_or_information_sharing"})
    _check_url_no_tokens(href)
    _check_url_no_tokens(snapshot["source_url"])

    _check_no_forbidden_tokens(
        control.get("tag"), href, text, snapshot.get("op"),
        snapshot.get("candidate_kind"), snapshot["source_url"],
    )

    # Verify anchor actually exists in source_html with exact href+text.
    finder = _AnchorFinder(href, text)
    try:
        finder.feed(snapshot["source_html"])
    except Exception:
        raise GateDenied("source_html_unparseable", {"stage": "preflight"})

    if finder.matches > 1:
        raise GateDenied("ambiguous_duplicate_anchor_requires_review")
    if not finder.found:
        raise GateDenied("anchor_not_found_in_source_html",
                          {"stage": "preflight"})


class ReviewDecision(NamedTuple):
    sha_source_html: str
    sha_view_text: str
    sha_control: str
    observed_href: str
    source_url: str
    op: str
    candidate_kind: str
    reviewer: str
    reason: str


def make_review_decision(snapshot, reviewer, reason) -> ReviewDecision:
    """Runs preflight on snapshot, then builds a bound ReviewDecision."""
    _validate_snapshot_shape(snapshot)
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise GateDenied("reviewer_required")
    if not isinstance(reason, str) or not reason.strip():
        raise GateDenied("reason_required")
    return ReviewDecision(_sha_text(snapshot["source_html"]), _sha_text(snapshot["view_text"]),
                          _sha_control(snapshot["control"]), snapshot["control"]["href"],
                          snapshot["source_url"], snapshot["op"], snapshot["candidate_kind"], reviewer, reason)


def _recompute_and_compare(decision: ReviewDecision, snapshot: dict,
                            stage: str):
    """Recompute hashes/facts from the *current* snapshot and ensure they
    match the decision exactly. Never trusts any pre-supplied hash."""

    _validate_snapshot_shape(snapshot)

    cur_sha_source_html = _sha_text(snapshot["source_html"])
    cur_sha_view_text = _sha_text(snapshot["view_text"])
    cur_sha_control = _sha_control(snapshot["control"])
    cur_href = snapshot["control"]["href"]
    cur_source_url = snapshot["source_url"]
    cur_op = snapshot["op"]
    cur_kind = snapshot["candidate_kind"]

    mismatches = []
    if cur_sha_source_html != decision.sha_source_html:
        mismatches.append("source_html_changed")
    if cur_sha_view_text != decision.sha_view_text:
        mismatches.append("view_text_changed")
    if cur_sha_control != decision.sha_control:
        mismatches.append("control_changed")
    if cur_href != decision.observed_href:
        mismatches.append("href_changed")
    if cur_source_url != decision.source_url:
        mismatches.append("source_url_changed")
    if cur_op != decision.op:
        mismatches.append("op_changed")
    if cur_kind != decision.candidate_kind:
        mismatches.append("candidate_kind_changed")

    if mismatches:
        raise GateDenied(
            "snapshot_decision_mismatch:" + ",".join(mismatches),
            {"stage": stage, "mismatches": mismatches},
        )


def _validate_candidate_matches_decision(candidate: dict,
                                          decision: ReviewDecision,
                                          stage: str):
    if candidate is None:
        raise GateDenied("candidate_none", {"stage": stage})
    if decision is None:
        raise GateDenied("decision_none", {"stage": stage})

    mismatches = []
    if candidate.get("href") != decision.observed_href:
        mismatches.append("candidate_href_mismatch")
    if candidate.get("op") != decision.op:
        mismatches.append("candidate_op_mismatch")
    if candidate.get("candidate_kind") != decision.candidate_kind:
        mismatches.append("candidate_kind_mismatch")

    control = candidate.get("control")
    if not isinstance(control, dict):
        mismatches.append("candidate_control_missing")
    else:
        if _sha_control(control) != decision.sha_control:
            mismatches.append("candidate_control_hash_mismatch")

    if mismatches:
        raise GateDenied(
            "candidate_decision_mismatch:" + ",".join(mismatches),
            {"stage": stage, "mismatches": mismatches},
        )


def queue_gate(candidate, current_snapshot, decision):
    """Gate check before enqueueing an action. Raises GateDenied on
    any issue. Returns True only if fully consistent."""
    if decision is None:
        raise GateDenied("no_reviewed_decision", {"stage": "queue_gate"})
    if not isinstance(decision, ReviewDecision):
        raise GateDenied("decision_wrong_type", {"stage": "queue_gate"})

    _validate_candidate_matches_decision(candidate, decision, "queue_gate")
    _recompute_and_compare(decision, current_snapshot, "queue_gate")
    return True


def execution_gate(candidate, current_snapshot, decision):
    """Gate check immediately before executing an action."""
    if decision is None:
        raise GateDenied("no_reviewed_decision", {"stage": "execution_gate"})
    if not isinstance(decision, ReviewDecision):
        raise GateDenied("decision_wrong_type", {"stage": "execution_gate"})

    _validate_candidate_matches_decision(candidate, decision, "execution_gate")
    _recompute_and_compare(decision, current_snapshot, "execution_gate")
    return True


class ReviewedActionQueue:
    """
    Queue of candidate actions bound to human review decisions.
    Gate is enforced both at enqueue time and at execute time.
    """

    def __init__(self):
        self._items = []
        self.boundary_log = []

    def _log(self, event, detail):
        self.boundary_log.append({"event": event, "detail": detail})

    def enqueue(self, candidate, snapshot, decision):
        try:
            queue_gate(candidate, snapshot, decision)
        except GateDenied as e:
            self._log("enqueue_blocked", {"reason": e.reason, "boundary": e.boundary_log})
            raise

        safe_candidate = {
            "op": candidate["op"],
            "href": candidate["href"],
        }
        self._items.append((safe_candidate, decision))
        self._log("enqueued", {"op": safe_candidate["op"]})
        return len(self._items) - 1

    def execute_next(self, current_snapshot, execute_callback):
        if not self._items:
            raise GateDenied("queue_empty", {"stage": "execute_next"})

        safe_candidate, decision = self._items[0]

        try:
            execution_gate(
                {
                    "op": safe_candidate["op"],
                    "href": safe_candidate["href"],
                    "candidate_kind": decision.candidate_kind,
                    "control": current_snapshot["control"],
                },
                current_snapshot,
                decision,
            )
        except GateDenied as e:
            self._log("execute_blocked", {"reason": e.reason, "boundary": e.boundary_log})
            raise

        self._items.pop(0)
        callback_payload = {
            "op": safe_candidate["op"],
            "href": safe_candidate["href"],
        }
        self._log("executed", {"op": safe_candidate["op"]})
        return execute_callback(callback_payload)
