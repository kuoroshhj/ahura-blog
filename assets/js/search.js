/**
 * Ahura Blog — جستجوی آفلاین
 * Vanilla JS — بدون وابستگی
 */
(function() {
  'use strict';

  const input = document.getElementById('search-input');
  const results = document.getElementById('search-results');
  const status = document.getElementById('search-status');
  const BASE = input ? (input.getAttribute('data-base') || '') : '';
  let data = null;

  if (!input || !results) return;

  // بارگذاری دیتای جستجو
  fetch(BASE + '/search.json')
    .then(r => {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(json => {
      data = json;
      if (status) status.textContent = json.length + ' پست برای جستجو';
      input.disabled = false;
      input.placeholder = 'جستجو بین همه نوشته‌ها …';
      input.focus();
    })
    .catch(err => {
      if (status) status.textContent = '⚠️ خطا در بارگذاری: ' + err.message;
    });

  // جستجو با هر بار تایپ
  input.addEventListener('input', function() {
    const q = this.value.trim().toLowerCase();
    if (!q || !data) {
      results.innerHTML = '';
      return;
    }

    // امتیازدهی: عنوان > تگ > دسته > محتوا
    const scored = data.map(item => {
      let score = 0;
      const titleMatch = item.t.toLowerCase().includes(q);
      const catMatch = item.c.toLowerCase().includes(q);
      const tagMatch = item.g.some(t => t.toLowerCase().includes(q));
      const bodyMatch = item.b && item.b.toLowerCase().includes(q);

      if (titleMatch) score += 10;
      if (tagMatch) score += 5;
      if (catMatch) score += 3;
      if (bodyMatch) score += 1;

      // اولویت تطابق کامل عنوان
      if (item.t.toLowerCase() === q) score += 20;

      return { item, score };
    })
    .filter(s => s.score > 0)
    .sort((a, b) => b.score - a.score);

    if (scored.length === 0) {
      results.innerHTML = '<div class="search-no-result">😕 هیچ نتیجه‌ای پیدا نشد</div>';
      return;
    }

    results.innerHTML = scored.map(s => {
      const p = s.item;
      const badgeCls = p.s === 'done' ? 'status-done' : 'status-running';
      const badgeTxt = p.s === 'done' ? '✅ انجام شده' : '⏳ در حال انجام';
      const tagsHtml = p.g.map(t => `<span class="tag-badge" style="font-size:11px;padding:2px 8px">${t}</span>`).join('');
      const url = p.u.startsWith('/') ? BASE + p.u : p.u;
      return `<a href="${url}" class="thread-item fl aliI-CE">
        <div class="thread-number-ini">#</div>
        <h2>${p.t}</h2>
        <div class="actions fl aliI-CE">
          ${tagsHtml}
          <span class="status-badge ${badgeCls}">${badgeTxt}</span>
        </div>
      </a>`;
    }).join('');
  });
})();
