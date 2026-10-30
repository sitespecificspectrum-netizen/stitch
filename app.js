// 실 기록 — 픽셀 이미지 도안, 보유 실 기반 추천, 장보기, 진행 기록. 모든 데이터는 기기(localStorage)에 저장한다.
const KEY = 'stitch.projects.v1';
const STASH_KEY = 'stitch.stash.v1';
const byCode = Object.fromEntries(DMC.map(([code, name, hex]) => [code, { code, name, hex }]));
const $ = (id) => document.getElementById(id);
const EMPTY = 255;                 // 도안에서 수놓지 않는 칸
const MAX_SIDE = 300;              // 도안 한 변 최대 칸 수
const OWNED_OK = 10;               // 보유 실 우선일 때 이 정도 색 차이(ΔE)까지는 보유 실을 쓴다
const SYMBOLS = '●▲■◆○△□◇ABCDEFGHJKLMNPQRSTUVWXYZ23456789abdefghkmnpqrtuy+=×÷%#@&?!$/<>~^*'.split('');
// 25번사 2가닥 기준 한 타래로 놓을 수 있는 대략적인 칸 수
const STITCHES_PER_SKEIN = { 11: 1300, 14: 1800, 16: 2100, 18: 2400 };

let projects = load(KEY, []);
let stash = load(STASH_KEY, {});   // { 실 번호: 타래 수 }
let currentTab = 'list-view';
let current = null;                // 열려 있는 작품
let draft = [];                    // 편집 중인 실 번호 목록 (도안 없는 작품)
let pv = { mode: 'view', zoom: 0, highlight: null };

// ───────── 저장 ─────────
function load(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}
// _로 시작하는 필드는 화면용 캐시라 저장하지 않는다
const skipCache = (k, v) => (k.startsWith('_') ? undefined : v);
function persist() {
  try {
    localStorage.setItem(KEY, JSON.stringify(projects, skipCache));
    localStorage.setItem(STASH_KEY, JSON.stringify(stash));
  } catch {
    toast('저장 공간이 부족해요. 백업 파일을 저장하고 오래된 작품을 정리해 주세요.');
  }
}

// ───────── 공통 ─────────
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}
function toast(msg) {
  const t = $('toast');
  t.textContent = msg; t.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (t.hidden = true), 2400);
}
const owned = (code) => (stash[code] || 0) > 0;
const threadHex = (code) => byCode[code]?.hex || '999999';
const fmt = (n) => n.toLocaleString('ko-KR');
const today = () => new Date().toLocaleDateString('sv-SE'); // YYYY-MM-DD (현지 날짜)
const fmtDate = (d) => (d ? new Date(d).toLocaleDateString('ko-KR') : '');

function b64(u8) {
  let s = '';
  for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
  return btoa(s);
}
function unb64(s) {
  const bin = atob(s);
  const u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  return u8;
}
function swatch(hex, cls = 'swatch') {
  const s = el('span', cls);
  s.style.background = '#' + hex;
  return s;
}

const VIEWS = ['list-view', 'stash-view', 'shop-view', 'project-view', 'new-view', 'edit-view', 'picker-view'];
const TABS = ['list-view', 'stash-view', 'shop-view'];
function show(view) {
  for (const v of VIEWS) $(v).hidden = v !== view;
  $('tabs').hidden = !TABS.includes(view);
  document.body.classList.toggle('with-tabs', TABS.includes(view));
  window.scrollTo(0, 0);
}
function switchTab(tab) {
  currentTab = tab;
  for (const b of $('tabs').children) b.classList.toggle('on', b.dataset.tab === tab);
  render();
  show(tab);
}
function render() {
  renderList();
  renderStash();
  renderShop();
}

// ───────── 작품 데이터 ─────────
// 도안이 있는 작품: pattern { w, h, palette: [hex], cells: base64 }, threads: [palette 순서의 실 번호], done: base64 비트셋
// 도안이 없는 작품: codes: [실 번호], status

/** 도안 캐시(칸 배열, 완료 비트셋, 색별 칸 수)를 만든다 */
function hydrate(p) {
  if (!p.pattern || p._cells) return p;
  const { w, h, palette } = p.pattern;
  p._cells = unb64(p.pattern.cells);
  p._done = p.done ? unb64(p.done) : new Uint8Array(Math.ceil((w * h) / 8));
  p._counts = new Array(palette.length).fill(0);
  p._doneCounts = new Array(palette.length).fill(0);
  for (let i = 0; i < w * h; i++) {
    const c = p._cells[i];
    if (c === EMPTY) continue;
    p._counts[c]++;
    if (isDone(p, i)) p._doneCounts[c]++;
  }
  return p;
}
const isDone = (p, i) => (p._done[i >> 3] >> (i & 7)) & 1;
function setDone(p, i, on) {
  const c = p._cells[i];
  if (c === EMPTY || !!isDone(p, i) === on) return false;
  if (on) p._done[i >> 3] |= 1 << (i & 7); else p._done[i >> 3] &= ~(1 << (i & 7));
  p._doneCounts[c] += on ? 1 : -1;
  const d = today();
  p.log = p.log || {};
  p.log[d] = (p.log[d] || 0) + (on ? 1 : -1);
  if (!p.log[d]) delete p.log[d];
  return true;
}

function totals(p) {
  if (!p.pattern) return null;
  hydrate(p);
  const total = p._counts.reduce((a, b) => a + b, 0);
  const done = p._doneCounts.reduce((a, b) => a + b, 0);
  return { total, done, pct: total ? Math.floor((done / total) * 100) : 0 };
}

