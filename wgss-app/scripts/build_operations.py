"""Compile an auditable review catalogue; never turn model proposals into MECE approval.

Private inputs are snapshotted under research/source-store/operation-v12.
Counting, ID assignment, merge resolution and foreign-key checks are deterministic.
"""
import argparse,collections,csv,hashlib,json,re,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads(path.read_text())
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def apply_closure(works,mapping,closure):
    if not closure:return works,mapping,{},[]
    by={w['id']:w for w in works};aliases={r['from']:r['into'] for r in closure['merges']}
    # Later reviews may correct a previously added definition. Register additions
    # before applying their patches; a source-backed addition is not immutable.
    for w in closure['additions']:
        assert w['id'] not in by
        by[w['id']]=w
    def target(i,trail=()):
        assert i not in trail,('closure merge cycle',trail,i)
        return target(aliases[i],trail+(i,)) if i in aliases else i
    for i in aliases:assert target(i) in by
    for patch in closure['edits']:
        w=by[patch['id']];w.update(patch['fields'])
        for k in ['actor_role','object_key','outcome_key','discriminator']:w[k]=key(w[k])
        w['outcome']=w['outcome_key'].replace('_',' ')
        w['actor_label']={'customer':'이용자·권리자','support':'서비스 이용자 또는 지원 담당자','institution':'금융기관 처리 담당자'}[w['layer']]+' · '+w['actor_role'].replace('_',' ')
    for r in closure['merges']:
        old=by[r['from']];dest=by[target(r['from'])]
        dest['input_ids']=list(dict.fromkeys(dest['input_ids']+old['input_ids']))
        dest['refs']=list({(s['id'],s['url'],str(s['locator'])):s for s in dest['refs']+old['refs']}.values())
        dest.setdefault('former_work_ids',[]).append(old['id'])
        dest['review_note']+=' '+r['reason']
    for i in aliases:del by[i]
    # A retired source row must not restore references explicitly replaced or
    # quarantined by a later root review of the surviving definition.
    for patch in closure['edits']:
        if patch['id'] in by and patch.get('reference_override_is_authoritative') and 'refs' in patch['fields']:
            by[patch['id']]['refs']=patch['fields']['refs']
    contexts=closure.get('noncountable_contexts',[])
    redirects={r['id']:r['targets'] for r in contexts}
    for r in contexts:del by[r['id']]
    def targets(i,trail=()):
        assert i not in trail,('closure context cycle',trail,i)
        i=target(i)
        return list(dict.fromkeys(t for j in redirects[i] for t in targets(j,trail+(i,)))) if i in redirects else [i]
    for w in by.values():
        w['boundary']['related_ids']=list(dict.fromkeys(t for i in w['boundary']['related_ids'] for t in targets(i) if t!=w['id']))
        assert set(w['boundary']['related_ids'])<=set(by),('closure orphan',w['id'])
    mapping={i:list(dict.fromkeys(t for old in ts for t in targets(old))) for i,ts in mapping.items()}
    decisions=[{'decision':'검증 후 병합','ids':[r['from'],r['into']],'work_ids':[target(r['from'])],'reason':r['reason'],'basis':['root-closure-20261004']} for r in closure['merges']]
    decisions += [{'decision':'원문 근거·경계 보완','ids':[r['id']],'work_ids':[target(r['id'])],'reason':r['reason'],'basis':['root-closure-20261004']} for r in closure['edits']]
    decisions += [{'decision':'누락 업무 추가','ids':[w['origin_unit_id']],'work_ids':[w['id']],'reason':w['review_note'],'basis':['root-closure-20261004']} for w in closure['additions']]
    decisions += [{'decision':'병합 제안 반려','ids':[r['id']],'work_ids':[target(r['id'])],'reason':r['reason'],'basis':['root-closure-20261004']} for r in closure['rejected_merge_proposals']]
    decisions += [{'decision':'포괄 개념 집계 제외','ids':[r['id']],'work_ids':targets(r['id']),'reason':r['reason'],'basis':['root-closure-20261004']} for r in contexts]
    for r in decisions:r['work_ids']=list(dict.fromkeys(t for i in r['work_ids'] for t in targets(i)))
    # Flat aliases plus explicit context redirects are returned for rebasing earlier ledgers.
    aliases.update(redirects)
    return list(by.values()),mapping,aliases,decisions
