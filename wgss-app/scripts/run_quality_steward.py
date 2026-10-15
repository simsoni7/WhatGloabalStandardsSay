"""Bounded WGSS product-quality review using public structured summaries only.

This script does not collect sources, modify datasets, or publish a site. One
invocation makes at most one gateway request, with no automatic retry.
"""
import argparse
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_ENDPOINT = 'https://frontier-llmgw.aipocnhbank.com/v1/chat/completions'


def public_summary(repo):
    library = json.loads((repo/'dist/data/library.json').read_text())
    products = [{k:p[k] for k in ('id','role','name','target_platforms','feature_count','policy_context_count','record_count','screen_count')} for p in library['products']]
    summary = {
        'scope_status': library['scope_note'], 'counts': library['counts'],
        'standards': library['standard_counts'],
        'products': products,
        'reference_entities': [[f['id'],f['intent_id'],f['product_id'],f['market'],f['language'],f['entity_kind'],f['record_ids']] for f in library['features']+library['policy_contexts']],
        'search_headings': [[t['id'],t['title'],t['feature_ids'],t['policy_context_ids']] for t in library['tasks']],
        'screen_metadata': [{k:r.get(k) for k in ('id','product_id','market','language','channel','evidence_kind','policy_conflict','ui_version','checked_at')} for r in library['records'] if r['type']=='screen'],
        'source_checks': [[r['id'],r['source_state'],r['http_status'],r['checked_at']] for r in library['sources']],
        'quarantine': [[r['id'],r['status'],r['source_id']] for r in library['archived_records']],
        'mapping_groups': list({(m['task_id'],m['concept_id']):(m['task_id'],m['standard'],m['concept_name'],m['role'],m['status']) for m in library['mappings']}.values()),
        'counting_rules': ['Objects, API resources, named schema terms, glossary terms and document sections are distinct units.',
            'Financial provider functions and scheme policy contexts are distinct entity kinds.',
            'Search headings are navigation; legacy 42/176/44 definitions do not determine the active denominator.',
            'Source location checks do not establish semantic truth; interpretation remains editorial.',
            'A changed source is a new revision requiring reassessment, not automatic policy replacement.',
            'Do not infer app UI, OS, eligibility, market, current UI version or compliance from help documents.',
            'No global MECE total, cross-standard equivalence, independent human approval or measured time saving is established.']}
    operation_path=repo/'dist/data/operations.json'
    if operation_path.exists():
        operations=json.loads(operation_path.read_text());audit=operations['audit']
        summary['definition_checkpoint']={k:audit.get(k) for k in ('registered_count','mece_approved_count','counts_by_layer','global_mece_proof','source_scope_ce_accepted','new_provider_collection_allowed')}
        checkpoint=audit.get('closure_progress',{})
        summary['definition_checkpoint'].update(version=operations['version'],review_counts=checkpoint.get('review_counts',{}),
            gates=checkpoint.get('gates',[]),remaining_work=[{k:r[k] for k in ('id','kind','title','next_action')} for r in checkpoint.get('remaining_work',[])])
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['scope', 'coverage'], required=True)
    parser.add_argument('--repo', '--root', dest='repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output-dir', '--output', dest='output_dir', type=Path, required=True)
    parser.add_argument('--max-tokens',type=int,default=6400)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--force', action='store_true', help='Request a new review even when the successful prompt hash is unchanged.')
    args = parser.parse_args()
    summary = public_summary(args.repo)
    expected_counts = dict(summary['counts'])
    if args.phase == 'scope':
        library = json.loads((args.repo/'dist/data/library.json').read_text())
        summary['definition_contexts'] = list({m['concept_id']:(m['standard'],m['concept_name'],m['concept_definition_evidence']['definition']) for m in library['mappings']}.values())
    material = json.dumps(summary, ensure_ascii=False, separators=(',', ':'))
    if len(material.encode()) > 100_000:
        raise SystemExit('Public summary exceeds the bounded input budget; no request sent.')
    scope = '''Critically review the source-backed WGSS graph architecture and standard interpretation boundaries.
Do not reinstate the retired 42 situations or create a universal financial-case count.
ISO BusinessComponents, BIAN service API resources, FIBO terms and NIST identity sections have different scopes.
Check actual provider-function links against original definitions and flag capability vs object vs semantic confusion.
Return Korean JSON only: {"scope_claim":string,"findings":[{"severity":"high|medium|low","entity_ids":[string],"problem":string,"fix":string}],"acceptance_gates":[string],"limitations":[string]}.
At most 7 findings. This is an advisory AI review, never human approval or measured usability evidence.
'''
    coverage = '''Critically review WGSS benchmark usefulness, evidence scope and counting rules.
Return Korean JSON only: {"verified_counts":object,"findings":[{"severity":"high|medium|low","entity_ids":[string],"problem":string,"fix":string}],"release_gates":[string],"limitations":[string]}.
At most 6 findings. Supplied deterministic counts cannot be repaired or recomputed by your answer.
Keep source-backed provider functions, scheme-policy references, documents, screens and search headings separate.
Check empty targets, unknown market/channel/version, source failures, quarantine and policy-conflicting historical screens.
Do not invent a global denominator, case family, provider policy, authenticated native capture or human approval.
'''
    instruction = scope if args.phase == 'scope' else coverage
    prompt = instruction + '\nPUBLIC_SUMMARY\n' + material
    model = 'claude-opus-5' if args.phase == 'scope' else 'claude-sonnet-5'
    snapshot_paths = ['dist/data/library.json','dist/data/standards.json','research/benchmark-targets.json','data/wgss.sqlite']
    source_snapshot = {name: hashlib.sha256((args.repo/name).read_bytes()).hexdigest()
                       for name in snapshot_paths if (args.repo/name).exists()}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    record = {'phase': args.phase, 'model_requested': model,
              'run_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'input_sha256': hashlib.sha256(material.encode()).hexdigest(),
              'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
              'input_bytes': len(material.encode()), 'status': 'prepared',
              'source_snapshot_sha256': source_snapshot,
              'public_summary_only': True, 'image_bytes_sent': False, 'ocr_sent': False,
              'credential_logged': False, 'independent_human_review': False,
              'applied_automatically': False, 'max_gateway_calls': 1}
    output = args.output_dir / f'quality-steward-{args.phase}.json'
    if args.dry_run:
        output = args.output_dir / f'quality-steward-{args.phase}-dry-run.json'
    elif output.exists() and not args.force:
        previous = json.loads(output.read_text())
        if (previous.get('status') == 'succeeded' and previous.get('prompt_sha256') == record['prompt_sha256']
                and previous.get('source_snapshot_sha256') == source_snapshot):
            print(json.dumps({'status': 'reused_successful_review', 'report': str(output),
                              'original_run_at': previous['run_at'], 'tokens_consumed_this_invocation': 0}))
            return
    run_suffix = record['run_at'].replace(':', '').replace('+', '_')
    archive = args.output_dir / f'quality-steward-{args.phase}-{run_suffix}.json'
    def save():
        serialized = json.dumps(record, ensure_ascii=False, indent=2) + '\n'
        output.write_text(serialized)
        if not args.dry_run:
            archive.write_text(serialized)
    if args.dry_run:
        record['status'] = 'dry_run_no_request'; save()
        print(json.dumps({'status': record['status'], 'model': model, 'input_bytes': record['input_bytes']}))
        return
    key = os.environ.get('BEDROCK_API_KEY', '')
    if not key:
        record['status'] = 'blocked_missing_credential'; save()
        raise SystemExit('Gateway credential unavailable; no request sent.')
    endpoint = os.environ.get('WGSS_LLM_CHAT_COMPLETIONS_URL', DEFAULT_ENDPOINT)
    parsed_url = urllib.parse.urlsplit(endpoint)
    if parsed_url.scheme != 'https' or parsed_url.hostname != 'frontier-llmgw.aipocnhbank.com' or parsed_url.path != '/v1/chat/completions':
        raise SystemExit('Gateway endpoint is outside the configured allowlist; no request sent.')
    body = {'model': model, 'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': args.max_tokens,
            'temperature': 1, 'reasoning_effort': 'low'}
    request = urllib.request.Request(endpoint, data=json.dumps(body).encode(),
                                    headers={'Authorization': 'Bearer ' + key,
                                             'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = json.load(response)
    except urllib.error.HTTPError as error:
        record.update(status='failed_http', http_status=error.code); save()
        raise SystemExit(f'Gateway HTTP {error.code}; response body and credential not logged.')
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        record.update(status='failed_transport_or_json', error_type=type(error).__name__); save()
        raise SystemExit('Gateway request failed; no secrets logged.')
    choice = (raw.get('choices') or [{}])[0]
    content = (choice.get('message') or {}).get('content', '')
    if isinstance(content, list):
        content = '\n'.join(x.get('text', '') for x in content if isinstance(x, dict))
    record.update(model_returned=raw.get('model'), usage=raw.get('usage'), finish_reason=choice.get('finish_reason'), http_status=200)
    if key in content:
        record['status'] = 'blocked_secret_echo'; save(); raise SystemExit('Model response blocked.')
    record['raw_gateway_response'] = raw
    if choice.get('finish_reason') == 'length':
        record['status']='rejected_truncated_output';save();raise SystemExit('Truncated response retained; retry with --force and a higher --max-tokens value.')
    candidate = content.strip()
    if candidate.startswith('```'):
        candidate = candidate.split('\n', 1)[1].rsplit('```', 1)[0].strip()
    try:
        review = json.loads(candidate)
        if not isinstance(review, dict) or not isinstance(review.get('findings'), list) or not isinstance(review.get('limitations'), list):
            raise ValueError('Unexpected output shape')
        if len(review['findings']) > (7 if args.phase == 'scope' else 6):
            raise ValueError('Output exceeds finding limit')
    except (ValueError, json.JSONDecodeError):
        record['status'] = 'rejected_invalid_model_json'; save()
        raise SystemExit('Model output rejected; raw response retained for review. No data was changed.')
    aliases = {}
    mismatches = []
    unverified_fields = []
    for field, value in review.get('verified_counts', {}).items():
        mapped_field = aliases.get(field, field)
        expected = expected_counts.get(mapped_field)
        if expected is None:
            unverified_fields.append(field)
        if isinstance(value, (int, float)) and expected is not None and value != expected:
            mismatches.append({'field': field, 'model_value': value, 'deterministic_value': expected})
    record.update(status='succeeded', review=review, numeric_count_mismatches=mismatches,
                  unverified_model_count_fields=unverified_fields,
                  count_checks_apply_to_explicit_verified_counts_only=True); save()
    print(json.dumps({'status': record['status'], 'model': record['model_returned'], 'usage': record['usage'], 'report': str(output)}))


if __name__ == '__main__':
    main()