function statusOf(p) {
  const t = totals(p);
  if (!t) return p.status || '준비';
  if (t.total && t.done === t.total) return '완성';
  return t.done > 0 ? '진행 중' : '준비';
}

/** 작품의 상태 날짜를 진행 상황에 맞춘다 */
function syncDates(p) {
  const s = statusOf(p);
  if (s !== '준비' && !p.startedAt) p.startedAt = Date.now();
  if (s === '완성' && !p.finishedAt) p.finishedAt = Date.now();
  if (s !== '완성') delete p.finishedAt;
  if (s === '준비' && p.pattern) delete p.startedAt;
}

/** 작품에 쓰는 실 번호 → 칸 수 */
function threadUsage(p) {
  const use = new Map();
  if (p.pattern) {
    hydrate(p);
    p.threads.forEach((code, i) => use.set(code, (use.get(code) || 0) + p._counts[i]));
  } else {
    for (const code of p.codes || []) use.set(code, 0);
  }
  return use;
}
function skeinsFor(stitches, fabric) {
  if (!stitches) return 1;
  return Math.max(1, Math.ceil(stitches / (STITCHES_PER_SKEIN[fabric] || 1800)));
}

/** 보유 실 / 전체 실 중 추천 실을 고른다 */
function recommend(hex, mode) {
  const best = nearestThread(hex);
  const ownedCodes = new Set(Object.keys(stash).filter(owned));
  const mine = ownedCodes.size ? nearestThread(hex, ownedCodes) : null;
  if (!mine) return best.code;
  if (mode === 'exact') return mine.dE <= best.dE + 0.01 ? mine.code : best.code;
  return mine.dE <= Math.max(OWNED_OK, best.dE) ? mine.code : best.code;
}

// ───────── 탭 1: 작품 목록 ─────────
function renderList() {
  const q = $('list-search').value.trim().toLowerCase();
  const items = projects
    .filter((p) => !q || p.title.toLowerCase().includes(q) || [...threadUsage(p).keys()].some((c) => c.toLowerCase().includes(q)))
    .sort((a, b) => b.createdAt - a.createdAt);
  $('project-list').replaceChildren(...items.map((p) => {
    const li = el('li', 'project-card');
    if (p.pattern) li.append(thumbnail(p));
    const body = el('div', 'card-body');
    const top = el('div', 'card-top');
    const status = statusOf(p);
    top.append(el('strong', null, p.title), el('span', 'badge-status s-' + status.replace(' ', ''), status));
    body.append(top);

    const use = threadUsage(p);
    const missing = [...use.keys()].filter((c) => !owned(c)).length;
    const meta = [`실 ${use.size}개`];
    if (missing) meta.push(`살 실 ${missing}개`);
    const t = totals(p);
    if (t) meta.unshift(`${t.pct}%`);
    body.append(el('div', 'meta', meta.join(' · ')));
    if (t) {
      const bar = el('div', 'bar-track');
      const fill = el('div', 'bar-fill');
      fill.style.width = t.pct + '%';
      bar.append(fill);
      body.append(bar);
    } else if (use.size) {
      const chips = el('div', 'chips');
      for (const c of use.keys()) chips.append(swatch(threadHex(c), 'chip'));
      body.append(chips);
    }
    body.append(el('div', 'date', fmtDate(p.createdAt)));
    li.append(body);
    li.onclick = () => openProject(p.id);
    return li;
  }));
  $('empty').hidden = projects.length > 0;
}

function thumbnail(p) {
  hydrate(p);
  const { w, h } = p.pattern;
  const c = el('canvas', 'thumb');
  c.width = w; c.height = h;
  const ctx = c.getContext('2d');
  const img = ctx.createImageData(w, h);
  const rgb = p.threads.map((code) => hexToRgb(threadHex(code)));
  for (let i = 0; i < w * h; i++) {
    const k = p._cells[i];
    if (k === EMPTY) continue;
    img.data.set([...rgb[k], 255], i * 4);
  }
  ctx.putImageData(img, 0, 0);
  return c;
}

// ───────── 탭 2: 보유 실 ─────────
function renderStash() {
  const q = $('stash-search').value.trim().toLowerCase();
  const codes = Object.keys(stash).filter(owned)
    .sort((a, b) => DMC.findIndex((d) => d[0] === a) - DMC.findIndex((d) => d[0] === b));
  const skeins = codes.reduce((s, c) => s + stash[c], 0);
  $('stash-summary').textContent = codes.length ? `실 ${codes.length}가지 · ${fmt(skeins)}타래` : '';
  const shown = codes.filter((c) => !q || c.toLowerCase().includes(q) || (byCode[c]?.name || '').toLowerCase().includes(q));
  $('stash-list').replaceChildren(...shown.map((code) => {
    const li = el('li');
    li.append(swatch(threadHex(code)), threadInfo(code));
    const minus = el('button', 'step', '−');
    minus.setAttribute('aria-label', '한 타래 빼기');
    minus.onclick = () => {
      if (stash[code] === 1 && !confirm(`DMC ${code}을(를) 보유 실에서 뺄까요?`)) return;
      stash[code]--;
      if (!stash[code]) delete stash[code];
      persist(); render();
    };
    const plus = el('button', 'step', '＋');
    plus.setAttribute('aria-label', '한 타래 더하기');
    plus.onclick = () => { stash[code]++; persist(); render(); };
    const stepper = el('div', 'stepper');
    stepper.append(minus, el('span', 'qty', stash[code]), plus);
    li.append(stepper);
    return li;
  }));
  $('stash-empty').hidden = codes.length > 0;
}

