/* Read-only operations plan. Publishing a plan does not start a collection job. */
const WGSSOperations = (() => {
  'use strict';
  const scriptUrl = document.currentScript?.src || new URL('operations.js', location.href).href;
  const defaultPlanUrl = new URL('operations-plan.json', scriptUrl).href;
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const list = value => Array.isArray(value) ? value : [];
  const instances = new WeakMap();
  let requestSerial = 0;

  function validate(data) {
    if (!data || data.schema !== 'wgss-operations-plan/v1' || !Array.isArray(data.items) || !Array.isArray(data.categories)) throw new Error('운영 계획 형식을 확인해 주세요.');
    const categories = new Set(data.categories.map(x => x.id));
    const ids = new Set();
    for (const item of data.items) {
      if (!item.id || ids.has(item.id) || !categories.has(item.category) || !Object.hasOwn(data.statusLabels || {}, item.status)) throw new Error('운영 계획 항목을 확인해 주세요.');
      ids.add(item.id);
    }
    return data;
  }

  function taskMarkup(item, plan) {
    const category = plan.categories.find(x => x.id === item.category)?.label || '';
    const milestone = list(plan.milestones).find(x => x.id === item.milestone)?.label || '';
    const feedback = list(item.feedbackIds).map(id => list(plan.feedback).find(x => x.id === id)).filter(Boolean);
    return `<article class="ops-task"><div class="ops-task-meta"><span class="ops-status" data-status="${escape(item.status)}">${escape(plan.statusLabels[item.status])}</span><span>우선순위 ${escape(item.priority)} · ${escape(category)}</span>${milestone ? `<span>${escape(milestone)}</span>` : ''}</div><div><h3>${escape(item.title)}</h3><p class="ops-task-description">${escape(item.summary)}</p><dl>${list(item.candidates).length ? `<dt>조사 후보</dt><dd>${list(item.candidates).map(escape).join(' · ')}</dd>` : ''}${item.scope ? `<dt>수집 범위</dt><dd>${escape(item.scope)}</dd>` : ''}<dt>완료 기준</dt><dd>${escape(item.completion)}</dd>${feedback.length ? `<dt>근거 요청</dt><dd><ul class="ops-feedback-list">${feedback.map(f => `<li>${escape(f.label)}<small>${escape(f.source)}</small></li>`).join('')}</ul></dd>` : ''}</dl></div></article>`;
  }

  function refresh(instance) {
    const {host, plan, category, status} = instance;
    const filtered = plan.items.filter(x => (category === 'all' || x.category === category) && (status === 'all' || x.status === status)).sort((a,b) => a.priority - b.priority);
    host.querySelectorAll('[data-ops-category]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.opsCategory === category)));
    const counts = Object.entries(plan.statusLabels).map(([key,label]) => `${escape(label)} ${plan.items.filter(x => x.status === key).length}건`).join(' · ');
    host.querySelector('[data-ops-summary]').innerHTML = `${filtered.length}개 과제 · ${counts}`;
    host.querySelector('[data-ops-results]').innerHTML = filtered.map(x => taskMarkup(x, plan)).join('') || '<p class="ops-empty">이 조건에 해당하는 과제가 없습니다.</p>';
  }

  function mount(host, plan, mode) {
    const instance = {host, plan, mode, category:'all', status:'all'};
    instances.set(host, instance);
    const serial = ++requestSerial;
    const statusId = `ops-status-${serial}`;
    host.innerHTML = `<section class="wgss-operations" aria-label="WGSS 운영 계획"><div class="ops-heading"><div><h1>${escape(plan.title)}</h1><p>${escape(plan.description)}</p></div><p class="ops-updated">계획 갱신 ${escape(plan.updatedOn)}</p></div><p class="ops-notice">${escape(plan.notice)} ${mode === 'public' ? '자료 검토와 설정 변경은 운영 계정 전용 관리 화면에서 진행합니다.' : '이 목록의 상태는 계획 파일을 갱신해야 바뀝니다. 작업 기록은 AI 작업 메뉴에서 따로 확인하세요.'}</p><ol class="ops-stages" aria-label="진행 순서">${list(plan.milestones).map(stage => `<li><h2>${escape(stage.label)}</h2><p>${escape(stage.description)}</p></li>`).join('')}</ol><h2 class="ops-section-title">수집과 개선 계획</h2><div class="ops-controls"><div class="ops-tabs" role="group" aria-label="계획 분류">${[{id:'all',label:'전체'},...plan.categories].map(category => `<button type="button" class="ops-tab" data-ops-category="${escape(category.id)}" aria-pressed="${category.id === 'all'}">${escape(category.label)}</button>`).join('')}</div><label class="ops-filter" for="${statusId}">상태<select id="${statusId}" data-ops-status><option value="all">모든 상태</option>${Object.entries(plan.statusLabels).map(([key,label])=>`<option value="${escape(key)}">${escape(label)}</option>`).join('')}</select></label></div><p class="ops-summary" data-ops-summary role="status" aria-live="polite"></p><div data-ops-results></div><section class="ops-facts" aria-label="현재 운영 방식"><h2 class="ops-section-title">현재 운영 방식</h2><div class="ops-fact-grid">${list(plan.operatingFacts).map(fact => `<article class="ops-fact"><h3>${escape(fact.label)}</h3><strong>${escape(fact.value)}</strong><p>${escape(fact.detail)}</p></article>`).join('')}</div></section>${mode === 'admin' ? '<section class="ops-admin-guidance"><h2 class="ops-section-title">출처별 품질 관리</h2><p>출처의 권리 확인, 의미 검토와 공개 여부는 자료 관리에서 다룹니다. 검토 전 자료나 내부 판단 메모를 공개 검색에 섞지 않습니다.</p><p>이 계획 목록은 검토 대기함이나 작업 실행 기록을 대신하지 않습니다.</p></section>' : ''}</section>`;
    const root = host.querySelector('.wgss-operations');
    root.addEventListener('click', event => {
      const button = event.target.closest('[data-ops-category]');
      if (!button || !root.contains(button)) return;
      instance.category = button.dataset.opsCategory;
      refresh(instance);
    });
    root.addEventListener('change', event => {
      if (!event.target.matches('[data-ops-status]')) return;
      instance.status = event.target.value;
      refresh(instance);
    });
    refresh(instance);
  }

  async function render({mode = 'public', target = '#admin-panel', planUrl = defaultPlanUrl, data} = {}) {
    const host = typeof target === 'string' ? document.querySelector(target) : target;
    if (!host || !(host instanceof Element)) throw new Error('운영 계획을 표시할 위치를 찾을 수 없습니다.');
    const request = {};
    instances.set(host, request);
    host.innerHTML = '<p class="loading" role="status">운영 계획을 불러오는 중입니다.</p>';
    const pending = host.firstElementChild;
    try {
      let plan = data;
      if (!plan) {
        const response = await fetch(planUrl, {credentials:'same-origin', cache:'no-cache'});
        if (!response.ok) throw new Error('운영 계획을 불러오지 못했습니다.');
        plan = await response.json();
      }
      validate(plan);
      if (instances.get(host) !== request || !host.isConnected || !host.contains(pending)) return;
      mount(host, plan, mode === 'admin' ? 'admin' : 'public');
      return plan;
    } catch (error) {
      if (instances.get(host) !== request || !host.isConnected || !host.contains(pending)) return;
      host.innerHTML = `<div class="wgss-operations"><p class="ops-error" role="alert">${escape(error.message || '운영 계획을 불러오지 못했습니다.')}<button type="button" class="button secondary" data-ops-retry>다시 불러오기</button></p></div>`;
      host.querySelector('[data-ops-retry]').addEventListener('click', () => render({mode,target:host,planUrl,data}));
      throw error;
    }
  }
  return Object.freeze({render});
})();
