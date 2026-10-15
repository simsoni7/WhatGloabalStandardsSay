'use strict';
/* Company × task navigation. An empty cell says nothing about service availability. */
const WGSSFeatures=(()=>{
  let companyPage=1,lastContext='';
  const expanded=new Set();
  const list=value=>Array.isArray(value)?value:[];
  const norm=value=>String(value??'').toLocaleLowerCase().replace(/\s+/g,'');
  const ids=row=>[row.taskId,...list(row.taskIds),...list(row.navigationTaskIds)].filter(Boolean);
  const hasTask=(row,task)=>ids(row).includes(task.id)||(row.workId&&list(task.workIds).includes(row.workId));
  const allowedImage=row=>{if(!row.imagePath)return false;try{const url=new URL(row.imagePath,location.href);return ['https:','http:'].includes(url.protocol)}catch{return false}};
  const external=url=>{try{const u=new URL(url);return ['https:','http:'].includes(u.protocol)?u.href:''}catch{return ''}};
  const taskMatches=(task,features,screens)=>{
    const query=norm(state.query);if(!query)return true;
    if([task.label,...list(task.aliases)].some(value=>norm(value).includes(query)))return true;
    if(list(state.catalog.canonicalWorks).some(work=>list(task.workIds).includes(work.id)&&[work.label,work.definition,...list(work.aliases)].some(value=>norm(value).includes(query))))return true;
    return features.some(row=>hasTask(row,task)&&[row.expression,row.label,row.meaning].some(value=>norm(value).includes(query)))||screens.some(row=>hasTask(row,task)&&[row.title,row.stageLabel,...list(row.wording)].some(value=>norm(value).includes(query)));
  };
  const proposal=(task,provider,language)=>({kind:'screen',proposalType:'screen',provider:provider.id,task:task.id,workId:list(task.workIds).length===1?task.workIds[0]:'',language:language||'',title:`${provider.name} · ${task.label} 화면 제안`,text:`${provider.name}의 ${task.label} 화면을 추가합니다.`});
  function cell(task,provider,screens,features){
    const key=task.id+'\u001f'+provider.id;
    const matches=screens.filter(row=>row.providerId===provider.id&&hasTask(row,task)&&allowedImage(row));
    const documents=features.filter(row=>row.providerId===provider.id&&hasTask(row,task));
    const urls=[...new Set(documents.flatMap(row=>list(row.evidence).map(item=>external(item.url))).filter(Boolean))];
    return `<td class="wgss-feature-cell" data-feature-task="${esc(task.id)}" data-feature-provider="${esc(provider.id)}">${matches.length?`<div class="wgss-feature-previews">${matches.slice(0,expanded.has(key)?matches.length:2).map(row=>`<button type="button" class="wgss-feature-preview" data-feature-screen="${esc(row.id)}" aria-label="${esc(provider.name+' · '+task.label+' · '+(row.stageLabel||row.title||'화면')+' 화면과 흐름 보기')}"><span class="wgss-feature-image"><img src="${esc(row.imagePath)}" alt="${esc(provider.name+' '+(row.stageLabel||row.title||task.label))}" loading="lazy" decoding="async"></span><span>${esc(row.stageLabel||row.title||task.label)}</span></button>`).join('')}</div><p class="wgss-feature-caption">수집한 화면 ${matches.length}장</p>${matches.length>2&&!expanded.has(key)?`<button type="button" class="text-button" data-feature-more="${esc(task.id)}" data-feature-provider="${esc(provider.id)}">화면 ${matches.length-2}장 더 보기</button>`:''}`:`<p class="wgss-feature-missing">수집한 화면 없음</p>${urls.length?`<a class="wgss-feature-document" href="${esc(urls[0])}" target="_blank" rel="noopener noreferrer">공식 안내 보기</a>`:''}`}<button type="button" class="wgss-feature-add" data-feature-add="${esc(task.id)}" data-feature-provider="${esc(provider.id)}" aria-label="${esc(provider.name+' '+task.label+' 화면 추가하기')}">화면 추가하기</button></td>`;
  }
  function render(){
    const target=document.querySelector('#results');if(!target||!state.catalog)return;
    const catalog=state.catalog,context=[state.provider,state.language,state.query,state.task].join('\u001f');
    if(context!==lastContext){companyPage=1;lastContext=context;}
    const screens=list(catalog.screens).filter(row=>!state.language||row.language===state.language);
    const features=list(catalog.features).filter(row=>(!state.language||row.language===state.language)&&(!state.provider||row.providerId===state.provider));
    const tasks=list(catalog.tasks).filter(task=>task.groupId!=='toss-v6-editorial'&&(!state.task||task.id===state.task)&&taskMatches(task,features,screens.filter(row=>!state.provider||row.providerId===state.provider)));
    const providers=list(catalog.providers).filter(provider=>!state.provider||provider.id===state.provider).sort((a,b)=>{
      const score=provider=>screens.filter(row=>row.providerId===provider.id&&allowedImage(row)).length;
      return score(b)-score(a)||String(a.name).localeCompare(String(b.name),'ko');
    });
    const pages=Math.max(1,Math.ceil(providers.length/8));companyPage=Math.min(companyPage,pages);
    const shown=providers.slice((companyPage-1)*8,companyPage*8),pager=pagination(tasks.length),start=(state.page-1)*18;
    const rowSet=tasks.slice(start,start+18);
    target.innerHTML=`<section class="wgss-features" aria-labelledby="feature-heading"><div class="result-head"><h2 id="feature-heading">회사별 금융 화면</h2><p>${tasks.length}개 업무 · ${providers.length}개 회사</p></div><p class="context-note">같은 업무의 화면을 회사별로 살펴보세요. 위의 업무·회사 필터로 원하는 항목을 좁힐 수 있어요. 빈칸은 ‘화면 추가하기’로 채워 주세요.</p>${providers.length>8?`<div class="wgss-feature-company-pages" aria-label="표에 표시할 회사"><button type="button" class="button secondary" data-feature-company-page="${companyPage-1}" ${companyPage===1?'disabled':''}>이전 회사</button><span aria-live="polite">회사 ${(companyPage-1)*8+1}–${Math.min(companyPage*8,providers.length)} / ${providers.length}곳</span><button type="button" class="button secondary" data-feature-company-page="${companyPage+1}" ${companyPage===pages?'disabled':''}>다음 회사</button></div>`:''}${tasks.length&&shown.length?`<div class="wgss-feature-scroll" tabindex="0" role="region" aria-label="업무별 금융사 화면 표, 좌우로 스크롤할 수 있습니다"><table class="wgss-feature-table"><thead><tr><th scope="col">금융업무</th>${shown.map(provider=>`<th scope="col">${esc(provider.name)}</th>`).join('')}</tr></thead><tbody>${rowSet.map(task=>`<tr><th scope="row">${esc(task.label)}</th>${shown.map(provider=>cell(task,provider,screens,features)).join('')}</tr>`).join('')}</tbody></table></div>${pager}`:`<div class="empty"><h3>검색된 업무가 없습니다.</h3><p>검색어를 바꾸거나 원하는 화면을 제안해 주세요.</p><button type="button" class="button secondary" data-feature-empty-add>자료 추가하기</button></div>`}<p class="wgss-feature-footnote">화면이 비어 있어도 해당 회사가 기능을 제공하지 않는다는 뜻은 아닙니다.</p></section>`;
    target.querySelectorAll('[data-feature-screen]').forEach(button=>button.addEventListener('click',()=>openScreen(button.dataset.featureScreen)));
    target.querySelectorAll('[data-feature-add]').forEach(button=>button.addEventListener('click',()=>{
      const task=tasks.find(row=>row.id===button.dataset.featureAdd),provider=providers.find(row=>row.id===button.dataset.featureProvider);
      if(task&&provider)beginContribution(proposal(task,provider,state.language));
    }));
    target.querySelectorAll('[data-feature-more]').forEach(button=>button.addEventListener('click',()=>{
      expanded.add(button.dataset.featureMore+'\u001f'+button.dataset.featureProvider);
      render();
    }));
    target.querySelectorAll('[data-feature-company-page]').forEach(button=>button.addEventListener('click',()=>{companyPage=Number(button.dataset.featureCompanyPage);render();}));
    target.querySelector('[data-feature-empty-add]')?.addEventListener('click',()=>beginContribution({kind:'screen',proposalType:'screen',provider:state.provider||'',task:state.task||'',language:state.language||'',text:state.query||'',title:state.query?`${state.query} 화면 제안`:''}));
  }
  return {render};
})();