function threadInfo(code, extra) {
  const info = el('div', 'thread-info');
  info.append(el('b', null, `DMC ${code}`));
  if (byCode[code]) info.append(el('small', null, byCode[code].name));
  if (extra) info.append(el('small', 'extra', extra));
  return info;
}

// ───────── 탭 3: 장보기 ─────────
function shoppingList() {
  const need = new Map(); // code → { skeins, projects: [] }
  for (const p of projects) {
    if (statusOf(p) === '완성') continue;
    for (const [code, stitches] of threadUsage(p)) {
      if (owned(code)) continue;
      const item = need.get(code) || { skeins: 0, projects: [] };
      item.skeins += skeinsFor(stitches, p.fabric || 14);
      item.projects.push(p.title);
      need.set(code, item);
    }
  }
  return [...need].sort((a, b) => a[0].localeCompare(b[0], 'en', { numeric: true }));
}

function renderShop() {
  const list = shoppingList();
  $('shop-list').replaceChildren(...list.map(([code, item]) => {
    const li = el('li');
    li.append(swatch(threadHex(code)), threadInfo(code, `약 ${item.skeins}타래 · ${item.projects.join(', ')}`));
    const bought = el('button', 'pill', '샀어요');
    bought.onclick = () => {
      stash[code] = (stash[code] || 0) + item.skeins;
      persist(); render();
      toast(`DMC ${code}을(를) 보유 실에 넣었어요`);
    };
    li.append(bought);
    return li;
  }));
  $('shop-empty').hidden = list.length > 0;
  $('shop-badge').hidden = !list.length;
  $('shop-badge').textContent = list.length;
}

async function shareShop() {
  const list = shoppingList();
  if (!list.length) { toast('살 실이 없어요'); return; }
  const text = '십자수 실 장보기\n' + list.map(([c, i]) => `□ DMC ${c} ${byCode[c]?.name || ''} — ${i.skeins}타래`).join('\n');
  await shareOrCopy(text);
}

async function shareOrCopy(text) {
  if (navigator.share) {
    try { await navigator.share({ text }); } catch {}
    return;
  }
  try { await navigator.clipboard.writeText(text); toast('복사했어요'); } catch { toast('복사하지 못했어요'); }
}

// ───────── 작품 상세 ─────────
function openProject(id) {
  current = projects.find((p) => p.id === id);
  if (!current) return;
  hydrate(current);
  pv = { mode: 'view', zoom: 0, autoZoom: true, highlight: null };
  show('project-view'); // 먼저 보여야 화면 너비에 맞춰 도안 크기를 정할 수 있다
  renderProject();
}

function renderProject() {
  const p = current;
  $('pv-title').textContent = p.title;
  $('pv-pattern').hidden = !p.pattern;
  $('rematch-btn').hidden = !p.pattern;
  document.querySelector('.pv-layout').classList.toggle('no-pattern', !p.pattern);
  renderProgress();
  renderLegend();
  renderLog();
  if (p.pattern) {
    setMode(pv.mode);
    drawPattern();
  }
}

function renderProgress() {
  const p = current;
  const box = $('pv-progress');
  const status = statusOf(p);
  const t = totals(p);
  const rows = [];
  const head = el('div', 'progress-head');
  head.append(el('span', 'badge-status s-' + status.replace(' ', ''), status));
  if (t) head.append(el('b', 'pct', t.pct + '%'));
  rows.push(head);
  if (t) {
    const bar = el('div', 'bar-track big');
    const fill = el('div', 'bar-fill');
    fill.style.width = (t.total ? (t.done / t.total) * 100 : 0) + '%';
    bar.append(fill);
    rows.push(bar, el('div', 'meta', `${fmt(t.done)} / ${fmt(t.total)}칸 · 남은 칸 ${fmt(t.total - t.done)}`));
    const fabric = p.fabric || 14;
    const cm = (n) => ((n / fabric) * 2.54).toFixed(1);
    rows.push(el('div', 'meta', `도안 ${p.pattern.w}×${p.pattern.h}칸 · 원단 ${fabric}칸 기준 약 ${cm(p.pattern.w)}×${cm(p.pattern.h)}cm`));
  }
  const dates = [];
  if (p.startedAt) dates.push(`시작 ${fmtDate(p.startedAt)}`);
  if (p.finishedAt) dates.push(`완성 ${fmtDate(p.finishedAt)}`);
  if (dates.length) rows.push(el('div', 'meta', dates.join(' · ')));
  const missing = [...threadUsage(p).keys()].filter((c) => !owned(c)).length;
  if (missing) {
    const link = el('button', 'text-btn small', `살 실 ${missing}개 → 장보기 보기`);
    link.onclick = () => switchTab('shop-view');
    rows.push(link);
  }
  if (p.note) rows.push(el('p', 'note', p.note));
  box.replaceChildren(...rows);
}

