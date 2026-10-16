"""Read-only screen UI regression against the built public bundle; API is mocked."""
import asyncio,functools,http.server,json,pathlib,sys,threading,urllib.parse
from playwright.async_api import async_playwright
ROOT=pathlib.Path(sys.argv[1]);BASE='/WhatGloabalStandardsSay/wgss/'
TARGET='v44:citi-us-existing-registration:citi-10'
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def translate_path(self,path):
        return str(ROOT/urllib.parse.urlparse(path).path.removeprefix(BASE))
async def main():
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    errors=[];checks=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        page=await browser.new_page()
        page.on('pageerror',lambda error:errors.append(str(error)))
        async def api(route):
            assert route.request.method=='GET','Test must not mutate runtime data'
            resource=urllib.parse.parse_qs(urllib.parse.urlparse(route.request.url).query).get('resource',[''])[0]
            value={'role':'admin','publicReview':True} if resource=='session' else {'items':[]}
            await route.fulfill(json=value,headers={'Access-Control-Allow-Origin':'*'})
        await page.route('**/api/wgss?**',api)
        url=f'http://127.0.0.1:{server.server_port}{BASE}'
        await page.goto(url+'?reference='+urllib.parse.quote(TARGET)+'#screens')
        await page.locator('#detail-dialog[open]').wait_for()
        dialog=page.locator('#detail-dialog')
        assert await dialog.locator('.screen-management-actions').count()==0
        for attribute in ['data-propose','data-evidence-export','data-copy-reference','data-screen-update']:
            assert await dialog.locator('['+attribute+']').count()==0
        assert await dialog.locator('q').filter(has_text='User ID').count()>0
        assert await dialog.locator('q').filter(has_text='Sign On').count()>0
        assert await dialog.locator('[data-add-collection-screen]').count()==1
        checks.append('public detail: expanded literal phrases, no management tools, add screen retained')
        await dialog.locator('[data-close]').first.click()
        assert await page.get_by_text('빠른 검색',exact=True).is_visible()
        await page.locator('.quick-search [data-task]').first.click()
        assert urllib.parse.parse_qs(urllib.parse.urlparse(page.url).query).get('task')
        checks.append('quick search: visible label and working task button')
        for width in [390,1280]:
            await page.set_viewport_size({'width':width,'height':900})
            assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        checks.append('mobile and desktop: no horizontal page overflow')
        await page.goto(url+'#admin')
        await page.locator('[data-admin-tab="inventory"]').click()
        await page.locator('#admin-panel [data-screen]').first.click()
        await dialog.locator('.screen-management-actions').wait_for()
        assert await dialog.locator('.screen-management-actions button').count()==5
        checks.append('management inventory: five tools remain available')
        assert not errors,errors
        await browser.close()
    server.shutdown()
    print(json.dumps({'passed':checks,'pageErrors':errors},ensure_ascii=False,indent=2))
asyncio.run(main())
