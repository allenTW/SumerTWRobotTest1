'use strict';

// One file per request: the body is the raw file, all metadata rides in the
// query string. XHR (not fetch) because it is the only way to get upload
// progress events.

const $ = (id) => document.getElementById(id);

const el = {
  gate: $('gate'), gateForm: $('gate-form'), gateToken: $('gate-token'),
  gateError: $('gate-error'),
  app: $('app'), rootHint: $('root-hint'),
  category: $('category'), newCategory: $('new-category'),
  newRow: $('new-category-row'), newName: $('new-category-name'),
  newSave: $('new-category-save'), newCancel: $('new-category-cancel'),
  tags: $('tags'), note: $('note'),
  drop: $('drop'), picker: $('picker'), queue: $('queue'),
  recent: $('recent'), refresh: $('refresh'),
};

const LAST_CATEGORY_KEY = 'uploader.lastCategory';
let maxBytes = 2 * 1024 * 1024 * 1024;
let uploading = Promise.resolve();

function humanBytes(n) {
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i += 1; }
  return `${n < 10 && i > 0 ? n.toFixed(1) : Math.round(n)} ${units[i]}`;
}

async function api(path, options = {}) {
  const res = await fetch(path, { credentials: 'same-origin', ...options });
  let body = {};
  try { body = await res.json(); } catch (_) { /* non-JSON error page */ }
  if (!res.ok) {
    const err = new Error(body.error || `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return body;
}

// ---- boot / auth ---------------------------------------------------------

async function boot() {
  try {
    const config = await api('/api/config');
    el.gate.hidden = true;
    el.app.hidden = false;
    maxBytes = config.maxBytes || maxBytes;
    el.rootHint.textContent = `檔案會存到 ${config.uploadRoot}`;
    renderCategories(config.categories);
    loadRecent();
  } catch (err) {
    if (err.status === 401) {
      el.app.hidden = true;
      el.gate.hidden = false;
      el.gateToken.focus();
    } else {
      el.gateError.textContent = `無法連線：${err.message}`;
      el.gateError.hidden = false;
      el.gate.hidden = false;
    }
  }
}

el.gateForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  el.gateError.hidden = true;
  try {
    await api('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: el.gateToken.value.trim() }),
    });
    el.gateToken.value = '';
    boot();
  } catch (err) {
    el.gateError.textContent = err.message;
    el.gateError.hidden = false;
  }
});

// ---- categories ----------------------------------------------------------

function renderCategories(categories) {
  const previous = el.category.value || localStorage.getItem(LAST_CATEGORY_KEY);
  el.category.innerHTML = '';
  for (const name of categories) {
    const option = document.createElement('option');
    option.value = name;
    option.textContent = name;
    el.category.append(option);
  }
  if (previous && categories.includes(previous)) el.category.value = previous;
}

el.category.addEventListener('change', () => {
  localStorage.setItem(LAST_CATEGORY_KEY, el.category.value);
});

el.newCategory.addEventListener('click', () => {
  el.newRow.hidden = false;
  el.newName.focus();
});

el.newCancel.addEventListener('click', () => {
  el.newRow.hidden = true;
  el.newName.value = '';
});

el.newSave.addEventListener('click', async () => {
  const name = el.newName.value.trim();
  if (!name) return;
  try {
    const { categories } = await api('/api/category', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    renderCategories(categories);
    el.category.value = name;
    localStorage.setItem(LAST_CATEGORY_KEY, name);
    el.newRow.hidden = true;
    el.newName.value = '';
  } catch (err) {
    alert(`建立分類失敗：${err.message}`);
  }
});

el.newName.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') { event.preventDefault(); el.newSave.click(); }
});

// ---- file selection ------------------------------------------------------

el.drop.addEventListener('click', () => el.picker.click());

el.drop.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    el.picker.click();
  }
});

el.picker.addEventListener('change', () => {
  enqueue([...el.picker.files]);
  el.picker.value = '';
});

for (const type of ['dragenter', 'dragover']) {
  el.drop.addEventListener(type, (event) => {
    event.preventDefault();
    el.drop.classList.add('over');
  });
}

for (const type of ['dragleave', 'drop']) {
  el.drop.addEventListener(type, () => el.drop.classList.remove('over'));
}

el.drop.addEventListener('drop', (event) => {
  event.preventDefault();
  enqueue([...event.dataTransfer.files]);
});

// The whole page swallows stray drops so a mis-aimed file does not navigate
// the browser away from the form.
window.addEventListener('dragover', (e) => e.preventDefault());
window.addEventListener('drop', (e) => e.preventDefault());

// ---- upload --------------------------------------------------------------

function enqueue(files) {
  if (!files.length) return;
  // Metadata is read once per batch, so editing the note mid-upload does not
  // retroactively change files already queued.
  const meta = {
    category: el.category.value,
    tags: el.tags.value.trim(),
    note: el.note.value.trim(),
  };
  for (const file of files) {
    const row = addRow(file);
    uploading = uploading.then(() => upload(file, meta, row));
  }
  uploading = uploading.then(loadRecent);
}

function addRow(file) {
  const li = document.createElement('li');
  li.innerHTML = `
    <div class="name"></div>
    <div class="bar"><i></i></div>
    <div class="state">等待中…</div>`;
  li.querySelector('.name').textContent = `${file.name} · ${humanBytes(file.size)}`;
  el.queue.prepend(li);
  return {
    bar: li.querySelector('.bar > i'),
    state: li.querySelector('.state'),
  };
}

function upload(file, meta, row) {
  if (file.size === 0) {
    row.state.textContent = '略過：空檔案';
    row.state.className = 'state failed';
    return Promise.resolve();
  }
  if (file.size > maxBytes) {
    row.state.textContent = `略過：超過 ${humanBytes(maxBytes)} 上限`;
    row.state.className = 'state failed';
    return Promise.resolve();
  }

  const query = new URLSearchParams({
    category: meta.category,
    name: file.name,
    tags: meta.tags,
    note: meta.note,
  });

  return new Promise((resolve) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `/api/upload?${query}`);
    xhr.withCredentials = true;
    xhr.setRequestHeader('Content-Type', 'application/octet-stream');

    xhr.upload.addEventListener('progress', (event) => {
      if (!event.lengthComputable) return;
      const pct = Math.round((event.loaded / event.total) * 100);
      row.bar.style.width = `${pct}%`;
      row.state.textContent = `上傳中 ${pct}%`;
    });

    xhr.addEventListener('load', () => {
      let body = {};
      try { body = JSON.parse(xhr.responseText); } catch (_) { /* ignore */ }
      if (xhr.status === 200 && body.ok) {
        row.bar.style.width = '100%';
        row.state.textContent = `已存到 ${body.item.storedPath}`;
        row.state.className = 'state done';
      } else {
        row.state.textContent = `失敗：${body.error || `HTTP ${xhr.status}`}`;
        row.state.className = 'state failed';
      }
      resolve();
    });

    xhr.addEventListener('error', () => {
      row.state.textContent = '失敗：連線中斷';
      row.state.className = 'state failed';
      resolve();
    });

    row.state.textContent = '上傳中 0%';
    xhr.send(file);
  });
}

// ---- recent --------------------------------------------------------------

async function loadRecent() {
  try {
    const { items } = await api('/api/recent');
    el.recent.innerHTML = '';
    if (!items.length) {
      el.recent.innerHTML = '<li class="muted">還沒有任何上傳紀錄。</li>';
      return;
    }
    for (const item of items) {
      const li = document.createElement('li');
      li.innerHTML = '<div class="name"></div><div class="state"></div>';
      li.querySelector('.name').textContent = item.storedPath;
      li.querySelector('.state').textContent =
        `${item.category} · ${humanBytes(item.bytes)} · ` +
        new Date(item.uploadedAt).toLocaleString('zh-TW');
      el.recent.append(li);
    }
  } catch (err) {
    el.recent.innerHTML = '<li class="error"></li>';
    el.recent.firstChild.textContent = `讀取失敗：${err.message}`;
  }
}

el.refresh.addEventListener('click', loadRecent);

boot();
