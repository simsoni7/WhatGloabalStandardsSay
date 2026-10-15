"""Resumable, frozen-input Bedrock audits; outputs never edit the active catalogue."""
import argparse, concurrent.futures, datetime, hashlib, json, re, threading
from pathlib import Path
from bedrock_gateway import call_stream

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'research/source-store/mece-closure-20261005'
LOCK = threading.Lock()

def read(path):
    return json.loads(path.read_text())

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def execute(job):
    expected = job.get('expected_ids')
    if expected is not None:
        assert len(expected)==len(set(expected)), 'duplicate frozen assigned IDs; regenerate disambiguated inputs before API call'
    prompt = job['instructions'] + '\nFROZEN INPUT:\n' + json.dumps(job['input'], ensure_ascii=False, separators=(',', ':'))
    sha = hashlib.sha256(prompt.encode()).hexdigest()
    folder = RUN / 'reviews' / job['id'] / sha
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / 'proposal.json'
    if output.exists():
        print(job['id'], 'cached', flush=True)
        return
    (folder / 'prompt.txt').write_text(prompt)
    # Refuse accidentally expanded full ontologies before any paid request.
    # This is a transport bound, never a reason to drop review rows: split or
    # select the relevant clauses under a new frozen job identity instead.
    if len(prompt) > job.get('max_prompt_characters', 450000):
        write(folder / 'input-rejection.json', {'reason':'prompt_over_transport_bound',
            'characters':len(prompt),'automatic_adoption':False,'api_called':False})
        raise ValueError('Input too large; prepare bounded frozen inputs')
    previous_attempts=[int(p.stem.split('-')[-1]) for p in folder.glob('attempt-*.json')]
    first_attempt=max(previous_attempts, default=0)+1
    for attempt in range(first_attempt, first_attempt+3):
        attempt_metadata = {'job_id': job['id'], 'model': job['model'], 'attempt': attempt,
                            'prompt_sha256': sha, 'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            'response_preserved': False, 'automatic_adoption': False}
        write(folder / f'attempt-{attempt}.json', attempt_metadata)
        try:
            raw = call_stream(job['model'], prompt, max_tokens=job.get('max_tokens', 24000))
            write(folder / f'raw-{attempt}.json', raw)
            attempt_metadata.update(response_preserved=True, finish_reason=raw['finish_reason'])
            write(folder / f'attempt-{attempt}.json', attempt_metadata)
            assert raw['finish_reason'] == 'stop', 'truncated response retained; retry'
            text = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw['response'].strip())
            result = json.loads(text)
            expected = job.get('expected_ids')
            if expected is not None:
                actual = [r[job['row_key']] for r in result['rows']]
                assert len(actual) == len(expected) and set(actual) == set(expected), 'incomplete/duplicate/unknown rows'
            if job.get('candidate_bindings'):
                for row in result['rows']:
                    binding=job['candidate_bindings'][row[job['row_key']]]
                    assert all(row.get(key)==value for key,value in binding.items()), 'candidate/source/work/label assignment mismatch'
            allowed = set(job.get('work_ids', []))
            for row in result.get('rows', []):
                assert set(row.get('work_ids', [])) <= allowed, 'unknown canonical IDs'
                # Nested proposed results must obey the same provenance/ID
                # contract as top-level rows, even though they stay advisory.
                for component in row.get('atomic_results', []):
                    assert set(component.get('nearest_work_ids', [])) <= allowed, 'unknown nearest work'
                    assert set(component.get('evidence_section_ids', [])) <= set(job.get('sections', {})), 'unknown atomic source section'
                    assert component.get('recommendation') in ['add','covered','gap','excluded'], 'unknown atomic disposition'
                for component in row.get('components', []):
                    if component.get('existing_work_id'):
                        assert component['existing_work_id'] in allowed, 'unknown existing component work'
                if job.get('grounded_section_ids'):
                    ids = row.get('evidence_section_ids', [])
                    assert set(ids) <= set(job['sections']), 'unknown source section ID'
                    assert not row.get('evidence'), 'grounded-ID job must not fabricate quotes'
                    for component in row.get('coverage_components', []):
                        assert set(component.get('work_ids', [])) <= allowed, 'unknown component work'
                        if component.get('source_section_id'):
                            assert component['source_section_id'] in job['sections'], 'unknown component section'
                for quote in row.get('evidence', []):
                    section = job.get('sections', {}).get(quote['section_id'])
                    assert section is not None and quote['quote'] and quote['quote'] in section, 'unverified exact quote'
                if job.get('validate_feature_quotes'):
                    section=job.get('sections',{}).get(row[job['row_key']])
                    assert section is not None, 'feature source section missing'
                    for feature in row.get('features',[]):
                        assert set(feature.get('work_ids',[])) <= allowed, 'unknown nested feature work'
                        assert feature.get('proof_quote') and feature['proof_quote'] in section, 'unverified nested feature quote'
                        assert feature.get('native_expression') and feature['native_expression'] in section, 'unverified nested native label'
                        for claim in feature.get('flow_steps',[])+feature.get('conditions',[]):
                            assert claim.get('proof_quote') and claim['proof_quote'] in section, 'unverified nested condition/step quote'
            write(output, {'job_id': job['id'], 'model': raw['model'], 'prompt_sha256': sha,
                           'usage': raw['usage'], 'result': result, 'automatic_adoption': False})
            print(job['id'], 'complete', flush=True)
            return
        except Exception as exc:
            # Exception text may contain an echoed provider payload; log its type only.
            attempt_metadata.update(error_type=type(exc).__name__)
            if hasattr(exc, 'code'):
                attempt_metadata['http_status'] = exc.code
            write(folder / f'attempt-{attempt}.json', attempt_metadata)
            print(job['id'], 'attempt', attempt, type(exc).__name__, flush=True)
    raise RuntimeError(job['id'] + ' failed after three retained attempts')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('jobs', nargs='*')
    parser.add_argument('--run-dir', type=Path, default=RUN)
    args = parser.parse_args()
    RUN = args.run_dir.resolve()
    files = sorted((RUN / 'inputs').glob('*.json'))
    jobs = [read(f) for f in files if not args.jobs or f.stem in args.jobs]
    assert jobs and (not args.jobs or {j['id'] for j in jobs} == set(args.jobs))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(execute, job): job['id'] for job in jobs}
        failures = []
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception:
                failures.append(futures[future])
    execution_id = hashlib.sha256(json.dumps([j['id'] for j in jobs]).encode()).hexdigest()
    write(RUN / 'executions' / (execution_id + '.json'), {'selected': [j['id'] for j in jobs], 'failed': failures,
                                      'automatic_adoption': False})
    if failures:
        raise SystemExit('Unfinished jobs: ' + ', '.join(failures))
