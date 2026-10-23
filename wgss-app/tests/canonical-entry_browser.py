"""Exercise the static-first hosting entry, without calling the real service."""
import asyncio,functools,http.server,pathlib,threading
from playwright.async_api import async_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1]
OFFICIAL='https://3.36.58.188/WhatGloabalStandardsSay/wgss/'
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
async def main():
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'public')))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        for enabled in [True,False]:
            context=await browser.new_context(java_script_enabled=enabled,ignore_https_errors=True)
            page=await context.new_page();calls=[];page.on('request',lambda request:calls.append(request.url))
            await page.route(OFFICIAL+'**',lambda route:route.fulfill(content_type='text/html',body='<h1>Official WGSS</h1>'))
            await page.goto(f'http://127.0.0.1:{server.server_port}/workspace/?tab=screens&reference=one%3Atwo#admin')
            await page.wait_for_url(OFFICIAL+'**')
            if enabled:assert page.url==OFFICIAL+'?tab=screens&reference=one%3Atwo#admin',page.url
            assert not any('/integration-data/' in url or '/api/wgss' in url for url in calls)
            await context.close()
        await browser.close()
    server.shutdown()
    print('Static-first entry passes with JavaScript and without it; old catalogue is never loaded')
asyncio.run(main())