def key(value):
    if value is None:return None
    s=re.sub(r'[^\w]+','_',value.strip().lower()).strip('_')
    return 'key_'+s if s and s[0].isdigit() else s
def build(src):
    originals=read(src/'catalogue/candidate-works.json'); by={r['id']:r for r in originals}
    reg=read(src/'catalogue/reference-registry.json')
    proposals=read(src/'review/root-candidate-dispositions.json')
    rows={r['input_id']:r for r in proposals['rows']}
    assert set(rows)==set(by) and len(rows)==len(originals)
    corrections=read(src/'review/external-reference-disposition.json');reg.update(corrections['refs'])
    for fix in corrections['candidate_reference_corrections']:
        for b in originals:
            if b['batch']==fix['batch'] and int(b['id'].rsplit('-',1)[1])==fix['number']:
                b['source_refs']=[r for r in b['source_refs'] if not r['id'].startswith('IFSB:')]+fix['corrected_source_refs']
    units={}; origin_map={}; blockers=[]
    for i,r in rows.items():
        if r['disposition'] in ('keep','unresolved'):
            b=by[i]; c=r.get('canonical') or {'title_ko':b['title_ko'],'role':b['actor_role'],'object':b['object_key'],
                  'result':b['outcome_ko'],'discriminator':b['discriminator_key']}
            units[i]={'proposal':c,'base':b,'decision':r,'child':None};origin_map[i]=[i]
        elif r['disposition']=='split':
            assert len(r['children'])>=2,i
            for ch in r['children']:
                assert ch['proposed_id'] not in units
                units[ch['proposed_id']]={'proposal':ch,'base':by[i],'decision':r,'child':ch}
            origin_map[i]=[ch['proposed_id'] for ch in r['children']]
        elif r['disposition']=='exclude':origin_map[i]=[]
        else:assert r['disposition']=='merge',r
    child_aliases=proposals.get('child_aliases',{})
    for i in child_aliases:
        assert i in units,('unknown child alias',i)
        del units[i]
    def resolve(i,trail=()):
        assert i not in trail,('merge cycle',trail,i)
        if i in child_aliases:return resolve(child_aliases[i]['target_id'],trail+(i,))
        if i in units:return [i]
        r=rows.get(i);assert r,('unknown merge target',i)
        if r['disposition']=='merge':return resolve(r['target_id'],trail+(i,))
        if r['disposition']=='split':
            blockers.append({'kind':'ambiguous_merge_to_split','input_id':trail[0] if trail else i,'target_id':i})
            return [ch['proposed_id'] for ch in r['children']]
        if r['disposition']=='exclude':
            blockers.append({'kind':'merge_target_excluded','input_id':trail[0] if trail else i,'target_id':i});return []
        raise AssertionError(i)
    for i,targets in list(origin_map.items()):
        if rows[i]['disposition']=='split':origin_map[i]=list(dict.fromkeys(t for target in targets for t in resolve(target,(i,))))
    for i,r in rows.items():
        if r['disposition']=='merge':origin_map[i]=resolve(r['target_id'],(i,))
    stable={}; meanings={}
    for i,u in units.items():
        c=u['proposal'];meaning=[key(c['role']),key(c['object']),key(c['result']),key(c.get('discriminator'))]
        signature=json.dumps(meaning,ensure_ascii=False)
        if signature in meanings:
            blockers.append({'kind':'same_normalized_tuple','input_ids':[meanings[signature],i]})
            # Keep both visible until semantic equivalence is adjudicated; never silently deduplicate.
        meanings[signature]=i
        stable[i]='WGSS-'+hashlib.sha256((signature+'|'+i).encode()).hexdigest()[:12].upper()
    reverse=collections.defaultdict(list)
    for i,targets in origin_map.items():
        for t in targets:reverse[t].append(i)
    cats=[('accounts-deposits','계좌·예금·현금'),('payments-cards','지급·송금·카드'),('lending-trade','대출·담보·무역금융'),
          ('investments-custody','투자·외환·수탁'),('insurance-pensions','보험·재보험·연금'),('islamic-virtual','이슬람금융·가상자산'),
          ('identity-support','신원·인증·공통 지원'),('institution-processing','금융기관 처리')]
    works=[]
    for i,u in units.items():
        b=u['base'];c=u['proposal'];r=u['decision'];ch=u['child'];role=c['role'];role_lower=role.lower()
        layer='support' if b['batch']=='identity-support' else ('institution' if b['batch']=='institution-processing' or
           any(t in role_lower for t in ['operator','officer','analyst','administrator','servicer','issuer','custodian','underwriter','lender','assessor','committee','manager','agent bank','trader','market maker','board','factor','insurer']) else 'customer')
        actor_label={'customer':'이용자·권리자','support':'서비스 이용자 또는 지원 담당자','institution':'금융기관 처리 담당자'}[layer]+' · '+role
        refs=[];seen=set();source_gaps=[]
        for orig in reverse[i]:
            if by[orig]['evidence_status']=='source_gap':source_gaps.append({'input_id':orig,'reason':by[orig]['source_gap_ko']})
            for ref in by[orig]['source_refs']:
                if ref['id'] in seen:continue
                seen.add(ref['id']);assert ref['id'] in reg,(orig,ref['id']);rr=reg[ref['id']]
                refs.append({'id':rr['id'],'name':rr['name'],'url':rr['source_url'],'locator':rr['source_locator'],
                    'rationale':ref['rationale_ko'],'source_snapshot_id':rr.get('source_snapshot_id'),
                    'context_requires_review':bool(rr.get('source_context_requires_review')) and not rr['id'].startswith('IFSB:verified:')})
        unresolved=r['disposition']=='unresolved' or bool(source_gaps) or not refs or any(x['context_requires_review'] for x in refs)
        # This status describes definition editing only. MECE gates remain closed below.
        w={'id':stable[i],'title':c['title_ko'],'layer':layer,'category':b['batch'],'actor_role':key(role),'actor_label':actor_label,
          'object_key':key(c['object']),'outcome_key':key(c['result']),'outcome':c['result'], 'discriminator':key(c.get('discriminator')),
          'definition':ch['definition_ko'] if ch else b['definition_ko'],
          'includes':ch['includes_ko'] if ch else b['include_ko'],'excludes':ch['excludes_ko'] if ch else b['exclude_ko'],
          'boundary':{'related_ids':[],'distinction':ch['boundary_ko'] if ch else b['nearest_boundary_ko']['distinction_ko']},
          'refs':refs,'status':'unresolved' if unresolved else 'edited','review_note':r['reason_ko'],
          'source_gaps':source_gaps,'input_ids':reverse[i],'origin_unit_id':i,
          'definition_is_wgss_editorial':True,'independent_human_review':False,'mece_approved':False}
        if r.get('editorial_review_state','').startswith('root_corrected') and not ch:
            w['definition']=f"{c['title_ko']}: {c['result']}라는 직접 결과를 만드는 업무. 직접 대상은 {c['object']}이며 책임 역할은 {role}이다."
            w['includes']=[c['result']+'를 성립시키는 필수 절차'];w['excludes']=['별도 권리·계약·의무에 대한 독립 결과','상태 표현·API 호출·회계분개 자체']
            w['boundary']['distinction']=r['reason_ko']
        if unresolved:w['review_note']+=' 근거·경계 보강 전 MECE 승인에 사용할 수 없습니다.'
        works.append(w)
    # Nearest rows are navigation aids, not assertions of equivalence.
    by_title={by[k]['title_ko']:v for k,v in origin_map.items()}
    for w in works:
        u=units[w['origin_unit_id']];target_title=u['base']['nearest_boundary_ko']['other_work_title_ko']
        w['boundary']['related_ids']=[stable[t] for t in by_title.get(target_title,[]) if t!=w['origin_unit_id']]
        if u['child']:w['boundary']['related_ids']+= [stable[t] for t in origin_map[u['base']['id']] if t!=w['origin_unit_id']]
        w['boundary']['related_ids']=list(dict.fromkeys(w['boundary']['related_ids']))
    additions_path=src/'review/root-additions.json'
    additions=read(additions_path) if additions_path.exists() else {'review_catalogue_additions':[],'decisions':[]}
    for w in additions['review_catalogue_additions']:
        assert w['id'] not in {u['id'] for u in works}
        assert all(r['id'] in reg for r in w['refs'])
        works.append(w)
        if w['origin_unit_id']=='ROOT-MANDATORY-R07':
            w['boundary']['related_ids']=[stable[i] for i in units if i.startswith('investments-custody-') and i.endswith('-46')]
    # A voting mandate is not financial-service account authority; clarify both sides.
    for w in works:
        if w['origin_unit_id']==next(i for i in by if i.startswith('investments-custody-') and i.endswith('-28')):
            w['excludes'].append('주주총회 결의안 투표·투표권 대리인 지정')
    mapping={i:[stable[t] for t in ts] for i,ts in origin_map.items()}
    closure_path=src/'closure-20261004/root/root-closure-dispositions.json'
    closure=read(closure_path) if closure_path.exists() else None
    backbone_path=ROOT/'data/operation-backbone-dispositions.json'
    if backbone_path.exists():
        backbone=read(backbone_path)
        assert closure and backbone['source_version']==closure['new_version']
        for field in ['edits','additions','merges','noncountable_contexts','rejected_merge_proposals']:
            closure[field].extend(backbone.get(field,[]))
        closure['new_version']=backbone['new_version']
        closure['audit_summary']['backbone_review']=backbone['audit_summary']
    works,mapping,closure_aliases,closure_decisions=apply_closure(works,mapping,closure)
    def closure_targets(i,trail=()):
        assert i not in trail,('ledger closure cycle',trail,i)
        if i not in closure_aliases:return [i]
        targets=closure_aliases[i]
        if isinstance(targets,str):targets=[targets]
        return list(dict.fromkeys(t for j in targets for t in closure_targets(j,trail+(i,))))
    input_mapping_gaps=[]
    for override in backbone.get('input_mapping_overrides',[]) if backbone_path.exists() else []:
        assert override['input_id'] in mapping
        assert set(override['work_ids']) <= {w['id'] for w in works}
        mapping[override['input_id']]=override['work_ids']
        if override['state']!='corrected_source_relationship':input_mapping_gaps.append(override)
    reference_file=src/'basis/actual-audit/reference-coverage-after-critical-review.json'
    if not reference_file.exists():reference_file=src/'basis/actual-audit/actual-reference-coverage.json'
    coverage=read(reference_file);matrix=[]
    for r in coverage['records']:
        targets=list(dict.fromkeys(t for i in r['mapped_operation_ids'] for t in mapping.get(i,[])))
        # A partial/name-only/model mapping is never upgraded by successful FK resolution.
        state='검토 필요' if r['disposition']=='unresolved' or (r['disposition']=='mapped' and (not targets or r.get('needs_human_review') or r.get('mapping_basis')!='definition' or r.get('mapping_scope')!='specific_result')) else '연결 제안' if r['disposition']=='mapped' else '제외 제안'
        matrix.append({'id':r['reference_key'],'system':'BIAN','name':r['name'],'url':r['source_url'],'disposition':state,
            'work_ids':targets,'reason':r['reason_ko'],'proposal_disposition':r['disposition'],'editorial_approved':False})
    advisory_path=ROOT/'data/mece-source-advisory-v18.json'
    if advisory_path.exists():
        advisory=read(advisory_path);advisory_rows={r['reference_key']:r for r in advisory['rows']}
        v22_advisory=ROOT/'data/quality-steward-v22-source-dispositions.json'
        if v22_advisory.exists():
            newer=read(v22_advisory)
            advisory_rows.update({r['reference_key']:{**r,'source_review_version':newer['version']} for r in newer['rows']})
        assert len(advisory_rows)==927 and set(advisory_rows)=={r['id'] for r in matrix}
        root_rows={r['reference_key']:r for r in read(ROOT/'data/mece-closure-review.json')['source_dispositions']}
        current_ids={w['id'] for w in works}
        for r in matrix:
            latest=root_rows.get(r['id'],advisory_rows[r['id']]);decision=latest['decision']
            r.update(proposal_disposition=decision,reason=latest['reason'],
                work_ids=list(dict.fromkeys(t for i in latest.get('work_ids',[]) for t in closure_targets(i))),
                root_adjudicated=bool(latest.get('root_adjudicated')),coverage_is_complete=False,
                disposition='제외 제안' if decision in ['excluded_scope','noncountable_context'] else '연결 제안' if decision in ['linked_specific','linked_composed'] else '검토 필요',
                review_version=latest.get('source_review_version',advisory_rows[r['id']].get('source_review_version',advisory['version'])),
                mapping_is_comparison_only=bool(latest.get('mapping_is_comparison_only')))
            assert set(r['work_ids'])<=current_ids,('stale source advisory links',r['id'])
    gaps_file=src/'basis/actual-audit/actual-reported-gap-adjudication.json'
    gaps=read(gaps_file) if gaps_file.exists() else None
    counts=dict(collections.Counter(w['layer'] for w in works));states=dict(collections.Counter(w['status'] for w in works))
    states.setdefault('unresolved',0)
    unresolved=[w['id'] for w in works if w['status']=='unresolved']
    audit={'result_label':'전체 목록을 정리했습니다. MECE 확정은 아직 통과하지 않았습니다.',
       'result_note':f'원 후보 {len(originals)}개를 병합·분리·제외하여 {len(works)}개 정의 항목으로 정리했습니다. 이것은 검토용 등록 수이며 금융 전체의 확정 총수가 아닙니다.',
       'me_status':'보류: 의미 경계의 추가 검토 필요','ce_status':'보류: 원문 미정의·누락·불완전 연결 존재',
       'counts_by_layer':counts,'counts_by_status':states,'input_count':len(originals),'registered_count':len(works),
       'mece_approved_count':0,'reference_count':len(matrix),'source_mapping_proposals':coverage['dispositions'],
       'source_grounded_addition_count':len(additions['review_catalogue_additions'])+(len(closure['additions']) if closure else 0),
       'total_candidates_considered':len(originals)+len(additions['review_catalogue_additions'])+(len(closure['additions']) if closure else 0),
       'reported_gap_count':58,'boundary_fixture_count':30,'external_reference_count':68,
       'source_matrix_states':dict(collections.Counter(r['disposition'] for r in matrix)),
       'global_mece_proof':False,'source_scope_ce_accepted':False,'independent_human_review':False,
       'new_provider_collection_allowed':False,'unresolved_work_ids':unresolved,'compiler_blockers':blockers,
       'input_mapping_gaps':input_mapping_gaps,
       'limitations':['ISO 객체·BIAN 책임·FIBO 개념·NIST 용어의 수는 업무 총수에 더하지 않습니다.',
         '정의 정리 상태는 전체 의미 중복 없음 또는 범위 완전성 승인이 아닙니다.',
         'BIAN 341개 원문 서비스 노드·586개 역량 노드와 공식 릴리스 요약 수의 충돌은 미해결입니다.',
         'FIBO·NIST는 선택 원문을 수록한 상태입니다. ISO·BIAN·FIBO·NIST의 정의 집합을 합산하거나 전체 금융으로 간주하지 않습니다.',
         '원문 정의 TBD·이름/상위 계층만으로 연결한 항목을 CE 통과로 세지 않습니다.',
         '수집 재개는 업무 목록의 ME/CE 판정을 끝낸 뒤입니다. 기존 금융사 사례는 자동으로 이 분모에 연결하지 않습니다.']}
    progress_path=ROOT/'data/mece-closure-review.json'
    if progress_path.exists():
        progress=read(progress_path)
        assert progress['output_version']==closure['new_version']
        assert not progress['automatic_adoption'] and not progress['independent_human_review']
        gates=progress.get('gates',[])
        # A gate can advance only through retained root dispositions. Merely
        # changing definition editing states or finishing a model job is insufficient.
        me=next((g for g in gates if g['id']=='semantic_me'),{})
        ce=next((g for g in gates if g['id']=='source_ce'),{})
        audit['me_status']=me.get('label',audit['me_status'])
        audit['ce_status']=ce.get('label',audit['ce_status'])
        audit['source_scope_ce_accepted']=ce.get('state')=='passed'
        audit['new_provider_collection_allowed']=bool(gates) and all(g['state']=='passed' for g in gates) and not unresolved and not input_mapping_gaps and not blockers
        audit['closure_progress']={'version':progress['version'],'gates':gates,
              'remaining_work':progress.get('remaining_work',[]),'bedrock_jobs':progress.get('bedrock_jobs',[]),
              'source_followups':progress.get('source_followups',[]),
              'review_counts':progress.get('review_counts',{}),
              'definition_source_count':progress.get('definition_source_count'),
              'execution_plan':progress.get('execution_plan',[]),
              'unadjudicated_source_buckets':progress.get('unadjudicated_source_buckets',{}),
              'standards_scope':progress.get('standards_scope',[]),
              'standards_scope_open_tasks':progress.get('standards_scope_open_tasks',[]),
              'v22_source_review':progress.get('v22_source_review'),
              'standard_material_census':progress.get('standard_material_census'),
              'note':'단계 완료·업무 편집·원문 명세 공백·금융 업무 누락은 별도 집계입니다.'}
    decisions=[{'decision':{'keep':'정의 정리 제안','merge':'병합','split':'결과 분리','exclude':'집계 제외','unresolved':'판정 보류'}[r['disposition']],
       'ids':[r['input_id']]+([r['target_id']] if r['target_id'] else []),'work_ids':mapping[r['input_id']],
       'reason':r['reason_ko'],'basis':r['decision_basis']} for r in rows.values()]
    decisions += [{'decision':'분리 자식 병합','ids':[i,a['target_id']],'work_ids':[stable[t] for t in resolve(i)],'reason':a['reason_ko'],'basis':['root-child-equivalence-review-20261004']} for i,a in child_aliases.items()]
    decisions += additions['decisions']
    for r in decisions:r['work_ids']=list(dict.fromkeys(t for i in r['work_ids'] for t in closure_targets(i)))
    decisions += closure_decisions
    if closure:
        audit['closure_summary']=closure['audit_summary']
        audit['closure_root_decisions']={'merges':len(closure['merges']),'definition_edits':len(closure['edits']),'additions':len(closure['additions']),'noncountable_contexts':len(closure.get('noncountable_contexts',[])),'rejected_merges':len(closure['rejected_merge_proposals'])}
    d={'version':closure['new_version'] if closure else 'WGSS-operation-v1.2-review-20261004','scope_note':'행위자 역할 + 직접 대상 + 의도한 결과 + 필요한 의미 구분자로 정리한 검토 목록입니다. 업체 사례·국가·화면 수와 별도 집계합니다.',
       'audit':audit,'categories':[{'id':i,'label':label} for i,label in cats],
       'works':sorted(works,key=lambda w:(next(i for i,(c,_) in enumerate(cats) if c==w['category']),w['title'])),
       'decisions':decisions,'omission_matrix':matrix,'reported_gaps':{'original_reported_gap_count':58,'all_mece_approved':False,'raw_model_advice_not_published':True},
       'provenance':{'candidate_sha256':digest(src/'catalogue/candidate-works.json'),
          'disposition_sha256':digest(src/'review/root-candidate-dispositions.json'),'reference_coverage_sha256':digest(reference_file)}}
    output=ROOT/'dist/data';write(output/'operations.json',d);write(output/'operation-audit.json',{'audit':audit,'input_to_work_ids':mapping,'decisions':decisions,'omission_matrix':matrix})
    with (output/'operations.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['id','title','category','layer','status','actor_role','object_key','outcome','discriminator','definition','includes','excludes','source_urls','input_ids']
        cw=csv.DictWriter(f,fieldnames=fields);cw.writeheader()
        for w in d['works']:
            row={k:w.get(k) or '' for k in fields};row['includes']=' | '.join(w['includes']);row['excludes']=' | '.join(w['excludes']);row['input_ids']=' | '.join(w['input_ids']);row['source_urls']=' | '.join(dict.fromkeys(r['url'] for r in w['refs']))
            # CSV cells are plain text, including downloaded untrusted source strings.
            cw.writerow({k:("'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v) for k,v in row.items()})
    sql=ROOT/'data/operations-review.sqlite';sql.unlink(missing_ok=True)
    with sqlite3.connect(sql) as db:
        db.executescript('PRAGMA foreign_keys=ON;CREATE TABLE operation(id TEXT PRIMARY KEY, status TEXT NOT NULL, body_json TEXT NOT NULL);CREATE TABLE candidate(id TEXT PRIMARY KEY, disposition TEXT NOT NULL, reason TEXT NOT NULL);CREATE TABLE candidate_operation(candidate_id TEXT REFERENCES candidate(id),operation_id TEXT REFERENCES operation(id),PRIMARY KEY(candidate_id,operation_id));CREATE TABLE source_addition(operation_id TEXT PRIMARY KEY REFERENCES operation(id),reason TEXT NOT NULL);CREATE TABLE metadata(key TEXT PRIMARY KEY,value_json TEXT NOT NULL);')
        db.executemany('INSERT INTO operation VALUES(?,?,?)',[(w['id'],w['status'],json.dumps(w,ensure_ascii=False)) for w in works])
        db.executemany('INSERT INTO candidate VALUES(?,?,?)',[(i,r['disposition'],r['reason_ko']) for i,r in rows.items()])
        db.executemany('INSERT INTO candidate_operation VALUES(?,?)',[(i,t) for i,ts in mapping.items() for t in ts])
        all_additions=additions['review_catalogue_additions']+(closure['additions'] if closure else [])
        db.executemany('INSERT INTO source_addition VALUES(?,?)',[(closure_targets(w['id'])[0],w['review_note']) for w in all_additions])
        db.execute('INSERT INTO metadata VALUES(?,?)',('audit',json.dumps(audit,ensure_ascii=False)))
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
    lines=['# WGSS 금융업무 전체 검토 목록','',audit['result_note'],'',f'고객 {counts.get("customer",0)} · 공통 지원 {counts.get("support",0)} · 금융기관 처리 {counts.get("institution",0)}','',
       'ME: 보류. CE: 보류. 승인된 전 세계 금융업무 총수로 사용하지 않는다.','', '| ID | 업무 | 관점 | 상태 |','|---|---|---|---|']
    lines += [f'| {w["id"]} | {w["title"].replace("|","/")} | {w["layer"]} | {w["status"]} |' for w in d['works']]
    (ROOT/'docs/financial-operations-v12.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'registered_work_count':len(works),'counts_by_layer':counts,'counts_by_status':states,'candidate_dispositions':dict(collections.Counter(r['disposition'] for r in rows.values())),'compiler_blockers':blockers,'mece_approved':False},ensure_ascii=False))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=ROOT/'research/source-store/operation-v12');build(ap.parse_args().input)
