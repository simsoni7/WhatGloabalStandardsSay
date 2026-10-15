"""Independent UI integration QA for the October 16 change requests.

Uses a built public projection and real catalog/images. Intake POST responses are
mocked deliberately: this checks browser payloads, not production persistence.
"""
import asyncio
import base64
import json
import mimetypes
import pathlib
import struct
import sys
import threading
import zlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
from playwright.async_api import async_playwright

ROOT=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/home/ubuntu/wgss-oct16-preview')
BASE='/WhatGloabalStandardsSay/wgss/'
OUT=pathlib.Path('/home/ubuntu/wgss-oct16-ui-check')
OUT.mkdir(exist_ok=True)

def png(color):
    width,height=120,80
    def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+bytes(color)*width for _ in range(height))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')

class HTTP(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        u=urlsplit(self.path)
        if not u.path.startswith(BASE):self.send_response(404);self.end_headers();return
        name=u.path[len(BASE):] or 'index.html'
        target=(ROOT/name).resolve()
        if not target.is_relative_to(ROOT.resolve()) or not target.is_file():self.send_response(404);self.end_headers();return
        body=target.read_bytes()
        self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(body)));self.end_headers()
        try:self.wfile.write(body)
        except BrokenPipeError:pass

async def run():
    checks=[];errors=[];creates=[];uploads=[]
    def ck(name,ok):
        if not ok:raise AssertionError(name)
        checks.append(name);print(name,flush=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),HTTP)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}'+BASE
    async def intake(route):
        request=route.request
        headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'Content-Type,X-WGSS-Contribution-Token','Access-Control-Allow-Methods':'GET,POST,OPTIONS'}
        if request.method=='OPTIONS':return await route.fulfill(status=204,headers=headers)
        if request.method=='GET':
            resource=urlsplit(request.url).query
            data={'role':'public_reader','publicIntake':True} if 'resource=session' in resource else {'items':[]}
        else:
            body=request.post_data_buffer or b''
            if request.headers.get('content-type','').startswith('application/json'):
                data=json.loads(body)
                creates.append(data)
                data={'item':{'id':f'qa-submission-{len(creates)}','version':1,'status':'pending','files':[]}}
            else:
                uploads.append(body)
                data={'item':{'id':f'qa-submission-{len(creates)}','version':1,'status':'pending','files':[]}}
        await route.fulfill(status=200,body=json.dumps(data),content_type='application/json',headers=headers)
    try:
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(headless=True,args=['--no-sandbox'])
            page=await browser.new_page(viewport={'width':1280,'height':900})
            page.on('pageerror',lambda error:errors.append(str(error)))
            await page.route('https://wgss-public-intake.booknfoto461.chatgpt.site/api/wgss**',intake)
            await page.goto(url+'?tab=words&wordMode=phrases&task=card-application&query=Password#screens',wait_until='networkidle')
            await page.locator('#company-phrases .empty').wait_for()
            text=await page.locator('#results').inner_text()
            ck('empty phrases state has no bulk unfilter button or 736-count escape', '업무 조건 해제하고' not in text and '736건 보기' not in text and '검색된 문구가 없습니다.' in text)
            await page.locator('#company-phrases').get_by_role('button',name='자료 추가하기',exact=True).click()
            await page.locator('#contribution-text').wait_for()
            ck('empty-result contribution preserves query and task', await page.locator('#contribution-text').input_value()=='Password' and await page.evaluate('state.contributionPrefill.task')=='card-application')
            ck('screen and term proposal sub-tabs available',await page.get_by_role('tab',name='금융사 화면 제안').count()==1 and await page.get_by_role('tab',name='금융 용어 제안').count()==1)
            await page.get_by_role('tab',name='금융 용어 제안').click()
            await page.locator('#contribution-term-korean').fill('계좌 개설')
            await page.locator('#contribution-term-english').fill('Open an account')
            await page.locator('#contribution-term-language').select_option('ja')
            await page.locator('#contribution-term-target').fill('口座開設')
            await page.locator('#contribution-source').fill('https://example.org/financial-glossary')
            await page.get_by_role('tab',name='금융사 화면 제안').click()
            await page.get_by_role('tab',name='금융 용어 제안').click()
            ck('switching proposal tabs preserves all term fields',await page.locator('#contribution-term-korean').input_value()=='계좌 개설' and await page.locator('#contribution-term-english').input_value()=='Open an account' and await page.locator('#contribution-term-language').input_value()=='ja' and await page.locator('#contribution-term-target').input_value()=='口座開設')
            await page.locator('#capture-file').set_input_files([{'name':'test-one.png','mimeType':'image/png','buffer':png((220,240,230))},{'name':'test-two.png','mimeType':'image/png','buffer':png((235,240,245))}])
            await page.wait_for_function('captureFiles.length===2&&maskState!==null')
            ck('term proposals support multiple images',await page.locator('[data-capture-edit]').count()==2)
            await page.locator('[name="safeTextConfirmed"]').check()
            await page.get_by_role('button',name='자료 보내기',exact=True).click()
            await page.wait_for_function('document.querySelector("#contribution-status").textContent.includes("접수되었습니다")')
            term=creates[-1]
            ck('a term with images retains translation_issue kind and term fields',term['kind']=='translation_issue' and term['proposalType']=='term' and term['termEnglish']=='Open an account' and term['termKorean']=='계좌 개설' and term['termTarget']=='口座開設' and term['language']=='ja')
            ck('term payload retains source and description',term['sourceUrl']=='https://example.org/financial-glossary' and term['text']=='Password' and term['privacyConfirmed'] is True)
            ck('uploads send only masked roles',len(uploads)==2 and all(b'name="role"\r\n\r\nmasked' in item and b'name="role"\r\n\r\noriginal' not in item for item in uploads))
            ck('submission completion explicitly says staff review before publication','담당자가 검토한 뒤 게시합니다.' in await page.locator('#contribution-status').inner_text())
            await page.goto(url+'?tab=features&task=signup#screens',wait_until='networkidle')
            await page.locator('.wgss-feature-table').wait_for()
            await page.locator('[data-feature-screen]').first.click()
            await page.locator('#detail-dialog[open]').wait_for()
            ck('feature thumbnail opens real screen and flow dialog',await page.locator('#dialog-content .original img').count()==1 and '화면에 쓰인 문구' in await page.locator('#dialog-content').inner_text())
            await page.keyboard.press('Escape')
            await page.locator('#provider').select_option('woori-bank')
            await page.locator('#language').select_option('ko')
            ck('feature table hides raw evidence metadata','normalized_text_character_range' not in await page.locator('#results').inner_text() and 'official_public_function_document' not in await page.locator('#results').inner_text())
            await page.get_by_role('button',name='우리은행 회원가입 화면 추가하기',exact=True).click()
            await page.locator('#contribution-text').wait_for()
            prefill=await page.evaluate('state.contributionPrefill')
            ck('missing company/task cell prepopulates readable contribution',prefill['provider']=='woori-bank' and prefill['task']=='signup' and prefill['language']=='ko' and bool(prefill['workId']) and '우리은행' in await page.locator('#contribution-text').input_value() and '회원가입' in await page.locator('#contribution-text').input_value())
            await page.locator('[name="safeTextConfirmed"]').check()
            await page.get_by_role('button',name='자료 보내기',exact=True).click()
            await page.wait_for_function('document.querySelector("#contribution-status").textContent.includes("접수되었습니다")')
            screen=creates[-1]
            ck('company/task/language/work identifiers survive screen POST payload',screen['provider']=='woori-bank' and screen['task']=='signup' and screen['language']=='ko' and screen['workId']==prefill['workId'] and screen['kind']=='screen')
            await page.set_viewport_size({'width':390,'height':844})
            await page.goto(url+'?tab=features&task=signup#screens',wait_until='networkidle')
            ck('390px feature table scroll remains inside page',await page.evaluate('document.documentElement.scrollWidth<=390'))
            await page.screenshot(path=str(OUT/'features-390.png'))
            await page.locator('[data-feature-add]').first.click()
            ck('390px contribution fits page',await page.evaluate('document.documentElement.scrollWidth<=390'))
            await page.get_by_role('tab',name='금융 용어 제안').click()
            ck('390px term fields fit page',await page.evaluate('document.documentElement.scrollWidth<=390'))
            await page.screenshot(path=str(OUT/'terms-390.png'))
            await page.evaluate('''()=>beginContribution({proposalType:'term',kind:'translation_issue',text:'<img src=x onerror=window.xss=1>',termEnglish:'<svg onload=window.xss=1>',termKorean:'&quot;><script>window.xss=1</script>',termTarget:'<b>test</b>',language:'ja'})''')
            ck('untrusted proposal text is escaped without changing editable values',not await page.evaluate('window.xss||false') and await page.locator('#contribution-term-english').input_value()=='<svg onload=window.xss=1>' and await page.locator('#app svg').count()==0)
            ck('no unhandled browser errors',not errors)
            await browser.close()
    finally:
        server.shutdown();server.server_close()
    report={'passed':len(checks),'checks':checks,'errors':errors,'actualBuiltPublicUi':True,'actualCatalog':True,'intakePostMocked':True,'doesNotClaimProductionPersistence':True,'termPost':creates[0],'screenPost':creates[1]}
    (OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

asyncio.run(run())
