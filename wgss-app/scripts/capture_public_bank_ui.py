"""Capture root-selected public UI states without credentials or financial submissions."""
import argparse,datetime,hashlib,json
from pathlib import Path
from urllib.parse import urlparse,urlunparse
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--run-dir',type=Path,required=True);a=parser.parse_args();run=a.run_dir.resolve();assert not (run/'FROZEN').exists()
 targets=json.loads((run/'targets.json').read_text());results=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
  for target in targets:
   page_timeout=20000
   assert target['read_only'] and target['credentials_allowed'] is False and target['financial_submission_allowed'] is False
   page=browser.new_page(viewport=target['viewport'],locale=target['locale']);page.set_default_timeout(page_timeout);page.goto(target['url'],wait_until='domcontentloaded',timeout=45000)
   page.wait_for_timeout(1200)
   if page.get_by_role('button',name='Decline optional cookies',exact=True).is_visible():page.get_by_role('button',name='Decline optional cookies',exact=True).click()
   for state in target['states']:
    for action in state.get('actions',[]):
     assert action['kind'] in ['check_public_choice','click_public_choice_label','navigate_without_credentials']
     assert action['root_reviewed'] and action['contains_personal_data'] is False
     page.locator(action['selector']).check() if action['kind']=='check_public_choice' else page.locator(action['selector']).click()
    page.locator(state['wait_for']).wait_for(timeout=20000);assert urlparse(page.url).hostname in target['allowed_hosts']
    raw=page.content().encode();text=' '.join(page.locator('body').inner_text().split());sha=hashlib.sha256(raw).hexdigest();folder=run/'sources'/state['id']/sha;folder.mkdir(parents=True,exist_ok=True);(folder/'rendered.html').write_bytes(raw);(folder/'normalized.txt').write_text(text)
    image=folder/'screen.png';page.screenshot(path=str(image),full_page=True)
    results.append({'id':state['id'],'provider_id':target['provider_id'],'country':target['country'],'language':target['locale'],'ui_work_ids':[target['work_id']],'requested_url':target['url'],'resolved_url':urlunparse(urlparse(page.url)._replace(query='',fragment='')),'title':page.title(),'text':text,'raw_sha256':sha,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'snapshot_path':str(folder.relative_to(R)),'image_path':str(image.relative_to(R)),'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'browser':'chromium','browser_version':browser.version,'host_os':'linux','viewport':target['viewport'],'ui_state':state['state'],'capture_type':'live_public_web','authenticated':False,'credentials_entered':False,'authentication_attempted':False,'financial_form_submitted':False,'navigation_actions':state.get('actions',[]),'cookie_choice':'decline_optional','automatic_adoption':False,'review':'pending_root_visual_and_semantic_review'})
    (run/'captures.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
   page.close()
  browser.close()
 (run/'captures.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');(run/'FROZEN').write_text('Public UI capture snapshots frozen; semantic admission remains separate.\n');print(json.dumps([{'id':x['id'],'title':x['title'],'ui_state':x['ui_state']} for x in results],ensure_ascii=False))
if __name__=='__main__':main()
