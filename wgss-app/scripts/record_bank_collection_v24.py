"""One-time editor decisions for the frozen public collection batch.

The explicit selections below are author decisions, never model adoption.
Run after reviewing the exact native sources and unmodified guide images.
"""
import hashlib,json,re,shutil
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'research/source-store/bank-collection-v24-20261011'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
    ledger_path=ROOT/'data/bank-ui-collection-v24-decisions.json'
    assert not ledger_path.exists(), 'Frozen one-time recording already exists; do not rerun'
    root=read(ROOT/'data/bank-ui-root-decisions.json');work_by={w['id']:w for w in root['catalogue']['works']}
    bank=read(ROOT/'data/bank-ui-benchmark-dispositions.json');original=len(bank['examples']);assert original==15
    source_rows=read(RUN/'sources.json');sources={f'V24:{s["id"]}':s for s in source_rows}
    old=ROOT/'research/source-store/bank-ui-v23-20261011'
    for f in ['sources.json','extra-sources.json','supplement-sources.json','final-sources.json','closure-sources.json','last-proof-sources.json']:
        sources.update({f'V23:{s["id"]}':s for s in read(old/f)})
    def wid(short):
        full='WGSS-UI-'+short;assert full in work_by;return full
    def range_proof(s,text):
        start=s['text'].index(text);return {'kind':'normalized_text_character_range','start':start,'end':start+len(text),'excerpt':text}
    def add(source_id,short_ids,provider_id,provider_name,country,language,expression,meaning,conditions,channel,**extra):
        s=sources[source_id];ids=[wid(id) for id in short_ids]
        b={'id':f'BANK-BENCH-{len(bank["examples"])+1:03d}','source_id':source_id,'ui_work_ids':ids,
           'provider_id':provider_id,'provider_name':provider_name,'country':country,'language':language,
           'channel':channel,'expression':expression,'expression_type':'공식 안내의 기능 표제·설명',
           'meaning':meaning,'conditions':conditions,'source_url':s['url'],'raw_sha256':s['raw_sha256'],
           'text_sha256':hashlib.sha256(s['text'].encode()).hexdigest(),'proof':range_proof(s,expression),
           'collected_at':'2026-10-11','root_function_admitted':True,
           'policy_admission':'only_explicit_qualifications_no_global_policy','evidence_type':'official_public_function_document',
           'observed_app_screen':False,'verified_ui_version':None,'app_os':None,**extra}
        bank['examples'].append(b);return b
    soup=BeautifulSoup((old/'sources/hsbc-uk-ui-inventory.html').read_bytes(),'html.parser')
    # Every selected row independently names its customer action/read result.
    selected={
        (0,1):(['8C8F9954FAF2','591B10169113'],'계좌 잔액과 최근 거래내역 조회'),
        (0,3):(['E7352823594F'],'영국 내 가족·지인에게 송금 요청 제출'),
        (0,9):(['404A86BD87E0'],'향후 잔액 전망 확인; 확정 잔액·보장된 결과와 구분'),
        (0,11):(['01C26F0C8C7B'],'거래·지출 분석 확인'),
        (2,1):(['2425A1EB82D8'],'등록한 정기지급과 직접출금 내역 확인'),
        (2,3):(['87A044308A2E'],'직접출금 등록 취소; 이미 집행된 지급의 환불과 구분'),
        (2,4):(['CC40B2B0BFB3'],'정기지급 지시 중지'),
        (2,5):(['37D8DD5B6DD8'],'정기지급 지시 내용 변경'),
        (4,1):(['B840FB22717E'],'카드 분실·도난 사실 신고'),
        (4,2):(['FEB82BBD0285'],'손상된 카드의 교체 신청'),
        (4,4):(['3F3ACAC7635A'],'직불카드의 도박 거래 제한 설정'),
        (4,5):(['9BA0A71D5DA5'],'카드 활성화'),
        (6,1):(['68F0F9DD4C99'],'주소 변경'),
        (6,6):(['442584678D9F'],'고용·직업정보 변경'),
        (8,1):(['F695E90DA8E7'],'최근 명세서 조회·다운로드·인쇄'),
        (10,1):(['56DCD16215A9'],'기존 주택담보대출의 추가 상환 허용범위 조회'),
        (12,2):(['86F2DD937522'],'신용카드 한도 증액 심사 신청; 승인·변경 효력과 구분'),
        (16,1):(['698D2CE7A1AA'],'개인 대출 신청 제출; 대출계약 체결·실행과 구분'),
        (18,4):(['D621DF37D64F'],'고정금리 저축의 재예치 요청'),
        (20,6):(['2798DFDEFBB6'],'펀드 환매 주문 제출; 매도대금 수취와 구분'),
        (22,2):(['D6C1B099EAED'],'보안 메시지로 금융사에 문의 제출'),
        (24,3):(['1F6480F77F8C'],'온라인 카드 결제 확인 응답; 새로운 송금 요청과 구분')
    }
    native=[]
    for r in root['official_inventory']:
        ti,ri=map(int,[r['id'].split(':')[2],r['id'].split(':')[4]])
        tr=soup.select('table')[ti].select('tr')[ri];cells=tr.find_all(['td','th'])
        label=' '.join(' '.join(cells[0].stripped_strings).split());assert label==r['observed_label']
        channels=[];channel_proofs=[]
        for i,channel in [(1,'app'),(2,'online_banking')]:
            c=cells[i];note=' '.join(c.stripped_strings)
            state='described_available' if c.select('.icon-agree') else 'conditional_description' if note else 'not_available_in_comparison' if c.select('.icon-minimize') else 'unknown'
            channel_proofs.append({'channel':channel,'state':state,'condition_native':note or None,
                'locator':f'table[{ti}].tr[{ri}].cell[{i}]','basis':'official comparison, not direct channel observation'})
            if state in ['described_available','conditional_description']:channels.append(channel)
        if (ti,ri) in selected:
            short_ids,meaning=selected[(ti,ri)];conditions='공식 채널 비교표에서 제공 기능으로 설명한 범위입니다. 이용 자격·처리 기한·계약 효력은 개별 안내에서 추가 확인해야 합니다.'
            if ti==8:conditions+=' 온라인뱅킹 열은 개인대출 명세서를 제외한다고 설명합니다.'
            if ti==18:conditions+=' 고정금리 저축 상품의 재예치 요청에 한정하며 새 계약 성립을 관찰한 결과가 아닙니다.'
            b=add('V23:hsbc-uk-ui-inventory',short_ids,'hsbc-uk','HSBC UK','GB','en',label,meaning,conditions,
                  '공식 기능 비교표 · '+(' / '.join('앱' if c=='app' else '온라인뱅킹' for c in channels)),
                  described_channels=channels,channel_proofs=channel_proofs,native_locator=r['locator'],
                  review_note='실제 버튼을 관찰한 자료가 아닙니다. 기능 표제와 해당 행의 채널 표시를 직접 확인했습니다.')
            decision='admit_function_document';reason='자체 행에서 고객의 요청·조회·변경 기능을 명시한다. 공개 채널 표시와 조건을 함께 보존하고 실행·계약성립·실제 화면을 주장하지 않는다.'
        else:
            b=next((b for b in bank['examples'][:original] if b['provider_id']=='hsbc-uk' and b['expression']==label),None)
            if b:
                b.update(described_channels=channels,channel_proofs=channel_proofs,native_locator=r['locator'])
                decision='retain_prior_document';reason='기존 원문 입증 사례와 동일 표제·동일 업무를 보존한다. 채널 자체 셀을 추가 확인했다.'
            else:decision='not_admitted_this_wave';reason='반복되는 표현·복합 행위·일반 관리 표제·심사/효력 경계 또는 추가 상세 확인 대상. 이번 미채택은 기능 미지원 판정이 아니다.'
        native.append({'source_row_id':r['id'],'root_decision':decision,'example_id':b['id'] if b else None,
                       'reason_ko':reason,'channel_proofs':channel_proofs,'automatic_adoption':False})
    hk='V24:hsbc-hk-zh-guide';images={x['id']:x for x in read(RUN/'guide-images.json')}
    def guide(image_id,labels,description):
        im=images[image_id];assert im['sha256']==hashlib.sha256((ROOT/im['private_path']).read_bytes()).hexdigest()
        src=sources[hk];assert any(a['url']==im['asset_url'] for a in src['images'])
        path=f'evidence/bank-v24/{image_id}.jpg';dest=ROOT/'dist'/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/im['private_path'],dest)
        return {'image_path':path,'image_sha256':im['sha256'],'asset_url':im['asset_url'],'source_locator':im['image_locator'],
                'description_ko':description,'labels':labels,'image_derivation':im['derivation'],
                'visual_review':'root_visual_checked','independent_human_review':False,'source_version':None,
                'screen_role':'action_entry_or_information_view','limitation_ko':'공식 안내의 설명용 이미지. 현재 설치 앱·OS·버전·실제 거래 결과를 관찰하지 않음'}
    hk_specs=[
        (['DB6B889609EF'],'個人預算','재무 예산 설정의 진입점','메뉴에서 예산으로 진입하고 개인 설정으로 예산을 설정·수정한다고 설명합니다.','hk-zh-4',['個人預算'],'예산 메뉴로 진입하는 공식 안내 화면'),
        (['591B10169113'],'查閱交易紀錄','계좌 거래내역 조회','계좌 선택 후 최근 거래를 조회하고 더 이전 거래를 펼치거나 검색할 수 있다고 안내합니다.','hk-zh-5',['戶口資訊','最近交易'],'거래내역 조회 진입과 검색 아이콘 예시'),
        (['8C8F9954FAF2'],'戶口','계좌 잔액 조회','이미지에 계좌의 장부 잔액과 가용 잔액을 구분해 표시합니다. 숫자는 설명용 예시이며 실제 고객 잔액이 아닙니다.','hk-zh-5',['賬面結餘','可用結餘'],'장부 잔액과 가용 잔액을 구분한 공식 예시'),
        (['F695E90DA8E7'],'電子結單及電子通知書','계좌·카드 전자명세서 조회','계좌에서 월을 선택해 명세서를 조회·다운로드하고 카드 화면에서도 전자명세서에 접근한다고 안내합니다.','hk-zh-6',['電子結單及電子通知書'],'카드 전자명세서 진입점 예시'),
        (['314E135C277E'],'繳付款項','신용카드 대금 납부의 진입점','카드 탭에서 대상 신용카드를 선택한 뒤 납부로 진입합니다. 납부가 실행·완료된 화면은 아닙니다.','hk-zh-7',['繳付款項'],'신용카드 납부 버튼의 공식 예시'),
        (['E7352823594F'],'您的滙豐戶口之間','본인 명의 HSBC 계좌 간 송금','홍콩 내·다른 시장에 있는 본인 HSBC 계좌 간 이체를 안내합니다. 타인 수취인 송금과 동일 경로로 일반화하지 마세요.','hk-zh-8',['您的滙豐戶口之間'],'본인 HSBC 계좌 간 이체 메뉴 예시'),
        (['E7496FA3A1FD'],'概覽','투자상품 보유내역 조회','투자 탭에서 상품 유형별 보유내역을 구분합니다. 설명 이미지의 금액·비중·등락은 현재 시세나 고객 성과가 아닙니다.','hk-zh-9',['您的持倉'],'상품 유형별 투자 보유내역 예시')
    ]
    for shorts,expression,meaning,conditions,image_id,labels,description in hk_specs:
        add(hk,shorts,'hsbc-hk','HSBC Hong Kong','HK','zh-Hant',expression,meaning,conditions,'공식 앱 조작 안내 · OS 미확인',
            evidence_type='official_guide_screen',expression_type='공식 안내 문구와 시각 확인한 화면 예시',
            screen_evidence=guide(image_id,labels,description),
            review_note='안내 원문은 화면이 참고·설명용임을 명시합니다. 문서의 단계와 원본 이미지의 표시를 구분해 확인했습니다.')
    add('V24:toss-rate-path',['86F2DD937522'],'toss','토스뱅크','KR','ko','금리인하요구권 신청하기',
        '신용상태 개선을 근거로 기존 대출 금리 인하 심사 요청',
        '문서 작성 기준 2026-09-16. 대출 취급일 당일·동일 일자 심사 완료·연체 등 신청 제한이 있으며 신청해도 거절될 수 있습니다. 인하 확정 문구로 사용하지 마세요.',
        '공식 앱 이용 설명 · 화면 미확인',expression_type='공식 문서에서 설명한 UI 문구',
        flow_steps=['토스 앱에서 토스뱅크로 이동','대출의 관리 메뉴 선택','금리인하요구권 신청 기능 선택'],source_published_at='2026-09-16',
        condition_source_id='V24:toss-rate-cut',condition_proof=range_proof(sources['V24:toss-rate-cut'],'금리인하요구를 할 수 없는 경우'))
    add('V24:kakao-account',['014E9CA936CF'],'kakao','카카오뱅크','KR','ko','계좌개설','카카오뱅크 입출금 계좌 개설 기능',
        '상품 안내는 만 14세 이상 실명의 내국인을 대상으로 설명합니다. 개설 시 금융거래 한도 제한을 원칙으로 안내합니다. 현재 앱의 가입 버튼은 직접 확인하지 않았습니다.',
        '공식 상품 웹 안내 · 앱 기능 설명')
    add('V24:kakao-account',['4012B26180F6'],'kakao','카카오뱅크','KR','ko','계약해지','입출금 통장 계약 종료와 잔여자산 정리',
        '공식 안내는 자동이체·카드 결제 연결의 해제, 실명확인을 근거로 개설한 상품의 해지, 대출 연결계좌 여부 등을 조건으로 설명합니다. 압류 등 출금제한이 있으면 해지·지급이 제한될 수 있습니다. 앱 경로는 미확인입니다.',
        '공식 상품 약관 요약 웹 안내')
    for short,label,meaning in [('F4EC0C60B176','Freeze','카드 일시 사용잠금'),('C45F080F8F9A','Defrost','일시 잠근 카드의 사용정지 해제')]:
        add('V24:monzo-freeze',[short],'monzo','Monzo','GB','en',label,meaning,
            '공식 도움말은 카드 메뉴의 잠금·해제를 함께 설명합니다. 분실·도난 신고 철회나 카드 재발급과 구분합니다. 직접 조작한 결과·현재 앱 버전은 확인하지 않았습니다.',
            '공식 앱 도움말 · 화면 미확인',expression_type='공식 문서에서 설명한 UI 문구',flow_steps=['홈 화면에서 카드 메뉴 선택',meaning+' 기능 선택'])
    # Explicitly adjudicate advisory defects; nested quotes never become trusted evidence.
    model_records=[];model_findings=[]
    valid=set(work_by)
    for p in sorted((RUN/'reviews').glob('*/*/proposal.json')):
        proposal=read(p);model_records.append({k:proposal[k] for k in ['job_id','model','prompt_sha256','usage']})
        result=proposal['result'];job=read(RUN/'inputs'/(proposal['job_id']+'.json'))
        if proposal['job_id']=='collection-strategy':
            for g in result.get('priority_groups',[]):
                unknown=set(g['work_ids'])-valid
                if unknown:model_findings.append({'job_id':proposal['job_id'],'finding':'unknown_priority_ids','values':sorted(unknown),'root_decision':'reject_unknown_ids; author priority list uses only canonical IDs'})
        for row in result.get('rows',[]):
            for f in row.get('features',[]):
                text=job.get('sections',{}).get(row['id'],'')
                if f.get('proof_quote') not in text or f.get('native_expression') not in text:
                    model_findings.append({'job_id':proposal['job_id'],'source_id':row['id'],'finding':'nested_feature_quote_or_label_not_exact','root_decision':'reject_feature_claim; use separately authored exact source proof'})
        model_findings.append({'job_id':proposal['job_id'],'finding':'proposal_reviewed','root_decision':'advisory_only; use explicit native-row and source decisions; never automatically adopt'})
    assert len(model_records)==4
    gap={'id':'V24-GAP-LIMITED-ACCOUNT-REVIEW','label_ko':'한도계좌 제한 해제 심사 신청',
         'source_id':'V24:kakao-limit','source_url':sources['V24:kakao-limit']['url'],
         'proof':range_proof(sources['V24:kakao-limit'],'계좌 관리 > 한도 해제 > 해제 신청하기'),
         'reason_ko':'금융거래 목적 증빙을 제출해 은행이 부과한 제한의 해제를 심사받는 요청입니다. 고객이 자기 안전한도를 직접 바꾸는 업무와 다릅니다. 신원확인·서류 제출 단계만으로도 대체하지 않습니다.',
         'status':'requires_scope_version_and_boundary_review','automatic_adoption':False,
         'nearest_rejected_work_id':wid('DFEB572279B8')}
    ledger={'batch':'bank-collection-v24-20261011','scope_version':'bank-customer-ui-v1','denominator':214,
            'root_approved':True,'automatic_adoption':False,'independent_human_review':False,
            'native_row_dispositions':native,'source_dispositions':[
                {'id':'hsbc-hk-zh-guide','decision':'admit_seven_function_references_with_six_verified_guide_images','rejected_inference':'card block does not identify temporary lock versus loss report'},
                {'id':'toss-rate-cut','decision':'admit_condition_context_only; linked to rate-path function'},
                {'id':'toss-rate-path','decision':'admit_application_only; reject claim of rate reduction guaranteed'},
                {'id':'toss-hours','decision':'operating_hours_context; no blanket work/function admission'},
                {'id':'kakao-limit','decision':'definition_review_gap; reject mapping to customer self-selected limit'},
                {'id':'kakao-account','decision':'admit_account_open_and_qualified_end; reject nav-only group-service admission'},
                {'id':'monzo-freeze','decision':'admit_reversible_freeze_defrost_documented_actions; not lost-report withdrawal'},
                {'id':'wise-send-global','decision':'stage_country_unknown; reject GB inference from company headquarters'}],
            'definition_review_gaps':[gap],'model_runs':model_records,'model_dispositions':model_findings,
            'new_example_ids':[b['id'] for b in bank['examples'][original:]],
            'screen_review_method':'Direct visual inspection of six original official guide images and native original Chinese instructions; no authenticated app access',
            'scope_change':False}
    write(ledger_path,ledger)
    bank['collection_batches']=[{'id':ledger['batch'],'root_decisions':'data/bank-ui-collection-v24-decisions.json','automatic_adoption':False}]
    write(ROOT/'data/bank-ui-benchmark-dispositions.json',bank)
    plan=read(ROOT/'data/bank-ui-collection-plan.json');plan.update(plan_version='collection-v24',reviewed_at='2026-10-11',scope_change=False)
    target_specs=[('toss','토스뱅크','KR',['ko'],'https://www.tossbank.com/'),('kakao','카카오뱅크','KR',['ko'],'https://www.kakaobank.com/'),('woori','우리카드','KR',['ko'],'https://pc.wooricard.com/'),('kb','KB국민은행','KR',['ko'],'https://www.kbstar.com/'),('hsbc-uk','HSBC UK','GB',['en'],'https://www.hsbc.co.uk/'),('monzo','Monzo','GB',['en'],'https://monzo.com/'),('wise','Wise','GB',['en'],'https://wise.com/gb/'),('hsbc-hk','HSBC Hong Kong','HK',['zh-Hant','en'],'https://www.hsbc.com.hk/'),('za-bank','ZA Bank','HK',['zh-Hant','en'],'https://bank.za.group/')] 
    plan['provider_targets']=[{'id':id,'name':name,'country':country,'languages':langs,'official_url':url,
        'channels_ko':'공식 웹·도움말·안내 화면 우선; iOS·Android는 확인 가능한 자료가 있을 때 별도 수집',
        'selection_basis_ko':'공개 공식 자료와 기능 비교를 위한 조사 후보. 시장 대표성·전체 업무 제공을 주장하지 않음.',
        'representativeness_proven':False,'candidate_only':True} for id,name,country,langs,url in target_specs]
    plan['countries']=[{'country':c,'languages':langs,'providers':[t['name'] for t in plan['provider_targets'] if t['country']==c]} for c,langs in [('KR',['ko']),('GB',['en']),('HK',['zh-Hant','en'])]]
    plan['phases']=[
        {'id':'public-census','name_ko':'1. 공개 기능 자료 연결','status_ko':'첫 배치 완료 · 확장 중','exit_condition_ko':'전체 214개 × 3개 국가의 연결·공란을 공개하고, 현지 공식 문서의 기능·언어·채널을 자체 원문으로 확인한다. 공란을 미지원으로 단정하지 않는다.'},
        {'id':'screen-and-policy','name_ko':'2. 화면과 적용 조건 보강','status_ko':'진행 중','exit_condition_ko':'우선 업무의 안내서 화면·실제 UI 표기·조작 경로·예외 조건을 각각 출처에 연결한다. 안내 이미지·마케팅 이미지·직접 앱 캡처를 구분하고 버전 미공개를 표시한다.'},
        {'id':'comparison','name_ko':'3. 현지 플랫폼 비교','status_ko':'다음 단계','exit_condition_ko':'같은 업무·국가에서 둘 이상의 플랫폼을 비교할 때 상품·이용자 역할·조건·증거 종류를 일치시킨다. 미수집은 비교 불가로 표시한다.'},
        {'id':'extend-maintain','name_ko':'4. 국가 확장과 변경 추적','status_ko':'준비','exit_condition_ko':'기존 원문과 새 원문의 해시·수집일·게시 기준일을 보존하고 변경 자료를 재검토한다. 프랑스·동남아·아프리카·중동은 현지 플랫폼 선정 근거와 언어 검토자를 확보한 뒤 추가한다.'},
        {'id':'practitioner-test','name_ko':'5. 실제 화면 설계 과제로 효용 검증','status_ko':'수집 보강 후','exit_condition_ko':'실무자가 업무·국가·플랫폼을 찾아 화면 하나를 만드는 과제에서 탐색 시간, 잘못된 문구·조건 선택, 근거 확인 성공률을 측정한다. 아직 개선 효과를 측정했다고 주장하지 않는다.'}]
    priority=[('계좌·조회·송금',['014E9CA936CF','4012B26180F6','8C8F9954FAF2','591B10169113','E7352823594F','44B3F0605C30','BE3E28DEF349','0E34959F2794','37D8DD5B6DD8','CC40B2B0BFB3','87A044308A2E']),('카드 관리',['3826A2FD05F2','9BA0A71D5DA5','F4EC0C60B176','C45F080F8F9A','B840FB22717E','D4DF22E05F69','FEB82BBD0285','4C651EE831D1','3F3ACAC7635A','ACC94DC0E603']),('대출·이자·명세서·접속',['698D2CE7A1AA','56DCD16215A9','86F2DD937522','628AEBC5DA28','314E135C277E','8AB4CAD58603','F695E90DA8E7','F94E9EA98403','57106ED8458D','8D6F981E0EF8','4C73650B5797'])]
    plan['priority_groups']=[{'name_ko':name,'ui_work_ids':[wid(id) for id in shorts],'basis_ko':'이번 초기 공개 자료 수집의 실무 설계 우선순위이며 이용빈도 통계에 근거한 순위가 아님'} for name,shorts in priority]
    plan['priority_works']=len({id for g in plan['priority_groups'] for id in g['ui_work_ids']})
    plan['definition_review_gaps']=[gap]
    plan['staged_sources']=[{'source_id':'V24:wise-send-global','provider_id':'wise','country':None,'language':'en','state':'country_evidence_needed','source_url':sources['V24:wise-send-global']['url'],'reason_ko':'글로벌 도움말을 영국 전용 UI·조건 사례로 추정하지 않는다.'}]
    plan['latest_execution']={'batch':ledger['batch'],'source_targets':len(source_rows),'successful_snapshots':sum(s['state']=='fetched_pending_review' for s in source_rows),'native_rows_reviewed':len(native),'new_function_examples':len(bank['examples'])-original,'official_guide_images':len(images),'bedrock_successful_jobs':len(model_records),'observed_app_captures':0,'automatic_adoption':False}
    plan['maintenance']={'mode':'manual_batches; no background schedule','recommended_check_cadence':'weekly priority function/guide sources; monthly broader provider inventory','promotion':'changed snapshots require separate source review; never automatically replace accepted claims'}
    write(ROOT/'data/bank-ui-collection-plan.json',plan)
    print(json.dumps({'original_examples':original,'new_examples':len(bank['examples'])-original,'total_examples':len(bank['examples']),'priority_works':plan['priority_works'],'root_decisions':len(native),'guide_images':len(images),'bedrock_jobs':len(model_records)},ensure_ascii=False))
if __name__=='__main__':main()
