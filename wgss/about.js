/* Introduction reads the same admitted catalogue as the reference browser. */
'use strict';
const WGSSAbout=(()=>{
 const list=value=>Array.isArray(value)?value:[];
 const number=value=>Number(value||0).toLocaleString('ko-KR');
 const safe=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const languageName=(catalog,id)=>list(catalog.languages).find(x=>x.id===id)?.label||id;
 function metrics(catalog){
  const dictionary=catalog.dictionary||{};
  const datasets=list(dictionary.datasets).filter(x=>x.commercial===true&&x.layer==='core');
  const allowed=new Set(datasets.map(x=>x.id));
  const chunks=list(dictionary.chunks).filter(x=>x.layer==='core'&&list(x.datasetIds).length&&x.datasetIds.every(id=>allowed.has(id)));
  const languageCounts=new Map();
  for(const chunk of chunks)for(const [id,count]of Object.entries(chunk.languageCounts||{}))languageCounts.set(id,(languageCounts.get(id)||0)+Number(count||0));
  const dictionaryRows=datasets.reduce((sum,x)=>sum+Number(x.count||0),0);
  const countedRows=[...languageCounts.values()].reduce((sum,x)=>sum+x,0);
  // Mixed-source chunks must be projected before their language totals can be advertised.
  const languageTotalsComplete=countedRows===dictionaryRows&&dictionaryRows>0;
  const screens=list(catalog.screens),phrases=list(catalog.phrases);
  return {datasets,dictionaryRows,languageCounts,languageTotalsComplete,screens,phrases,
   screenProviders:new Set(screens.map(x=>x.providerId).filter(Boolean)).size,
   screenLanguages:new Set(screens.map(x=>x.language).filter(x=>x&&x!=='unknown')).size,
   uniqueImages:new Set(screens.map(x=>x.originalSha||x.imagePath).filter(Boolean)).size,
   languageCount:languageTotalsComplete?languageCounts.size:null};
 }
 function referenceHref(tab,extra={}){
  const params=new URLSearchParams({tab,...extra});
  return '?'+params.toString()+'#screens';
 }
 function imageStrip(catalog,m){
  const providers=[['toss','toss-v6:TOSS-004'],['paypal','v44:paypal-us-login:paypal-login-01'],['citi','v44:citi-us-existing-registration:citi-11']];
  const chosen=[];
  for(const [name,preferred] of providers){const row=m.screens.find(x=>x.id===preferred&&x.imagePath)||m.screens.find(x=>x.imagePath&&String(x.providerId).toLowerCase().includes(name));if(row&&!chosen.some(x=>x.id===row.id))chosen.push(row);}
  for(const row of m.screens)if(chosen.length<3&&row.imagePath&&!chosen.some(x=>x.providerId===row.providerId))chosen.push(row);
  if(!chosen.length)return '';
  return `<div class="about-screen-strip" aria-label="WGSS에서 볼 수 있는 실제 금융사 화면">${chosen.map(row=>`<figure><a href="${safe(referenceHref('screens',{reference:row.id}))}" aria-label="${safe(row.provider||row.providerId)} ${safe(row.stageLabel||'화면')} 보기"><div class="about-screen-image"><img src="${safe(row.imagePath)}" alt="${safe(row.provider||row.providerId)}에서 수집한 ${safe(row.stageLabel||'금융 서비스 화면')}" loading="eager" decoding="async"></div></a><figcaption>${safe(row.provider||row.providerId)}<span>${safe(row.stageLabel||row.title||'수집 화면')}</span></figcaption></figure>`).join('')}</div>`;
 }
 function languageGraph(catalog,m){
  if(!m.languageTotalsComplete)return '<p class="about-small">언어별 자료 수는 공개 용어집 집계가 끝나면 표시합니다.</p>';
  const ranked=[...m.languageCounts].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));
  const visible=ranked.slice(0,8),max=visible[0]?.[1]||1;
  const table=ranked.map(([id,count])=>`<tr><th scope="row">${safe(languageName(catalog,id))}</th><td>${number(count)}쌍</td></tr>`).join('');
  return `<figure class="about-language-chart"><figcaption>언어별 용어 수 <span>자료가 많은 8개 언어 · 영어 원문과 대상 언어의 대응 쌍</span></figcaption><ol class="about-bars" aria-label="언어별 용어 대응 쌍 수">${visible.map(([id,count])=>`<li><span class="about-bar-label">${safe(languageName(catalog,id))}</span><span class="about-bar-track" aria-hidden="true"><span style="width:${(count/max*100).toFixed(2)}%"></span></span><span class="about-bar-value">${number(count)}<span class="about-sr-only">쌍</span></span></li>`).join('')}</ol></figure><details class="about-language-details"><summary>${number(m.languageCount)}개 언어 전체 보기</summary><div class="about-language-table table-scroll"><table><caption class="about-sr-only">상업적 이용이 허용된 용어집의 언어별 대응 쌍 수</caption><thead><tr><th scope="col">언어·표기</th><th scope="col">용어 대응 쌍</th></tr></thead><tbody>${table}</tbody></table></div></details>`;
 }
 function render(){
  const catalog=state.catalog;if(!catalog)return;
  const m=metrics(catalog),languages=m.languageCount;
  const languageText=languages?`${number(languages)}개 언어의 용어를<br>한곳에서 찾아보세요.`:'다국어 금융 용어를<br>한곳에서 찾아보세요.';
  document.querySelector('#app').innerHTML=`<div class="about-page">
   <section class="about-hero" aria-labelledby="about-title">
    <h1 id="about-title">다른 금융사는<br>어떻게 만들었을까요?</h1>
    <p class="about-hero-copy">회원가입부터 카드 신청까지.<br>실제 금융사의 화면과 표현, 다국어 용어를 한곳에서 찾아보세요.</p>
    <div class="about-hero-actions"><a class="button primary" href="${safe(referenceHref('screens'))}">레퍼런스 찾기</a><a class="about-inline-link" href="#about-how">처음 이용하시나요?</a></div>
    ${imageStrip(catalog,m)}
    <p class="about-image-note">WGSS에 수집된 실제 화면입니다. 수집 시점의 화면을 참고할 수 있습니다.</p>
   </section>
   <section class="about-section about-scale" aria-labelledby="about-scale-title">
    <div class="about-section-heading"><h2 id="about-scale-title">화면, 문구, 다국어 용어.<br>현재 모은 자료입니다.</h2><p>금융사의 화면을 보고, 실제 문구와 다른 언어의 표현을 찾을 수 있습니다.</p></div>
    <dl class="about-metrics"><div><dt>금융사 화면</dt><dd>${number(m.screens.length)}<span>건</span></dd><dd class="about-metric-note">${number(m.screenProviders)}개 금융사 · ${number(m.uniqueImages)}개 이미지</dd></div><div><dt>화면 문구</dt><dd>${number(m.phrases.length)}<span>건</span></dd><dd class="about-metric-note">화면과 안내 자료에서 수집한 문구</dd></div><div><dt>다국어 용어</dt><dd>${number(m.dictionaryRows)}<span>쌍</span></dd><dd class="about-metric-note">영어 원문과 다른 언어의 대응 표현</dd></div><div><dt>용어집 출처</dt><dd>${number(m.datasets.length)}<span>곳</span></dd><dd class="about-metric-note">상업적 이용을 허용한 자료</dd></div></dl>
    <p class="about-small">화면 수는 등록된 화면 사례 수입니다. 용어 수는 언어별 대응 쌍 수이며, 같은 뜻의 표현이 여러 자료에 포함될 수 있습니다.</p>
   </section>
   <section class="about-section about-language" aria-labelledby="about-language-title">
    <div class="about-section-heading"><h2 id="about-language-title">${languageText}</h2><p>영어 원문과 다른 언어의 표현을 함께 확인하세요. 공공기관과 공개 소프트웨어의 자료를 모아 출처별로 살펴볼 수 있습니다.</p><a class="about-inline-link" href="${safe(referenceHref('words',{wordMode:'terms'}))}">다국어 용어 찾기</a><p class="about-small">언어·표기 코드를 기준으로 집계합니다. 실제 금융사 화면의 제공 언어 수와는 다릅니다.</p></div>
    <div>${languageGraph(catalog,m)}</div>
   </section>
   <section class="about-section" id="about-how" aria-labelledby="about-how-title">
    <div class="about-section-heading"><h2 id="about-how-title">만들 화면이 있다면,<br>이렇게 시작해 보세요.</h2><p>복잡한 분류를 먼저 배울 필요 없이, 익숙한 업무 이름으로 검색하면 됩니다.</p></div>
    <ol class="about-steps"><li><span class="about-step-number" aria-hidden="true">1</span><div><h3>만들려는 업무를 검색하세요.</h3><p>‘회원가입’, ‘로그인’, ‘카드 신청’처럼 입력하세요. 회사와 언어로 좁히면 필요한 사례를 찾기 쉽습니다.</p><div class="about-examples"><a href="${safe(referenceHref('screens',{query:'회원가입'}))}">회원가입</a><a href="${safe(referenceHref('screens',{query:'로그인'}))}">로그인</a><a href="${safe(referenceHref('screens',{query:'카드 신청'}))}">카드 신청</a></div></div></li><li><span class="about-step-number" aria-hidden="true">2</span><div><h3>실제 화면과 표현을 살펴보세요.</h3><p>이미지를 열어 배치와 버튼 문구를 확인하세요. 함께 수집한 화면, 수집일과 출처가 있는 자료는 상세 화면에서 이어 볼 수 있습니다.</p></div></li><li><span class="about-step-number" aria-hidden="true">3</span><div><h3>다른 언어로는 어떻게 쓰는지 확인하세요.</h3><p>‘표현과 용어’에서 금융사의 실제 문구와 다국어 용어를 찾아보세요. 출처가 다른 표현을 함께 보고 내 화면에 맞는 말을 고를 수 있습니다.</p><a class="about-inline-link" href="${safe(referenceHref('words',{wordMode:'all'}))}">표현과 용어 둘러보기</a></div></li></ol>
   </section>
   <section class="about-section about-grow" aria-labelledby="about-grow-title">
    <div class="about-section-heading"><h2 id="about-grow-title">자료를 제안하고,<br>함께 업데이트합니다.</h2><p>새 화면이나 표현을 모으고, 잘못된 내용을 고치며, 더 오래 쓸 수 있는 자료로 쌓아 갑니다.</p></div>
    <div class="about-growth-list"><div><h3>화면과 표현을 함께 모읍니다.</h3><p>간단한 설명, 출처 링크와 캡처 이미지를 제안해 주세요. 운영자가 자료를 확인한 뒤 화면과 용어에 반영합니다.</p></div><div><h3>운영자가 검토한 뒤 반영합니다.</h3><p>승인한 수정은 해당 자료에 반영하고, 교체된 화면은 이전 버전으로 남깁니다. 공개 사이트를 다시 조회하면 승인한 최신 자료를 볼 수 있습니다.</p></div><div><h3>앞으로 사용자 의견으로 수집 순서를 정합니다.</h3><p>앞으로 사용자 의견과 부족한 사례를 모아 다음에 수집할 화면과 개선할 기능의 순서를 정합니다.</p></div></div>
   </section>
   <section class="about-closing" aria-labelledby="about-closing-title"><h2 id="about-closing-title">이제 만들려는 화면을 찾아보세요.</h2><p>What Global Standards Say · 글로벌 금융서비스의 화면과 언어를 우리 팀의 참고 자원으로.</p><a class="button primary" href="${safe(referenceHref('screens'))}">레퍼런스 찾기</a></section>
  </div>`;
 }
 return {render,metrics};
})();
