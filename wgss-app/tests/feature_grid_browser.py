"""Exercise the company/task grid against the real catalog and screenshot assets."""
import asyncio
import contextlib
import functools
import http.server
import json
import pathlib
import threading
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path('/home/ubuntu/wgss-feature-check')
OUT.mkdir(exist_ok=True)
HTML = r'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>회사별 화면 검수</title><link rel="stylesheet" href="/integration-ui/styles.css"><link rel="stylesheet" href="/integration-ui/features.css"><body><main style="padding:24px;max-width:1400px;margin:auto"><div id="results"></div></main><script>
window.state={catalog:null,provider:'',task:'',query:'',language:'',page:1};
window.esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
window.arr=v=>Array.isArray(v)?v:[];
window.pagination=(total,size=18)=>{const pages=Math.max(1,Math.ceil(total/size));state.page=Math.min(state.page,pages);return total>size?`<div class="pagination"><button data-page="${state.page-1}" ${state.page===1?'disabled':''}>이전</button><span>${state.page} / ${pages}</span><button data-page="${state.page+1}" ${state.page===pages?'disabled':''}>다음</button></div>`:''};
window.openScreen=(id)=>window.opened=id;
window.beginContribution=prefill=>window.prefill=prefill;
document.addEventListener('click',event=>{const button=event.target.closest('[data-page]');if(button){state.page=Number(button.dataset.page);WGSSFeatures.render()}});
</script><script src="/integration-ui/features.js"></script><script>fetch('/integration-data/catalog.json').then(r=>r.json()).then(c=>{state.catalog=c;WGSSFeatures.render();window.ready=true});</script></body></html>'''

async def run():
    checks = []
    errors = []
    def ck(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)
    handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT))
    class Quiet(handler.func):
        def log_message(self,*args): pass
        def translate_path(self,path):
            if path.startswith('/assets/'):
                return str(ROOT/'public'/path.split('?',1)[0].lstrip('/'))
            return super().translate_path(path)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(headless=True,args=['--no-sandbox'])
            page=await browser.new_page(viewport={'width':1440,'height':1000})
            page.on('pageerror',lambda e:errors.append(str(e)))
            await page.route('**/feature-check',lambda route:route.fulfill(body=HTML,content_type='text/html'))
            await page.goto(f'http://127.0.0.1:{server.server_port}/feature-check')
            await page.wait_for_function('window.ready')
            ck('124 practitioner tasks, all 50 companies, 8 columns per page', '124개 업무 · 50개 회사' in await page.locator('#results').inner_text() and await page.locator('thead th').count()==9)
            ck('real images are present',await page.locator('.wgss-feature-image img').count()>0)
            ck('image cells use exact explicit company and task connections', await page.evaluate('''()=>[...document.querySelectorAll('[data-feature-screen]')].every(button=>{const cell=button.closest('td'),row=state.catalog.screens.find(row=>row.id===button.dataset.featureScreen);return row.providerId===cell.dataset.featureProvider&&[row.taskId,...(row.navigationTaskIds||[])].includes(cell.dataset.featureTask)})'''))
            ck('source locators and raw source kinds absent','normalized_text_character_range' not in await page.locator('#results').inner_text() and 'official_public_function_document' not in await page.locator('#results').inner_text())
            button=page.locator('[data-feature-screen]').first
            screen_id=await button.get_attribute('data-feature-screen')
            await button.click()
            ck('actual screen opens existing detail popup contract',await page.evaluate('window.opened')==screen_id)
            await page.get_by_role('button',name='다음 회사',exact=True).click()
            ck('company pagination reaches remaining companies','회사 9–16 / 50곳' in await page.locator('#results').inner_text())
            await page.evaluate("state.provider='woori-bank';state.task='signup';state.page=1;WGSSFeatures.render()")
            ck('Woori signup appears as an exact actionable missing cell',await page.locator('tbody tr').count()==1 and '우리은행' in await page.locator('thead').inner_text())
            await page.get_by_role('button',name='우리은행 회원가입 화면 추가하기',exact=True).click()
            prefill=await page.evaluate('window.prefill')
            ck('suggestion retains company, task, work identifier and readable text',prefill['provider']=='woori-bank' and prefill['task']=='signup' and bool(prefill['workId']) and '우리은행' in prefill['text'] and '회원가입' in prefill['text'])
            await page.evaluate("state.provider='hsbc-uk';state.task='transfer';state.page=1;WGSSFeatures.render()")
            ck('document-only evidence remains honest without unrelated screenshot',await page.locator('[data-feature-screen]').count()==0 and await page.get_by_role('link',name='공식 안내 보기').count()==1 and '수집한 화면 없음' in await page.locator('#results').inner_text())
            await page.evaluate("state.provider='';state.task='signup';state.language='ko';state.page=1;WGSSFeatures.render()")
            ck('language filter never shows an unrelated language screenshot',await page.evaluate("[...document.querySelectorAll('[data-feature-screen]')].every(b=>state.catalog.screens.find(s=>s.id===b.dataset.featureScreen).language==='ko')"))
            await page.locator('[data-feature-add]').first.click()
            ck('language is preserved in suggestion', (await page.evaluate('window.prefill'))['language']=='ko')
            await page.evaluate("state.language='';state.task='';state.provider='';state.page=1;WGSSFeatures.render()")
            await page.wait_for_function("[...document.querySelectorAll('.wgss-feature-image img')].filter(e=>e.getBoundingClientRect().top<innerHeight&&e.getBoundingClientRect().left<innerWidth).every(e=>e.complete&&e.naturalWidth>0)")
            ck('visible thumbnails load real stored screenshot bytes',await page.locator('.wgss-feature-image img').first.evaluate('e=>e.naturalWidth>0'))
            await page.screenshot(path=str(OUT/'company-grid-desktop.png'))
            await page.set_viewport_size({'width':390,'height':844})
            ck('390px mobile has no page overflow',await page.evaluate('document.documentElement.scrollWidth<=390'))
            ck('wide comparison scrolls within table region',await page.locator('.wgss-feature-scroll').evaluate('e=>e.scrollWidth>e.clientWidth'))
            await page.screenshot(path=str(OUT/'company-grid-mobile.png'))
            await page.evaluate("state.catalog.providers.find(p=>p.id==='woori-bank').name='<img src=x onerror=window.xss=1>';state.provider='woori-bank';state.task='signup';WGSSFeatures.render()")
            ck('untrusted company text cannot inject elements',await page.locator('thead img').count()==0 and not await page.evaluate('window.xss||false'))
            await page.evaluate("state.query='no-such-financial-task-9182';state.task='';state.provider='';WGSSFeatures.render()")
            await page.get_by_role('button',name='자료 추가하기',exact=True).click()
            ck('empty query offers prefilled contribution', (await page.evaluate('window.prefill'))['text']=='no-such-financial-task-9182')
            ck('no browser errors',not errors)
            await browser.close()
    finally:
        server.shutdown()
    result={'passed':len(checks),'checks':checks,'errors':errors,'actualCatalog':True,'actualImages':True,'testedAt':'2026-10-16'}
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False,indent=2))

asyncio.run(run())