function renderLegend() {
  const p = current;
  const ul = $('legend');
  if (!p.pattern) {
    ul.replaceChildren(...(p.codes || []).map((code) => {
      const li = el('li');
      li.append(swatch(threadHex(code)), threadInfo(code), ownBadge(code));
      return li;
    }));
    if (!(p.codes || []).length) ul.replaceChildren(el('li', 'muted', '편집을 눌러 실을 추가해 주세요.'));
    return;
  }
  const order = p.pattern.palette.map((_, i) => i).filter((i) => p._counts[i] > 0)
    .sort((a, b) => p._counts[b] - p._counts[a]);
  ul.replaceChildren(...order.map((i) => {
    const code = p.threads[i];
    const src = p.pattern.palette[i];
    const li = el('li', 'legend-row' + (pv.highlight === i ? ' active' : ''));
    const sym = el('span', 'symbol', SYMBOLS[i % SYMBOLS.length]);
    sym.style.background = '#' + threadHex(code);
    sym.style.color = inkFor(threadHex(code));
    const pair = el('div', 'pair');
    pair.append(swatch(src, 'mini'), el('span', 'arrow', '→'), swatch(threadHex(code), 'mini'));
    const dE = colorDistance(src, threadHex(code));
    const left = p._counts[i] - p._doneCounts[i];
    const info = threadInfo(code, `${fmt(p._counts[i])}칸${left ? ` · 남은 ${fmt(left)}` : ' · 완료'} · ${similarityLabel(dE)}`);
    const actions = el('div', 'row-actions');
    actions.append(ownBadge(code));
    const change = el('button', 'pill ghost', '바꾸기');
    change.onclick = (e) => { e.stopPropagation(); changeThread(i); };
    actions.append(change);
    li.append(sym, pair, info, actions);
    li.onclick = () => { pv.highlight = pv.highlight === i ? null : i; renderLegend(); drawPattern(); };
    return li;
  }));
}

function ownBadge(code) {
  return owned(code) ? el('span', 'own yes', '보유') : el('span', 'own no', '구매 필요');
}

function renderLog() {
  const p = current;
  const box = $('pv-log');
  const log = p.log || {};
  const days = Object.keys(log).filter((d) => log[d] > 0).sort();
  if (!p.pattern) {
    const parts = [`상태: ${statusOf(p)}`];
    if (p.startedAt) parts.push(`시작 ${fmtDate(p.startedAt)}`);
    if (p.finishedAt) parts.push(`완성 ${fmtDate(p.finishedAt)}`);
    box.replaceChildren(el('div', 'meta', parts.join(' · ')), el('p', 'hint', '도안이 있는 작품은 수놓은 칸이 날짜별로 기록돼요.'));
    return;
  }
  if (!days.length) {
    box.replaceChildren(el('p', 'hint', '‘수놓기’에서 칸을 누르면 날짜별로 기록돼요.'));
    return;
  }
  // 최근 14일 막대
  const recent = [];
  for (let k = 13; k >= 0; k--) {
    const d = new Date(); d.setDate(d.getDate() - k);
    const key = d.toLocaleDateString('sv-SE');
    recent.push([key, Math.max(0, log[key] || 0)]);
  }
  const max = Math.max(1, ...recent.map(([, n]) => n));
  const chart = el('div', 'chart');
  for (const [key, n] of recent) {
    const col = el('div', 'col');
    const bar = el('div', 'colbar');
    bar.style.height = Math.round((n / max) * 100) + '%';
    bar.title = `${key}: ${n}칸`;
    col.append(el('span', 'colnum', n ? fmt(n) : ''), bar, el('span', 'colday', key.slice(8).replace(/^0/, '')));
    chart.append(col);
  }
  const total = days.reduce((s, d) => s + log[d], 0);
  const avg = Math.round(total / days.length);
  const t = totals(p);
  const remain = t.total - t.done;
  const summary = [`수놓은 날 ${days.length}일`, `하루 평균 ${fmt(avg)}칸`];
  if (remain && avg) summary.push(`이 속도면 약 ${Math.ceil(remain / avg)}일 남음`);
  box.replaceChildren(el('div', 'meta', '최근 14일'), chart, el('div', 'meta', summary.join(' · ')));
}

// ── 도안 그리기 ──
const isWide = () => window.matchMedia('(min-width: 768px)').matches;

/** 화면에 도안 전체가 들어오는 칸 크기. 넓은 화면은 높이까지 맞춘다 */
function fitZoom() {
  const wrap = $('canvas-wrap');
  const { w, h } = current.pattern;
  let cs = (wrap.clientWidth - 2) / w;
  if (isWide()) {
    // 스크롤 위치와 상관없이, 맨 위로 올렸을 때 도안이 들어갈 높이
    const top = window.matchMedia('(min-width: 1000px)').matches ? 190 : wrap.getBoundingClientRect().top + window.scrollY;
    cs = Math.min(cs, (window.innerHeight - top - 32) / h);
  }
  return Math.max(3, Math.min(40, Math.floor(cs)));
}

function drawPattern() {
  const p = current;
  if (!p?.pattern) return;
  const { w, h } = p.pattern;
  if (pv.autoZoom) pv.zoom = fitZoom();
  const cs = pv.zoom;
  // 캔버스가 너무 크면 Safari가 그리지 못하므로 해상도를 줄인다
  const dpr = Math.min(window.devicePixelRatio || 1, Math.sqrt(16e6 / (w * h * cs * cs)));
  const canvas = $('pattern');
  canvas.width = Math.floor(w * cs * dpr);
  canvas.height = Math.floor(h * cs * dpr);
  canvas.style.width = w * cs + 'px';
  canvas.style.height = h * cs + 'px';
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, w * cs, h * cs);
  for (let i = 0; i < w * h; i++) drawCell(ctx, i, cs);
  drawGrid(ctx, cs);
}

