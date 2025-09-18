// Minimal site behavior: fetch JSON catalogs and render lists accessibly
async function fetchJSON(url) {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.status}`);
  return res.json();
}

function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') el.className = v; else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2).toLowerCase(), v); else el.setAttribute(k, v);
  }
  for (const c of children) el.append(c);
  return el;
}

function formatDate(s) {
  if (!s) return '';
  try { return new Date(s).toLocaleDateString(); } catch { return s; }
}

export async function renderList(elId, dataUrl, mapItem) {
  const root = document.getElementById(elId);
  if (!root) return;
  try {
    const data = await fetchJSON(dataUrl);
    const ul = h('ul', { class: 'list', role: 'list' });
    data.forEach(item => ul.append(mapItem(item)));
    root.innerHTML = '';
    root.append(ul);
  } catch (e) {
    root.textContent = 'Error loading content.';
    console.error(e);
  }
}

export function makeHeader(active) {
  const nav = h('nav', {},
    h('a', { href: './index.html', 'aria-current': active==='home' ? 'page' : null }, 'Home'),
    h('a', { href: './prayer.html', 'aria-current': active==='prayer' ? 'page' : null }, 'Prayer Points'),
    h('a', { href: './sermons.html', 'aria-current': active==='sermons' ? 'page' : null }, 'Sermon Summaries'),
    h('a', { href: './transcripts.html', 'aria-current': active==='transcripts' ? 'page' : null }, 'Transcripts'),
    h('a', { href: './presentations.html', 'aria-current': active==='presentations' ? 'page' : null }, 'Presentations')
  );
  return h('header', {}, nav);
}

export function card(title, meta, href) {
  return h('li', {},
    h('a', { href }, title),
    meta ? h('div', { class: 'badge' }, meta) : null
  );
}

// Prayer page: filter by year and search text
export async function initPrayerPage({
  listId = 'list',
  dataUrl = './data/prayer_points.json',
  yearSelectId = 'year-filter',
  searchInputId = 'search',
  clearBtnId = 'clear-filters',
} = {}) {
  const listEl = document.getElementById(listId);
  const yearEl = document.getElementById(yearSelectId);
  const searchEl = document.getElementById(searchInputId);
  const clearEl = document.getElementById(clearBtnId);
  if (!listEl || !yearEl || !searchEl) return;

  let all = [];

  function render(items) {
    const ul = h('ul', { class: 'list', role: 'list' });
    items.forEach(p => ul.append(card(p.title || p.theme || 'Untitled', p.week_of ? formatDate(p.week_of) : '', p.path || '#')));
    listEl.innerHTML = '';
    listEl.append(ul);
  }

  function uniqueYears(items) {
    const ys = new Set();
    items.forEach(p => {
      if (p.week_of) {
        const y = new Date(p.week_of).getFullYear();
        if (!Number.isNaN(y)) ys.add(y);
      }
    });
    return Array.from(ys).sort((a, b) => b - a);
  }

  function applyFilters() {
    const yearVal = yearEl.value;
    const q = searchEl.value.trim().toLowerCase();
    let items = all.slice();
    if (yearVal && yearVal !== 'All') {
      items = items.filter(p => p.week_of && String(new Date(p.week_of).getFullYear()) === yearVal);
    }
    if (q) {
      items = items.filter(p => {
        const hay = [(p.title || ''), (p.theme || ''), (p.path || '')].join(' ').toLowerCase();
        return hay.includes(q);
      });
    }
    render(items);
  }

  function populateYears(items) {
    const years = uniqueYears(items);
    yearEl.innerHTML = '';
    const allOpt = h('option', {}, 'All');
    allOpt.value = 'All';
    yearEl.append(allOpt);
    years.forEach(y => {
      const opt = h('option', {}, String(y));
      opt.value = String(y);
      yearEl.append(opt);
    });
    yearEl.disabled = false;
  }

  // debounce search
  let t;
  const onSearch = () => {
    clearTimeout(t);
    t = setTimeout(applyFilters, 200);
  };

  try {
    all = await fetchJSON(dataUrl);
    populateYears(all);
    applyFilters();
  } catch (e) {
    listEl.textContent = 'Error loading content.';
    console.error(e);
  }

  yearEl.addEventListener('change', applyFilters);
  searchEl.addEventListener('input', onSearch);
  if (clearEl) {
    clearEl.addEventListener('click', () => {
      searchEl.value = '';
      yearEl.value = 'All';
      applyFilters();
      searchEl.focus();
    });
  }
}
