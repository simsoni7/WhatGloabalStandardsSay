"""Exercise public search scopes, reference layout and management inventory.

Uses the real commercial public export. All intake writes are intercepted;
only a simulated draft is created to verify edited proposal metadata.
"""
import asyncio, functools, http.server, json, os, threading
from pathlib import Path
from urllib.parse import urlsplit
from playwright.async_api import async_playwright

ROOT = Path(os.environ.get('WGSS_UI_EXPORT', '/home/ubuntu/wgss-ui-fixes-20261023/export'))
OUT = Path(os.environ.get('WGSS_UI_QA', '/home/ubuntu/wgss-ui-fixes-20261023/qa'))
BASE = '/WhatGloabalStandardsSay/wgss/'
OUT.mkdir(parents=True, exist_ok=True)

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
    def translate_path(self, path):
        name = urlsplit(path).path.removeprefix(BASE).lstrip('/') or 'index.html'
        return str(ROOT / name)

async def main():
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}' + BASE
    checks, errors, writes = [], [], []
    def check(name, passed):
        assert passed, name
        checks.append(name)
        print(name, flush=True)
    async def api(route):
        from urllib.parse import parse_qs
        req = route.request
        resource = parse_qs(urlsplit(req.url).query).get('resource', [''])[0]
        if req.method == 'POST':
            data = req.post_data_json
            assert data['action'] == 'createSubmission', data['action']
            writes.append(data)
            await route.fulfill(json={'item': {'id': 'ui-only-draft', 'status': 'pending', 'files': []}})
        elif resource == 'session':
            await route.fulfill(json={'role': 'admin', 'publicReview': True})
        elif resource == 'submissions':
            await route.fulfill(json={'items': [{'id': 'screen-text-correction', 'kind': 'translation_issue', 'status': 'held', 'title': '화면 문구 수정', 'version': 1, 'createdAt': '2026-10-23', 'current': {'proposalType': 'screen', 'text': '문구 수정', 'referenceId': 'v44:citi-us-existing-registration:citi-10'}, 'files': []}]})
        else:
            await route.fulfill(json={'items': []})
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page(viewport={'width': 1440, 'height': 1000})
            page.on('pageerror', lambda e: errors.append(str(e)))
            await page.route('**/api/wgss*', api)
            async def go(tail):
                await page.goto(url + tail, wait_until='domcontentloaded')
                await page.wait_for_function('typeof state!=="undefined" && state.catalog && document.querySelector("#app h1")')
            async def shot(name):
                await page.screenshot(path=str(OUT / (name + '.png')), full_page=True)

            await go('?tab=features&query=%EC%B9%B4%EB%93%9C+%EC%8B%A0%EC%B2%AD&task=signup#screens')
            check('old card-search link clears incompatible signup filter', await page.locator('#task').input_value() == '' and '검색된 업무가 없습니다' not in await page.locator('#results').inner_text())
            await go('?query=%EC%B9%B4%EB%93%9C+%EC%8B%A0%EC%B2%AD#screens')
            await page.locator('[data-task="signup"]').click()
            check('quick search replaces the previous query', await page.locator('#query').input_value() == '' and await page.locator('.screen-card').count() > 0)

            await go('?tab=words&wordMode=terms&task=signup&provider=citi#screens')
            await page.wait_for_function('!state.loadingTerms', timeout=120000)
            check('dictionary hides inapplicable company and task fields', not await page.locator('#provider').is_visible() and not await page.locator('#task').is_visible() and not await page.locator('.quick-search').is_visible())
            check('dictionary explains its search scope without misleading chips', await page.locator('[data-remove-filter="provider"]').count() == 0 and '검색어와 언어' in await page.locator('.filter-scope').inner_text())
            await page.locator('#query').fill('account')
            await page.wait_for_timeout(300)
            await page.locator('#language').select_option('ar')
            await page.wait_for_function('!state.loadingTerms')
            check('dictionary actually filters by query and language', await page.evaluate('WGSSDictionary.visibleRows().length>0 && WGSSDictionary.visibleRows().every(r=>r.language==="ar"&&[r.english,r.korean,r.target,r.definition,r.source,r.sourceConceptId].some(x=>normalizeQuery(x).includes("account")))'))
            await page.locator('[name="word-mode"][value="all"]').check()
            check('mixed results show scope-specific company and task labels', await page.locator('label[for="provider"]').inner_text() == '회사·서비스 · 화면 문구' and await page.locator('#provider').is_visible())
            await shot('dictionary-search-scopes')

            await go('?tab=words&wordMode=phrases#screens')
            await page.locator('[data-phrase-detail]').first.click()
            detail = await page.locator('#dialog-content').inner_text()
            check('public phrase detail contains no admin export or raw unknown values', await page.locator('#detail-dialog [data-row-export]').count() == 0 and 'unknown' not in detail and '별도 화면 ID' not in detail)
            await shot('public-phrase-detail')

            await go('?reference=v44%3Aciti-us-existing-registration%3Aciti-10#screens')
            await page.locator('#detail-dialog[open]').wait_for()
            check('related screens precede the full phrase list', await page.evaluate('!!(document.querySelector("#flow-section").compareDocumentPosition(document.querySelector(".screen-phrases")) & Node.DOCUMENT_POSITION_FOLLOWING)'))
            check('all 39 source phrases remain available with six initially visible', await page.locator('.screen-phrases .phrase-list li').count() == 39 and await page.locator('.screen-phrases .phrase-list li:visible').count() == 6)
            await page.locator('.more-phrases summary').click()
            check('expanding phrases reveals every original phrase', await page.locator('.screen-phrases .phrase-list li:visible').count() == 39)
            await page.locator('.more-phrases summary').click()
            check('public screen metadata uses readable labels', 'existing-customer-registration' not in await page.locator('#dialog-content').inner_text())
            await page.set_viewport_size({'width': 390, 'height': 844})
            check('mobile detail has no horizontal overflow', await page.evaluate('document.documentElement.scrollWidth<=innerWidth && document.querySelector("#detail-dialog").scrollWidth<=document.querySelector("#detail-dialog").clientWidth+1'))
            check('mobile flow is reachable before long OCR text', await page.evaluate('document.querySelector("#flow-section").getBoundingClientRect().top-document.querySelector("#detail-dialog").getBoundingClientRect().top<2000'))
            await shot('mobile-screen-detail')

            await go('?tab=features&task=signup#screens')
            check('company tab and heading consistently describe screens', await page.locator('[data-tab="features"]').inner_text() == '회사별 화면' and await page.locator('#feature-heading').inner_text() == '회사별 화면')
            check('collection totals and target totals are separately labeled', '화면 확보' in await page.locator('.wgss-features .context-note').inner_text() and '전체 조사 대상 56곳' in await page.locator('.wgss-features .context-note').inner_text())
            check('mobile company comparison presents two complete columns', await page.locator('.wgss-feature-mobile-company:visible').count() == 2 and await page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            await shot('mobile-company-comparison')
            await page.locator('[data-feature-scope="all"]').click()
            check('uncollected targets remain available for suggestions', '56개 회사 표시' in await page.locator('.wgss-features .result-head').inner_text())
            await page.locator('[data-feature-scope="collected"]').click()
            add = page.locator('[data-feature-add]:visible').first
            origin = await add.get_attribute('aria-label')
            await add.click()
            await page.locator('#contribution-provider').wait_for()
            check('proposal visibly prefills company and task', await page.locator('#contribution-provider').input_value() in origin and await page.locator('#contribution-task').input_value() == 'signup')
            await page.locator('#contribution-provider').fill('우리은행')
            await page.locator('#contribution-task').select_option('login')
            await page.locator('#contribution-language').select_option('ko')
            await page.locator('#contribution-text').fill('로그인 화면을 제안합니다.')
            await page.locator('[name="safeTextConfirmed"]').check()
            await shot('editable-proposal-context')
            await page.locator('#submit-contribution').click()
            await page.wait_for_function('document.querySelector("#contribution-status").textContent.includes("접수되었습니다")')
            check('edited company, task and language reach the submitted payload', len(writes) == 1 and writes[0]['provider'] == '우리은행' and writes[0]['task'] == 'login' and writes[0]['language'] == 'ko')

            await go('?tab=words&wordMode=terms&language=ar&provider=citi&task=signup#admin')
            await page.locator('[data-admin-tab="inventory"]').click()
            await page.locator('[data-inventory-type="terms"]').click()
            await page.wait_for_function('!state.loadingTerms && state.terms.length>=21188', timeout=120000)
            check('term inventory loads all languages independently of reader filters', await page.evaluate('inventoryRows().length===21188'))
            await page.locator('#inventory-query').fill('Account')
            await page.wait_for_timeout(300)
            await page.locator('#inventory-language').select_option('ar')
            check('inventory search and language filters select real term rows', await page.evaluate('inventoryRows().length>0&&inventoryRows().every(r=>r.language==="ar"&&[r.english,r.korean,r.target,r.source].some(x=>normalizeQuery(x).includes("account")))'))
            await page.locator('[data-inventory-term]').first.click()
            check('manager can open and propose edits to a term', await page.locator('#dialog-title').inner_text() == '용어 자료' and await page.locator('#detail-dialog [data-term-propose]').count() == 1)
            await page.locator('[data-close]').click()
            await shot('mobile-term-inventory')
            await page.locator('[data-admin-tab="inbox"]').click()
            await page.locator('[data-review="screen-text-correction"]').wait_for()
            check('screen OCR correction remains a screen proposal', '화면 · 접수' in await page.locator('.list-row .meta').first.inner_text())
            await page.set_viewport_size({'width':1440,'height':1000})
            await page.locator('[data-admin-tab="inventory"]').click()
            await page.locator('[data-inventory-term]').first.wait_for()
            await shot('desktop-term-inventory')
            await go('#about')
            check('dictionary dataset total uses kinds rather than institutions', '11종' in (await page.locator('.about-metrics').inner_text()).replace('\n','') and '용어집 출처' not in await page.locator('.about-metrics').inner_text())
            check('no uncaught browser errors', not errors)
            await browser.close()
    finally:
        server.shutdown();server.server_close()
        report={'passed':len(checks),'checks':checks,'errors':errors,'simulatedSubmissions':len(writes)}
        (OUT/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))

if __name__ == '__main__':asyncio.run(main())