function drawCell(ctx, i, cs) {
  const p = current;
  const { w } = p.pattern;
  const x = (i % w) * cs, y = Math.floor(i / w) * cs;
  const k = p._cells[i];
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(x, y, cs, cs);
  if (k === EMPTY) return;
  const hex = threadHex(p.threads[k]);
  const dim = pv.highlight != null && pv.highlight !== k;
  if (isDone(p, i)) {
    ctx.globalAlpha = dim ? 0.15 : 1;
    ctx.fillStyle = '#' + hex;
    ctx.fillRect(x, y, cs, cs);
  } else {
    ctx.globalAlpha = dim ? 0.08 : 0.35;
    ctx.fillStyle = '#' + hex;
    ctx.fillRect(x, y, cs, cs);
    if (cs >= 11 && !dim) {
      ctx.globalAlpha = 1;
      ctx.fillStyle = '#1c1c1e';
      ctx.font = `${Math.floor(cs * 0.62)}px -apple-system, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(SYMBOLS[k % SYMBOLS.length], x + cs / 2, y + cs / 2 + 0.5);
    }
  }
  ctx.globalAlpha = 1;
}

function drawGrid(ctx, cs) {
  const { w, h } = current.pattern;
  const line = (x1, y1, x2, y2) => { ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); };
  if (cs >= 5) {
    ctx.strokeStyle = 'rgba(0,0,0,0.12)';
    ctx.lineWidth = 0.5;
    for (let x = 0; x <= w; x++) line(x * cs, 0, x * cs, h * cs);
    for (let y = 0; y <= h; y++) line(0, y * cs, w * cs, y * cs);
  }
  // 10칸마다 굵은 선 (칸 세기용)
  ctx.strokeStyle = 'rgba(0,0,0,0.45)';
  ctx.lineWidth = 1;
  for (let x = 0; x <= w; x += 10) line(x * cs, 0, x * cs, h * cs);
  for (let y = 0; y <= h; y += 10) line(0, y * cs, w * cs, y * cs);
}

function setMode(mode) {
  pv.mode = mode;
  $('mode-view').classList.toggle('on', mode === 'view');
  $('mode-stitch').classList.toggle('on', mode === 'stitch');
  $('pattern').classList.toggle('painting', mode === 'stitch');
  $('mode-hint').textContent = mode === 'stitch'
    ? '칸을 누르거나 손가락으로 문지르면 완료 표시돼요. 완료된 칸을 누르면 취소돼요.'
    : '칸을 누르면 같은 색만 강조해서 보여줘요. 두 손가락으로 화면을 움직일 수 있어요.';
}

function cellAt(e) {
  const r = $('pattern').getBoundingClientRect();
  const { w, h } = current.pattern;
  const x = Math.floor((e.clientX - r.left) / pv.zoom);
  const y = Math.floor((e.clientY - r.top) / pv.zoom);
  return x >= 0 && y >= 0 && x < w && y < h ? y * w + x : -1;
}

let paint = null; // 문지르는 중: { target: 완료/취소, changed }
function onPointerDown(e) {
  if (!current?.pattern) return;
  const i = cellAt(e);
  if (i < 0) return;
  if (pv.mode === 'view') {
    const k = current._cells[i];
    pv.highlight = k === EMPTY || pv.highlight === k ? null : k;
    renderLegend(); drawPattern();
    return;
  }
  e.preventDefault();
  $('pattern').setPointerCapture(e.pointerId);
  paint = { target: !isDone(current, i), changed: 0, last: -1 };
  paintCell(i);
}
function onPointerMove(e) {
  if (!paint) return;
  const i = cellAt(e);
  if (i >= 0 && i !== paint.last) paintCell(i);
}
function paintCell(i) {
  paint.last = i;
  if (!setDone(current, i, paint.target)) return;
  paint.changed++;
  const ctx = $('pattern').getContext('2d');
  drawCell(ctx, i, pv.zoom);
  const { w } = current.pattern;
  const cs = pv.zoom;
  ctx.strokeStyle = 'rgba(0,0,0,0.12)';
  ctx.lineWidth = 0.5;
  ctx.strokeRect((i % w) * cs, Math.floor(i / w) * cs, cs, cs);
}
function onPointerUp() {
  if (!paint) return;
  const changed = paint.changed;
  paint = null;
  if (!changed) return;
  current.done = b64(current._done);
  const before = current.finishedAt;
  syncDates(current);
  persist();
  drawPattern();
  renderProgress(); renderLegend(); renderLog();
  if (!before && current.finishedAt) toast('완성을 축하해요! 🎉');
}

function changeThread(i) {
  const p = current;
  openPicker({
    title: '실 바꾸기',
    single: true,
    selected: [p.threads[i]],
    target: p.pattern.palette[i],
    onDone: ([code]) => {
      if (!code) return;
      p.threads[i] = code;
      persist();
      openProject(p.id);
      render();
    },
    onCancel: () => show('project-view'),
  });
}

function rematch() {
  const p = current;
  if (!confirm('지금 보유 실을 기준으로 실을 다시 고를까요? 직접 바꾼 실도 다시 정해져요.')) return;
  p.threads = p.pattern.palette.map((hex) => recommend(hex, p.matchMode || 'owned'));
  persist();
  renderProject();
  render();
  toast('실을 다시 추천했어요');
}

// ───────── 새 작품 ─────────
let pending = null; // { imageData, W, H, detected, pattern }

function openNew() {
  pending = null;
  $('new-title').value = '';
  $('new-choice').hidden = false;
  $('import-setup').hidden = true;
  $('new-create').disabled = true;
  show('new-view');
}

async function onImagePicked(file) {
  try {
    const bmp = await createImageBitmap(file);
    const W = bmp.width, H = bmp.height;
    const c = document.createElement('canvas');
    c.width = W; c.height = H;
    const ctx = c.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(bmp, 0, 0);
    const data = ctx.getImageData(0, 0, W, H).data;
    const cell = detectCell(data, W, H);
    let cols = Math.round(W / cell);
    pending = { data, W, H, cell };
    if (cols > MAX_SIDE || (cell === 1 && W > 200)) {
      cols = Math.min(100, W);
      toast('픽셀 칸을 자동으로 찾지 못했어요. 가로 칸 수를 확인해 주세요.');
    }
    pending.autoCols = cols;
    if (!$('new-title').value.trim()) $('new-title').value = file.name.replace(/\.[^.]+$/, '');
    $('cols-input').value = cols;
    $('new-choice').hidden = true;
    $('import-setup').hidden = false;
    buildPending();
  } catch {
    toast('이미지를 열지 못했어요');
  }
}

/** 확대 저장된 픽셀 이미지에서 한 칸의 크기(픽셀)를 찾는다: 같은 색이 이어지는 길이들의 최대공약수 */
function detectCell(d, W, H) {
  const px = (x, y) => { const i = (y * W + x) * 4; return d[i + 3] < 128 ? -1 : (d[i] << 16) | (d[i + 1] << 8) | d[i + 2]; };
  const gcd = (a, b) => (b ? gcd(b, a % b) : a);
  let g = 0;
  const stepY = Math.max(1, Math.floor(H / 200)), stepX = Math.max(1, Math.floor(W / 200));
  for (let y = 0; y < H; y += stepY) {
    let run = 1;
    for (let x = 1; x <= W; x++) {
      if (x < W && px(x, y) === px(x - 1, y)) run++;
      else { g = gcd(g, run); run = 1; if (g === 1) return 1; }
    }
  }
  for (let x = 0; x < W; x += stepX) {
    let run = 1;
    for (let y = 1; y <= H; y++) {
      if (y < H && px(x, y) === px(x, y - 1)) run++;
      else { g = gcd(g, run); run = 1; if (g === 1) return 1; }
    }
  }
  return g || 1;
}

/** 이미지를 cols×rows 칸으로 나눠 각 칸 가운데 색을 읽는다 */
function sampleGrid({ data, W, H }, cols) {
  const size = W / cols;
  const rows = Math.max(1, Math.round(H / size));
  const colors = new Array(cols * rows);
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const sx = Math.min(W - 1, Math.floor((x + 0.5) * size));
      const sy = Math.min(H - 1, Math.floor((y + 0.5) * (H / rows)));
      const i = (sy * W + sx) * 4;
      colors[y * cols + x] = data[i + 3] < 128 ? -1 : (data[i] << 16) | (data[i + 1] << 8) | data[i + 2];
    }
  }
  // 색이 너무 많으면(사진 등) 비슷한 색끼리 묶는다
  let step = 1, palette;
  for (;;) {
    const q = (v) => (v < 0 ? -1 : step === 1 ? v : (((v >> 16 & 255) / step | 0) * step << 16) | (((v >> 8 & 255) / step | 0) * step << 8) | (((v & 255) / step | 0) * step));
    palette = new Map();
    for (const v of colors) if (v >= 0) palette.set(q(v), true);
    if (palette.size <= 254) {
      const idx = new Map([...palette.keys()].map((v, i) => [v, i]));
      const cells = new Uint8Array(colors.length);
      colors.forEach((v, i) => (cells[i] = v < 0 ? EMPTY : idx.get(q(v))));
      return { w: cols, h: rows, palette: [...palette.keys()].map((v) => rgbToHex([v >> 16 & 255, v >> 8 & 255, v & 255])), cells, reduced: step > 1 };
    }
    step = step === 1 ? 8 : step * 2;
  }
}

function buildPending() {
  if (!pending) return;
  let cols = Math.round(Number($('cols-input').value));
  if (!(cols >= 4)) cols = 4;
  cols = Math.min(cols, MAX_SIDE, pending.W);
  const pat = sampleGrid(pending, cols);
  if (pat.h > MAX_SIDE) { toast(`세로가 ${MAX_SIDE}칸을 넘어요. 가로 칸 수를 줄여 주세요.`); }
  const mode = $('match-mode').value;
  pat.threads = pat.palette.map((hex) => recommend(hex, mode));
  pending.pattern = pat;

  // 미리보기: 추천 실 색으로
  const cv = $('preview');
  const scale = Math.max(1, Math.floor(Math.min(isWide() ? 500 : 320, cv.parentElement.clientWidth - 18) / Math.max(pat.w, pat.h)));
  cv.width = pat.w * scale; cv.height = pat.h * scale;
  const ctx = cv.getContext('2d');
  ctx.clearRect(0, 0, cv.width, cv.height);
  pat.cells.forEach((k, i) => {
    if (k === EMPTY) return;
    ctx.fillStyle = '#' + threadHex(pat.threads[k]);
    ctx.fillRect((i % pat.w) * scale, Math.floor(i / pat.w) * scale, scale, scale);
  });

  const stitches = pat.cells.reduce((s, k) => s + (k !== EMPTY), 0);
  const codes = new Set(pat.threads);
  const missing = [...codes].filter((c) => !owned(c)).length;
  const fabric = Number($('fabric-input').value);
  const cm = (n) => ((n / fabric) * 2.54).toFixed(1);
  $('import-info').textContent =
    `${pat.w}×${pat.h}칸 · ${fmt(stitches)}땀 · 이미지 색 ${pat.palette.length}개 → DMC 실 ${codes.size}가지` +
    (missing ? ` (그중 ${missing}가지는 장보기에 추가돼요)` : ' (모두 보유 실)') +
    ` · 완성 크기 약 ${cm(pat.w)}×${cm(pat.h)}cm` +
    (pat.reduced ? ' · 색이 많아 비슷한 색끼리 묶었어요' : '');
  $('new-create').disabled = pat.h > MAX_SIDE || !stitches;
}

function createFromPending() {
  const title = $('new-title').value.trim();
  if (!title) { toast('제목을 입력해 주세요'); $('new-title').focus(); return; }
  const pat = pending.pattern;
  const p = {
    id: newId(),
    title,
    note: '',
    createdAt: Date.now(),
    fabric: Number($('fabric-input').value),
    matchMode: $('match-mode').value,
    pattern: { w: pat.w, h: pat.h, palette: pat.palette, cells: b64(pat.cells) },
    threads: pat.threads,
  };
  projects.push(p);
  persist();
  pending = null;
  render();
  openProject(p.id);
  toast('도안을 만들었어요');
}

function createManual() {
  const title = $('new-title').value.trim();
  if (!title) { toast('먼저 제목을 입력해 주세요'); $('new-title').focus(); return; }
  const p = { id: newId(), title, note: '', codes: [], status: '준비', fabric: 14, createdAt: Date.now() };
  projects.push(p);
  persist();
  render();
  current = p;
  openEditor();
}
const newId = () => crypto.randomUUID?.() || String(Date.now()) + Math.random().toString(16).slice(2);

// ───────── 작품 편집 ─────────
function openEditor() {
  const p = current;
  $('title-input').value = p.title;
  $('note-input').value = p.note || '';
  $('fabric-edit').value = String(p.fabric || 14);
  $('manual-fields').hidden = !!p.pattern;
  $('status-input').value = p.status || '준비';
  draft = [...(p.codes || [])];
  renderDraft();
  show('edit-view');
}

function renderDraft() {
  $('count').textContent = draft.length;
  $('thread-list').replaceChildren(...draft.map((code, i) => {
    const li = el('li');
    const up = el('button', 'row-btn', '↑');
    up.disabled = i === 0;
    up.setAttribute('aria-label', '위로');
    up.onclick = () => { [draft[i - 1], draft[i]] = [draft[i], draft[i - 1]]; renderDraft(); };
    const rm = el('button', 'row-btn remove', '−');
    rm.setAttribute('aria-label', '삭제');
    rm.onclick = () => { draft.splice(i, 1); renderDraft(); };
    li.append(swatch(threadHex(code)), threadInfo(code), ownBadge(code), up, rm);
    return li;
  }));
}

function saveEditor() {
  const p = current;
  const title = $('title-input').value.trim();
  if (!title) { toast('제목을 입력해 주세요'); return; }
  p.title = title;
  p.note = $('note-input').value.trim();
  p.fabric = Number($('fabric-edit').value);
  if (!p.pattern) {
    p.codes = draft;
    p.status = $('status-input').value;
    syncDates(p);
  }
  persist();
  render();
  openProject(p.id);
  toast('저장했어요');
}

function projectText(p) {
  const use = threadUsage(p);
  const lines = [...use].map(([c, n]) => `DMC ${c} ${byCode[c]?.name || ''}${n ? ` (${fmt(n)}칸)` : ''}${owned(c) ? '' : ' — 구매 필요'}`);
  const t = totals(p);
  return [p.title, t ? `진행 ${t.pct}% (${fmt(t.done)}/${fmt(t.total)}칸)` : `상태: ${statusOf(p)}`, `실 ${use.size}개`, ...lines, p.note ? `\n${p.note}` : '']
    .filter(Boolean).join('\n');
}

// ───────── 실 선택 ─────────
let picker = null; // { selected: [], single, target, onDone, onCancel }

function openPicker(opts) {
  picker = { ...opts, selected: [...(opts.selected || [])] };
  $('picker-title').textContent = opts.title || 'DMC 실 선택';
  $('picker-search').value = '';
  $('picker-owned').checked = false;
  $('picker-done').hidden = !!opts.single;
  const target = $('picker-target');
  target.hidden = !opts.target;
  if (opts.target) {
    target.replaceChildren(swatch(opts.target), el('span', null, '이미지 색과 비슷한 순서로 보여요'));
  }
  renderGrid();
  show('picker-view');
}

function renderGrid() {
  const q = $('picker-search').value.trim().toLowerCase();
  const ownedOnly = $('picker-owned').checked;
  let list = DMC.filter(([c, n]) => (!q || c.toLowerCase().includes(q) || n.toLowerCase().includes(q)) && (!ownedOnly || owned(c)));
  if (picker.target) {
    const lab = rgbToLab(hexToRgb(picker.target));
    list = list.map((t) => [t, deltaE2000(lab, rgbToLab(hexToRgb(t[2])))]).sort((a, b) => a[1] - b[1]).slice(0, q || ownedOnly ? 500 : 60).map(([t]) => t);
  }
  $('grid').replaceChildren(...list.map(([code, name, hex]) => {
    const t = el('button', 'tile' + (picker.selected.includes(code) ? ' on' : ''));
    const box = el('div', 'box');
    box.style.background = '#' + hex;
    if (owned(code)) box.append(el('span', 'dot', '보유'));
    t.append(box, el('b', null, code), el('small', null, name));
    t.onclick = () => {
      if (picker.single) { const cb = picker.onDone; picker = null; cb([code]); return; }
      toggle(code);
      t.classList.toggle('on', picker.selected.includes(code));
    };
    return t;
  }));
  const raw = $('picker-search').value.trim();
  const custom = $('custom-add');
  custom.hidden = !raw || !!byCode[raw] || picker.selected.includes(raw);
  custom.textContent = `＋ ‘${raw}’ 직접 추가`;
  custom.onclick = () => {
    if (picker.single) { const cb = picker.onDone; picker = null; cb([raw]); return; }
    toggle(raw); renderGrid();
  };
  $('picker-done').textContent = `완료 (${picker.selected.length})`;
}

function toggle(code) {
  const s = picker.selected;
  const i = s.indexOf(code);
  if (i >= 0) s.splice(i, 1); else s.push(code);
  $('picker-done').textContent = `완료 (${s.length})`;
}

// ───────── 백업 ─────────
function exportBackup() {
  const blob = new Blob([JSON.stringify({ app: 'stitch', version: 2, projects, stash }, skipCache, 2)], { type: 'application/json' });
  const a = el('a');
  a.href = URL.createObjectURL(blob);
  a.download = `실기록-백업-${today()}.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

async function importBackup(file) {
  try {
    const data = JSON.parse(await file.text());
    const incoming = Array.isArray(data) ? data : data.projects;
    if (!Array.isArray(incoming)) throw new Error();
    const ids = new Set(projects.map((p) => p.id));
    const added = incoming.filter((p) => p && p.id && p.title && (Array.isArray(p.codes) || p.pattern) && !ids.has(p.id));
    projects.push(...added);
    let stashAdded = 0;
    for (const [code, n] of Object.entries(data.stash || {})) {
      if (!(n > 0)) continue;
      if (!stash[code]) stashAdded++;
      stash[code] = Math.max(stash[code] || 0, n);
    }
    persist();
    render();
    toast(`작품 ${added.length}개${stashAdded ? `, 보유 실 ${stashAdded}가지` : ''}를 불러왔어요`);
  } catch {
    toast('백업 파일을 읽지 못했어요');
  }
}

// ───────── 이벤트 ─────────
for (const b of $('tabs').children) b.onclick = () => switchTab(b.dataset.tab);
$('new-btn').onclick = openNew;
$('list-search').oninput = renderList;
$('stash-search').oninput = renderStash;
$('shop-share').onclick = shareShop;

$('stash-add').onclick = () => openPicker({
  title: '보유 실 고르기',
  selected: Object.keys(stash).filter(owned),
  onDone: (codes) => {
    const keep = new Set(codes);
    for (const c of Object.keys(stash)) if (!keep.has(c)) delete stash[c];
    for (const c of codes) if (!stash[c]) stash[c] = 1;
    persist();
    switchTab('stash-view');
  },
  onCancel: () => switchTab('stash-view'),
});

$('back-btn').onclick = () => { current = null; switchTab('list-view'); };
$('edit-btn').onclick = openEditor;
$('mode-view').onclick = () => setMode('view');
$('mode-stitch').onclick = () => { pv.highlight = null; setMode('stitch'); renderLegend(); drawPattern(); };
$('zoom-in').onclick = () => { pv.autoZoom = false; pv.zoom = Math.min(40, Math.round(pv.zoom * 1.4) + 1); drawPattern(); };
$('zoom-out').onclick = () => { pv.autoZoom = false; pv.zoom = Math.max(2, Math.round(pv.zoom / 1.4)); drawPattern(); };
$('rematch-btn').onclick = rematch;
const canvas = $('pattern');
canvas.addEventListener('pointerdown', onPointerDown);
canvas.addEventListener('pointermove', onPointerMove);
canvas.addEventListener('pointerup', onPointerUp);
canvas.addEventListener('pointercancel', onPointerUp);

$('new-cancel').onclick = () => switchTab('list-view');
$('pick-image').onclick = () => $('image-file').click();
$('pick-again').onclick = () => $('image-file').click();
$('image-file').onchange = (e) => { const f = e.target.files[0]; e.target.value = ''; if (f) onImagePicked(f); };
$('manual-btn').onclick = createManual;
$('cols-input').onchange = buildPending;
$('cols-auto').onclick = () => { if (pending) { $('cols-input').value = pending.autoCols; buildPending(); } };
$('match-mode').onchange = buildPending;
$('fabric-input').onchange = buildPending;
$('new-create').onclick = createFromPending;

$('cancel-btn').onclick = () => openProject(current.id);
$('save-btn').onclick = saveEditor;
$('add-thread-btn').onclick = () => openPicker({
  selected: draft,
  onDone: (codes) => { draft = codes; renderDraft(); show('edit-view'); },
  onCancel: () => show('edit-view'),
});
$('share-btn').onclick = () => shareOrCopy(projectText(current));
$('delete-btn').onclick = () => {
  if (!confirm('이 작품을 삭제할까요? 되돌릴 수 없어요.')) return;
  projects = projects.filter((p) => p !== current);
  current = null;
  persist();
  switchTab('list-view');
};

$('picker-search').oninput = renderGrid;
$('picker-owned').onchange = renderGrid;
$('picker-done').onclick = () => { const p = picker; picker = null; p.onDone(p.selected); };
$('picker-cancel').onclick = () => { const p = picker; picker = null; p.onCancel(); };

$('menu-btn').onclick = () => $('menu').showModal();
$('menu-close').onclick = () => $('menu').close();
$('export-btn').onclick = exportBackup;
$('import-btn').onclick = () => $('import-file').click();
$('import-file').onchange = (e) => { if (e.target.files[0]) importBackup(e.target.files[0]); e.target.value = ''; $('menu').close(); };

// 아이패드를 돌리거나 창 크기가 바뀌면 (직접 확대하지 않았을 때) 도안을 다시 맞춘다
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => { if (current?.pattern && !$('project-view').hidden && pv.autoZoom) drawPattern(); }, 150);
});

// 홈 화면 앱에서 저장 공간이 지워지지 않도록 요청
navigator.storage?.persist?.();
if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js');

switchTab('list-view');
