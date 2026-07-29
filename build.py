#!/usr/bin/env python3
"""Ahura Blog — Build Engine: site generation logic"""

import logging
import re
import shutil
from datetime import datetime
from pathlib import Path

from parser import read_file, write_file, parse_frontmatter, convert_custom_boxes, md_to_html, add_lazy_loading
from templating import (
    tag_slug, render_tags_html, render_thread_item, build_tag_index,
    fill, generate_rss, generate_sitemap, generate_search_json,
)

# ─── logging ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(message)s",
)
log = logging.getLogger("ahura")

# ─── paths ─────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATE_DIR = BASE_DIR / "template"
ASSETS_DIR = BASE_DIR / "assets"

# ─── site config ───────────────────────────────────────────────────────

SITE_URL = "https://kuoroshhj.github.io/ahura-blog"
BASE = "/ahura-blog"  # برای GitHub Pages subpath

# ترتیب دلخواه دسته‌بندی‌ها (تغییر بده به سلیقه خودت)
CATEGORY_ORDER = ["عمومی", "برنامه‌نویسی", "تکنولوژی", "شخصی"]


def get_description(body_html):
    """استخراج توضیحات (حدود ۱۶۰ کاراکتر) از HTML بدن پست — بدون newline"""
    clean = re.sub(r'<[^>]+>', '', body_html).strip()
    clean = ' '.join(clean.split())  # collapse whitespace
    return clean[:160].rsplit(' ', 1)[0] if len(clean) > 160 else clean


# ─── helpers ───────────────────────────────────────────────────────────

def copy_assets():
    for item in ASSETS_DIR.rglob('*'):
        if item.is_file():
            rel = item.relative_to(ASSETS_DIR)
            dest = OUTPUT_DIR / "assets" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)


def load_templates():
    return {
        'svgs': read_file(TEMPLATE_DIR / "svgs.html"),
        'base': read_file(TEMPLATE_DIR / "base.html"),
        'home': read_file(TEMPLATE_DIR / "home.html"),
        'list': read_file(TEMPLATE_DIR / "thread-list-body.html"),
        'detail': read_file(TEMPLATE_DIR / "thread-detail-body.html"),
        'tags': read_file(TEMPLATE_DIR / "tags-body.html"),
        'tag_detail': read_file(TEMPLATE_DIR / "tag-detail-body.html"),
        'search': read_file(TEMPLATE_DIR / "search-body.html"),
    }


# ─── embedded templates (fallback) ─────────────────────────────────────

def ensure_templates():
    t = TEMPLATE_DIR
    if not (t / "svgs.html").exists():
        write_file(t / "svgs.html", '''<svg style="display:none">
  <symbol id="_DOTS_ICON" viewBox="0 0 34.77 35" fill="none"><g transform="matrix(0 1 -1 0 34.77 0)"><path d="M0 1.95741C0 .877402.87685.0 1.95455.0 3.03236.0 3.91083.877402 3.91083 1.95741c0 1.08001-.87847 1.95741-1.95628 1.95741C.87685 3.91482.0 3.03742.0 1.95741z" fill="currentColor" stroke-width="2" stroke="currentColor" transform="translate(15.545 7.515)"/><path d="M0 1.95542C0 .876525.87685.0 1.95455.0 3.03236.0 3.91083.876525 3.91083 1.95542c0 1.07889-.87847 1.95541-1.95628 1.95541C.87685 3.91083.0 3.03431.0 1.95542z" fill="currentColor" stroke-width="2" stroke="currentColor" transform="translate(15.545 15.43)"/><path d="M0 1.95737C0 .877392.876849.0 1.95455.0 3.03236.0 3.91083.877392 3.91083 1.95737c0 1.08008-.87847 1.95747-1.95628 1.95747C.876849 3.91484.0 3.03745.0 1.95737z" fill="currentColor" stroke-width="2" stroke="currentColor" transform="translate(15.545 23.34)"/></g></symbol>
  <symbol id="_SHARE_ICON" viewBox="0 0 512 512"><path fill="currentColor" d="M432 96a48 48 0 10-96 0 48 48 0 1096 0zm48 0c0 53-43 96-96 96-27.4.0-52.1-11.5-69.6-29.9L188.9 231.8c2 7.7 3.1 15.8 3.1 24.2s-1.1 16.5-3.1 24.2l125.5 69.7c17.5-18.4 42.2-29.9 69.6-29.9 53 0 96 43 96 96s-43 96-96 96-96-43-96-96c0-8.3 1.1-16.5 3.1-24.2L165.6 322.1C148.1 340.5 123.4 352 96 352c-53 0-96-43-96-96s43-96 96-96c27.4.0 52.1 11.5 69.6 29.9l125.5-69.7c-2-7.7-3.1-15.8-3.1-24.2.0-53 43-96 96-96s96 43 96 96zM144 256a48 48 0 10-96 0 48 48 0 1096 0zM384 464a48 48 0 100-96 48 48 0 100 96z"/></symbol>
  <symbol id="_BACK_ICON" viewBox="0 0 512 512"><path fill="currentColor" d="M48 256c0 114.9 93.1 208 208 208 13.3.0 24 10.7 24 24s-10.7 24-24 24C114.6 512 0 397.4.0 256S114.6.0 256 0c13.3.0 24 10.7 24 24s-10.7 24-24 24C141.1 48 48 141.1 48 256zM271 377 167 273c-9.4-9.4-9.4-24.6.0-33.9L271 135c9.4-9.4 24.6-9.4 33.9.0s9.4 24.6.0 33.9l-63 63H488c13.3.0 24 10.7 24 24s-10.7 24-24 24H241.9l63 63c9.4 9.4 9.4 24.6.0 33.9s-24.6 9.4-33.9.0z"/></symbol>
  <symbol id="_LICENSE_ICON" viewBox="0 0 640 512"><path fill="currentColor" d="M520 48H393.3C381 19.7 352.8.0 320 0s-61 19.7-73.3 48H120c-13.3.0-24 10.7-24 24s10.7 24 24 24h121.6c5.8 28.6 26.9 51.7 54.4 60.3V464H120c-13.3.0-24 10.7-24 24s10.7 24 24 24h4e2c13.3.0 24-10.7 24-24s-10.7-24-24-24H344V156.3c27.5-8.6 48.6-31.7 54.4-60.3L520 96c13.3.0 24-10.7 24-24s-10.7-24-24-24zm-8 147.8L584.4 320H439.6L512 195.8zM386 337.1C396.8 382 449.1 416 512 416s115.2-34 126-78.9c2.6-11-1-22.3-6.7-32.1L536.1 141.8c-5-8.6-14.2-13.8-24.1-13.8s-19.1 5.3-24.1 13.8L392.7 305.1c-5.7 9.8-9.3 21.1-6.7 32.1zM54.4 320l72.4-124.2L199.2 320H54.3zm72.4 96c62.9.0 115.2-34 126-78.9 2.6-11-1-22.3-6.7-32.1L150.9 141.8c-5-8.6-14.2-13.8-24.1-13.8s-19.1 5.3-24.1 13.8L7.6 305.1C1.9 314.8-1.8 326.1.9 337.1 11.7 382 64 416 126.8 416zM320 48a32 32 0 110 64 32 32 0 110-64z"/></symbol>
  <symbol id="_VIDEO_ICON" viewBox="0 0 576 512"><path fill="currentColor" d="M352 112c8.8.0 16 7.2 16 16v256c0 8.8-7.2 16-16 16H96c-8.8.0-16-7.2-16-16V128c0-8.8 7.2-16 16-16h256zM96 64c-35.3.0-64 28.7-64 64v256c0 35.3 28.7 64 64 64h256c35.3.0 64-28.7 64-64V128c0-35.3-28.7-64-64-64H96zM464 172v60l64-48v144l-64-48v60l73.6 55.2c4.2 3.1 9.2 4.8 14.4 4.8 13.3.0 24-10.7 24-24V136c0-13.3-10.7-24-24-24-5.2.0-10.2 1.7-14.4 4.8L464 172zM224 184c16.1.0 29.2 13.1 29.2 29.2.0 8.7-3.1 13.9-6.9 17.7-4.5 4.4-10.7 7.5-16.8 9.5-14.9 5-29.5 19.3-29.5 39.5.0 13.3 10.7 24 24 24 11.5.0 21.2-8.1 23.5-19 19.2-7.1 53.7-26.3 53.7-71.8.0-42.6-34.6-77.2-77.2-77.2s-77.2 34.6-77.2 77.2c0 13.3 10.7 24 24 24s24-10.7 24-24c0-16.1 13.1-29.2 29.2-29.2zm28 168a28 28 0 10-56 0 28 28 0 1056 0z"/></symbol>
  <symbol id="_MOON_ICON" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></symbol>
  <symbol id="_SUN_ICON" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></symbol>
  <symbol id="_GITHUB_ICON" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.374.0.0 5.373.0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931.0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176.0.0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221.0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></symbol>
  <symbol id="_EDIT_ICON" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4A2 2 0 002 6v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121.0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></symbol>
  <symbol id="_TAG_ICON" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83.0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></symbol>
</svg>''')
        log.info("📝  svgs ساخته شد!")

    if not (t / "base.html").exists():
        write_file(t / "base.html", '''<!doctype html>
<html lang="fa" dir="rtl" data-theme="dark">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{{ TITLE }}</title>
<link rel="stylesheet" href="{{ BASE }}/assets/css/structure.css" />
<link rel="stylesheet" href="{{ BASE }}/assets/css/style.css" />
<link rel="stylesheet" href="{{ BASE }}/assets/css/threads.css" />
<link rel="alternate" type="application/rss+xml" title="Ahura — RSS Feed" href="{{ BASE }}/rss.xml" />
<link rel="sitemap" type="application/xml" title="Sitemap" href="{{ BASE }}/sitemap.xml" />
</head>
<body class="theme-dark">
{{ SVGS }}

<header class="flW aliI-CE jusCo-SP wrp">
  <a href="{{ BASE }}/" class="c-box aliI-CE">
    <div class="svg-cont" style="background:#e94560;border-color:#e94560"><svg style="color:#fff"><use href="#_EDIT_ICON"/></svg></div>
    <p style="font-weight:700;margin-right:8px;color:var(--c-text-main);font-size:16px">Ahura</p>
  </a>
  <div class="fl aliI-CE" style="gap:8px">
    <a href="{{ BASE }}/threads/" class="c-box aliI-CE" data-tooltip-text="همه نوشته‌ها">
      <div class="svg-cont"><svg><use href="#_DOTS_ICON"/></svg></div>
    </a>
    <a href="{{ BASE }}/tags/" class="c-box aliI-CE" data-tooltip-text="برچسب‌ها">
      <div class="svg-cont"><svg><use href="#_TAG_ICON"/></svg></div>
    </a>
    <a href="{{ BASE }}/search/" class="c-box aliI-CE" data-tooltip-text="جستجو">
      <div class="svg-cont"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></div>
    </a>
    <button onclick="toggleTheme()" class="c-box aliI-CE dark-toggle" data-tooltip-text="تغییر تم" aria-label="تغییر تم دارک/لایت" style="border:none;background:none;cursor:pointer">
      <div class="svg-cont">
        <svg id="theme-icon" style="width:22px;height:22px"><use href="#_MOON_ICON"/></svg>
      </div>
    </button>
  </div>
</header>

<main>
{{ CONTENT }}
</main>

<footer class="txt-C wrp">
  <p style="font-size:13px">© {{ YEAR }} <a href="{{ BASE }}/" style="color:#e94560">Ahura</a> — ساخته شده با ❤️ و بدون فریم‌ورک</p>
</footer>

<script src="{{ BASE }}/assets/js/modal.js"></script>
<script src="{{ BASE }}/assets/js/isread.js"></script>
<script src="{{ BASE }}/assets/js/search.js"></script>
<script>
function toggleTheme() {
  const body = document.body;
  const html = document.documentElement;
  const icon = document.querySelector('#theme-icon use');
  if (body.classList.contains('theme-dark')) {
    body.classList.remove('theme-dark');
    html.setAttribute('data-theme', 'light');
    icon.setAttribute('href', '#_MOON_ICON');
    localStorage.setItem('theme', 'light');
  } else {
    body.classList.add('theme-dark');
    html.setAttribute('data-theme', 'dark');
    icon.setAttribute('href', '#_SUN_ICON');
    localStorage.setItem('theme', 'dark');
  }
}
(function() {
  const saved = localStorage.getItem('theme');
  const body = document.body;
  const html = document.documentElement;
  const icon = document.querySelector('#theme-icon use');
  if (!icon) return;
  if (saved === 'light') {
    body.classList.remove('theme-dark');
    html.setAttribute('data-theme', 'light');
    icon.setAttribute('href', '#_MOON_ICON');
  } else {
    body.classList.add('theme-dark');
    html.setAttribute('data-theme', 'dark');
    icon.setAttribute('href', '#_SUN_ICON');
  }
})();
</script>
</body>
</html>''')

        write_file(t / "home.html", '''<section class="banner">
  <div class="wrapper fl aliI-CE jusCo-CE" style="min-height:60vh;gap:20px">
    <h1 class="logo-txt" style="font-size:48px;font-weight:900">Hello, World! 👋</h1>
    <p class="hero-text" style="font-size:16px;line-height:2;max-width:500px">
      من <strong>Ahura</strong> هستم. اینجا وبلاگ شخصیمه — جایی که می‌نویسم درباره<br/>
      <strong>برنامه‌نویسی</strong> • <strong>هوش مصنوعی</strong> • <strong>پروژه‌های شخصی</strong> • <strong>چیزایی که یاد می‌گیرم</strong>
    </p>
    <div class="social-links">
      <a href="{{ BASE }}/threads/">📝 دیدن نوشته‌ها</a>
      <a href="{{ BASE }}/tags/">🏷️ برچسب‌ها</a>
      <a href="https://github.com/kuoroshhj" target="_blank" rel="noopener"><svg width="16" height="16"><use href="#_GITHUB_ICON"/></svg> GitHub</a>
    </div>
    <p style="color:var(--c-text-icon);font-size:13px;margin-top:20px">
      تا الان {{ POST_COUNT }} تا پست نوشتم 🎯
    </p>
  </div>
</section>''')

        write_file(t / "thread-list-body.html", '''<div class="wrp">
<h1 style="margin-bottom:5px;font-size:24px;color:var(--c-text-main)">📝 همه نوشته‌ها</h1>
<p style="color:var(--c-text-icon);font-size:13px;margin-bottom:25px">{{ NOW }} — مرتب شده بر اساس تاریخ</p>

{{ CATEGORIES }}

<div style="text-align:center;margin-top:20px;padding:10px">
  <a href="{{ BASE }}/" style="font-size:13px;color:var(--c-text-link)">← برگشت به صفحه اصلی</a>
</div>
</div>''')

        write_file(t / "thread-detail-body.html", '''<div class="wrp">
<div class="breadcrumb">
  <ul class="breadcrumb-list">
    <li class="breadcrumb-item"><a href="{{ BASE }}/" class="breadcrumb-link">خانه</a></li>
    <li class="breadcrumb-item"><span class="breadcrumb-separator">←</span></li>
    <li class="breadcrumb-item"><a href="{{ BASE }}/threads/" class="breadcrumb-link">نوشته‌ها</a></li>
    <li class="breadcrumb-item"><span class="breadcrumb-separator">←</span></li>
    <li class="breadcrumb-item"><span class="breadcrumb-current">{{ TITLE }}</span></li>
  </ul>
</div>

<div class="section-status">
  <span class="section-status-text">{{ DATE }} — {{ CATEGORY }}</span>
  {{ STATUS_BADGE }}
</div>

<div class="thread-detail">
  <div class="h fl aliI-CE jusCo-SP">
    <h1 style="font-size:20px;margin:0">{{ TITLE }}</h1>
    <div class="svg-cont" style="border:none;background:transparent"><svg style="width:20px;height:20px"><use href="#_DOTS_ICON"/></svg></div>
  </div>
  <div class="tags-row">{{ TAGS }}</div>
  <div class="content mdm" style="padding:25px 20px;line-height:2">
    {{ BODY }}
  </div>
  <div class="h f fl aliI-CE jusCo-SP" style="gap:15px">
    <div class="fl aliI-CE" style="gap:10px">
      {{ PREV_LINK }}
      {{ NEXT_LINK }}
    </div>
    <a href="{{ BASE }}/threads/" class="c-box aliI-CE" data-tooltip-text="همه نوشته‌ها">
      <div class="svg-cont"><svg><use href="#_DOTS_ICON"/></svg></div>
    </a>
  </div>
</div>

<div class="giscus-section">
  <p style="font-size:13px;color:var(--c-text-icon);text-align:center">📬 نظرت رو برام بنویس — بیا توی گیت‌هاب!</p>
</div>
</div>''')

        write_file(t / "tags-body.html", '''<div class="wrp">
<h1 style="margin-bottom:5px;font-size:24px;color:var(--c-text-main)">🏷️ برچسب‌ها</h1>
<p style="color:var(--c-text-icon);font-size:13px;margin-bottom:25px">همه برچسب‌های استفاده شده در وبلاگ</p>

<div class="tags-cloud">
{{ TAGS }}
</div>

<div style="text-align:center;margin-top:20px;padding:10px">
  <a href="{{ BASE }}/" style="font-size:13px;color:var(--c-text-link)">← برگشت به صفحه اصلی</a>
</div>
</div>''')

        write_file(t / "tag-detail-body.html", '''<div class="wrp">

<div class="breadcrumb">
  <ul class="breadcrumb-list">
    <li class="breadcrumb-item"><a href="{{ BASE }}/" class="breadcrumb-link">خانه</a></li>
    <li class="breadcrumb-item"><span class="breadcrumb-separator">←</span></li>
    <li class="breadcrumb-item"><a href="{{ BASE }}/tags/" class="breadcrumb-link">برچسب‌ها</a></li>
    <li class="breadcrumb-item"><span class="breadcrumb-separator">←</span></li>
    <li class="breadcrumb-item"><span class="breadcrumb-current">#{{ TAG_NAME }}</span></li>
  </ul>
</div>

<h1 style="margin-bottom:5px;font-size:24px;color:var(--c-text-main)">🏷️ #{{ TAG_NAME }}</h1>
<p style="color:var(--c-text-icon);font-size:13px;margin-bottom:25px">{{ POST_COUNT }} پست با این برچسب</p>

{{ TAG_POSTS }}

<div style="text-align:center;margin-top:20px;padding:10px">
  <a href="{{ BASE }}/tags/" style="font-size:13px;color:var(--c-text-link)">← همه برچسب‌ها</a>
</div>
</div>''')

        write_file(t / "search-body.html", '''<div class="wrp">

<div class="breadcrumb">
  <ul class="breadcrumb-list">
    <li class="breadcrumb-item"><a href="{{ BASE }}/" class="breadcrumb-link">خانه</a></li>
    <li class="breadcrumb-item"><span class="breadcrumb-separator">←</span></li>
    <li class="breadcrumb-item"><span class="breadcrumb-current">جستجو</span></li>
  </ul>
</div>

<h1 style="margin-bottom:5px;font-size:24px;color:var(--c-text-main)">🔍 جستجو</h1>
<p style="color:var(--c-text-icon);font-size:13px;margin-bottom:25px" id="search-status">در حال بارگذاری...</p>

<div class="search-container">
  <input type="text" id="search-input" class="search-input" placeholder="در حال بارگذاری..." disabled autofocus />
  <div id="search-results" class="search-results"></div>
</div>

<div style="text-align:center;margin-top:20px;padding:10px">
  <a href="{{ BASE }}/" style="font-size:13px;color:var(--c-text-link)">← برگشت به صفحه اصلی</a>
</div>
</div>''')

        log.info("📝  تمپلیت‌های پیش‌فرض ایجاد شدند!")


# ─── sample posts ──────────────────────────────────────────────────────

def _create_samples():
    samples = [
        {
            'file': '01-salam.md',
            'content': '''---
title: "سلام دنیا! 👋"
date: 2026-07-29
category: "عمومی"
status: "done"
tags: "شروع, شخصی, وبلاگ"
---

## خوش اومدی به وبلاگ من! 🎉

این اولین پست منه. اینجا می‌نویسم درباره:

- برنامه‌نویسی و تکنولوژی
- هوش مصنوعی و عامل‌های هوشمند
- پروژه‌های شخصی
- هر چیزی که یاد می‌گیرم

[info: یه نکته]
این وبلاگ با یه ژنراتور استاتیک شخصی ساخته شده که خودم نوشتمش!
[/info]

## چرا این وبلاگ؟

چون به نظرم:

> سادگی نهایت پیچیدگی است.

واسه همین این وبلاگ:

- بدون هیچ فریم‌ورکی
- فقط HTML + CSS + Vanilla JS
- با قابلیت دارک/لایت مود
- و تمرکز روی محتوا

[bestpractice: بهترین روش]
همیشه ساده شروع کن و بعداً اضافه کن!
[/bestpractice]

خب بیایم بریم سراغ پست بعدی! 🚀'''
        },
        {
            'file': '02-python-tips.md',
            'content': '''---
title: "نکات Python که باید بدونی"
date: 2026-07-28
category: "برنامه‌نویسی"
status: "done"
tags: "پایتون, برنامه‌نویسی, نکات"
---

## نکات کاربردی Python 🐍

### 1. استفاده از f-strings

به جای:

```python
name = "Ahura"
print("Hello, " + name + "!")
```

بنویس:

```python
name = "Ahura"
print(f"Hello, {name}!")
```

### 2. List Comprehension

```python
# به جای:
squares = []
for x in range(10):
    squares.append(x ** 2)

# بنویس:
squares = [x ** 2 for x in range(10)]
```

[warning: توجه]
از list comprehension زیاد استفاده نکن — اگه پیچیده شد، readability رو ببر بالا!
[/warning]

### 3. zip برای دو لیست هم‌زمان

```python
names = ["Ali", "Sara", "Reza"]
scores = [85, 92, 78]
for name, score in zip(names, scores):
    print(f"{name}: {score}")
```

ادامه داره... 📝'''
        },
        {
            'file': '03-hugo-internals.md',
            'content': '''---
title: "داخل موتور Hugo: چطور یه تم دست‌ساز بسازیم"
date: 2026-07-27
category: "تکنولوژی"
status: "running"
tags: "Hugo, SSG, تکنولوژی, وب"
---

## Hugo Static Site Generator 🦜

Hugo یه SSG فوق‌العاده سریع به زبان Go هست.

### چرا Hugo؟

✅ سرعت بالا
✅ بدون dependency (یه باینری)
✅ تمپلیت قدرتمند
✅ پشتیبانی عالی از Markdown

[exercise: تمرین]
سعی کن یه تم Hugo از صفر با CSS دست‌نویس بسازی!
[/exercise]

### ساختار تمپلیت

```go
{{ define "main" }}
<article>
  <h1>{{ .Title }}</h1>
  {{ .Content }}
</article>
{{ end }}
```

[info: نکته فنی]
در Hugo نسخه 0.164.0 از defer در partialها پشتیبانی میشه
[/info]

ادامه این پست در دست نوشتن است... ✍️'''
        },
        {
            'file': '04-goals.md',
            'content': '''---
title: "هدف‌های من برای ۲۰۲۶"
date: 2026-07-26
category: "شخصی"
status: "done"
tags: "هدف, شخصی, ۲۰۲۶"
---

## هدف‌های امسال 🎯

### 💪 سلامت

- [x] ورزش منظم (حداقل ۳ روز در هفته)
- [ ] خواب کافی
- [ ] تغذیه سالم

### 📚 یادگیری

- [x] گذروندن CS50
- [ ] ساختن یه Agent-AI از صفر
- [ ] شرکت در مسابقه کدنویسی

[project: Agent-AI]
می‌خوام یه ویدیوی آموزشی درباره Agent-AI بسازم که توضیح بدم چطور کار می‌کنه.
[/project]

### 🚀 پروژه‌ها

- [x] ساخت این وبلاگ
- [ ] انتشار یه ابزار CLI

> "تنها محدودیت، خودت هستی" 💪'''
        },
    ]

    for s in samples:
        fp = CONTENT_DIR / s['file']
        fp.parent.mkdir(parents=True, exist_ok=True)
        write_file(fp, s['content'])
    log.info("   %d پست نمونه ساخته شد!", len(samples))


# ─── main build ────────────────────────────────────────────────────────

def build_site():
    log.info("Ahura Blog Generator — v3 (ماژولار + BASE_URL)")
    log.info("=" * 50)

    # Ensure templates exist
    ensure_templates()
    tpl = load_templates()
    now = datetime.now()
    year_str = now.strftime('%Y')
    now_str = now.strftime('%Y-%m-%d %H:%M')

    # ── read posts ────────────────────────────────────────────────
    posts = []
    files = sorted(CONTENT_DIR.rglob('*.md'))
    if not files:
        log.info("ℹ️  هیچ پستی نیست → می‌سازمشون ...")
        _create_samples()
        files = sorted(CONTENT_DIR.rglob('*.md'))

    for f in files:
        slug = f.relative_to(CONTENT_DIR).with_suffix('').as_posix().replace('/', '-')
        log.info("📄  %s → slug: %s", f.relative_to(CONTENT_DIR), slug)
        raw = read_file(f)
        try:
            meta, body = parse_frontmatter(raw, filepath=str(f))
        except Exception as exc:
            log.warning("⚠️  %s — frontmatter خراب: %s. رد شد.", f.relative_to(CONTENT_DIR), exc)
            continue
        try:
            body_html = convert_custom_boxes(body)
            body_html = md_to_html(body_html)
            body_html = add_lazy_loading(body_html)
        except Exception as exc:
            log.warning("⚠️  %s — خطا در تبدیل: %s. رد شد.", f.relative_to(CONTENT_DIR), exc)
            continue
        meta['slug'] = slug
        posts.append(dict(meta=meta, body=body_html, slug=slug))

    posts.sort(key=lambda p: p['meta']['date'], reverse=True)

    # ── group by category ─────────────────────────────────────────
    groups = {}
    for p in posts:
        cat = p['meta']['category']
        groups.setdefault(cat, []).append(p)

    # ── clean output ──────────────────────────────────────────────
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    # Safe keys for fill() — HTML content that must NOT be escaped
    RAW = {'SVGS', 'CONTENT', 'BASE', 'CATEGORIES', 'STATUS_BADGE',
           'TAGS', 'BODY', 'PREV_LINK', 'NEXT_LINK', 'TAG_POSTS', 'DESC', 'OG_URL'}

    # ── sort by category order ────────────────────────────────────
    sorted_cats = sorted(
        groups.keys(),
        key=lambda c: (CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 999, c)
    )

    # ── build thread-list body ────────────────────────────────────
    list_items = ''
    for cat_name in sorted_cats:
        cat_posts = groups[cat_name]
        items = ''
        for idx, p in enumerate(cat_posts, 1):
            items += render_thread_item(p, idx, base=BASE, with_tags=True)
        list_items += f'''
        <div class="thread-group">
            <div class="h fl aliI-CE jusCo-SP">
                <h3>{cat_name}</h3>
                <div class="svg-cont"><svg><use href="#_DOTS_ICON"/></svg></div>
            </div>
            {items}
        </div>'''

    if not list_items:
        list_items = '''
        <div class="thread-group">
            <div class="h fl aliI-CE jusCo-SP">
                <h3>خوش آمدی!</h3>
                <div class="svg-cont"><svg><use href="#_DOTS_ICON"/></svg></div>
            </div>
            <div class="ph"><p class="x">هنوز پستی ننوشتی. برو content/ یه فایل .md بساز!</p></div>
        </div>'''

    list_body = fill(tpl['list'], safe_keys=RAW,
                     BASE=BASE, CATEGORIES=list_items, NOW=now_str)

    # ── build home page ───────────────────────────────────────────
    home_body = fill(tpl['home'], safe_keys=RAW,
                     BASE=BASE, POST_COUNT=str(len(posts)))

    # ── build detail pages ────────────────────────────────────────
    for i, p in enumerate(posts):
        m = p['meta']
        desc_text = get_description(p['body'])
        og_url = f"{SITE_URL}/threads/{p['slug']}/"
        status_cls = 'done' if m['status'] == 'done' else 'running'
        status_txt = '✅ انجام شده' if m['status'] == 'done' else '⏳ در حال انجام'
        tags_html = render_tags_html(m['tags'], base=BASE)

        prev_link = ''
        next_link = ''
        if i < len(posts) - 1:
            prev = posts[i + 1]
            prev_link = (f'<a href="../{prev["slug"]}/" class="c-box aliI-CE" '
                         f'data-tooltip-text="{prev["meta"]["title"]}">'
                         '<div class="svg-cont" style="transform:rotate(180deg)">'
                         '<svg><use href="#_BACK_ICON"/></svg></div></a>')
        if i > 0:
            nxt = posts[i - 1]
            next_link = (f'<a href="../{nxt["slug"]}/" class="c-box aliI-CE" '
                         f'data-tooltip-text="{nxt["meta"]["title"]}">'
                         '<div class="svg-cont">'
                         '<svg><use href="#_BACK_ICON"/></svg></div></a>')

        detail_body = fill(tpl['detail'], safe_keys=RAW,
            BASE=BASE,
            TITLE=m['title'],
            BODY=p['body'],
            STATUS_BADGE=f'<span class="status-badge status-{status_cls}">{status_txt}</span>',
            DATE=m['date'].strftime('%Y-%m-%d'),
            CATEGORY=m['category'],
            TAGS=tags_html,
            PREV_LINK=prev_link,
            NEXT_LINK=next_link,
        )

        full = fill(tpl['base'], safe_keys=RAW,
            BASE=BASE,
            SVGS=tpl['svgs'],
            TITLE=f"{m['title']} — Ahura",
            DESC=desc_text,
            OG_URL=og_url,
            CONTENT=detail_body,
            YEAR=year_str,
        )
        out = OUTPUT_DIR / "threads" / p['slug'] / "index.html"
        write_file(out, full)

    # ── write index ───────────────────────────────────────────────
    write_file(OUTPUT_DIR / "index.html", fill(tpl['base'], safe_keys=RAW,
        BASE=BASE,
        SVGS=tpl['svgs'],
        TITLE="Ahura — وبلاگ شخصی",
        DESC="وبلاگ شخصی Ahura — برنامه‌نویسی، هوش مصنوعی و پروژه‌های شخصی",
        OG_URL=SITE_URL,
        CONTENT=home_body,
        YEAR=year_str,
    ))

    # ── write threads listing ─────────────────────────────────────
    write_file(OUTPUT_DIR / "threads" / "index.html", fill(tpl['base'], safe_keys=RAW,
        BASE=BASE,
        SVGS=tpl['svgs'],
        TITLE="نوشته‌ها — Ahura",
        DESC="همه نوشته‌های وبلاگ Ahura مرتب شده بر اساس دسته‌بندی",
        OG_URL=f"{SITE_URL}/threads/",
        CONTENT=list_body,
        YEAR=year_str,
    ))

    # ── build tag pages ───────────────────────────────────────────
    tag_index = build_tag_index(posts)

    # Tag index page
    tag_list_html = ''
    for tag_name in sorted(tag_index.keys()):
        count = len(tag_index[tag_name])
        slug = tag_slug(tag_name)
        tag_list_html += f'''
        <a href="{BASE}/tags/{slug}/" class="tag-card">
            <span class="tag-card-name">{tag_name}</span>
            <span class="tag-card-count">{count} پست</span>
        </a>'''

    if tag_list_html:
        tags_body = fill(tpl['tags'], safe_keys=RAW, BASE=BASE, TAGS=tag_list_html)
        write_file(OUTPUT_DIR / "tags" / "index.html", fill(tpl['base'], safe_keys=RAW,
            BASE=BASE,
            SVGS=tpl['svgs'],
            TITLE="برچسب‌ها — Ahura",
            DESC="همه برچسب‌های استفاده شده در وبلاگ Ahura",
            OG_URL=f"{SITE_URL}/tags/",
            CONTENT=tags_body,
            YEAR=year_str,
        ))

    for tag_name, tag_posts in tag_index.items():
        slug = tag_slug(tag_name)
        items = ''
        for idx, p in enumerate(tag_posts, 1):
            items += render_thread_item(p, idx, base=BASE, with_tags=False)

        tag_detail_body = fill(tpl['tag_detail'], safe_keys=RAW,
            BASE=BASE,
            TAG_NAME=tag_name,
            TAG_POSTS=items,
            POST_COUNT=str(len(tag_posts)),
        )
        write_file(OUTPUT_DIR / "tags" / slug / "index.html", fill(tpl['base'], safe_keys=RAW,
            BASE=BASE,
            SVGS=tpl['svgs'],
            TITLE=f"#{tag_name} — Ahura",
            DESC=f"پست‌های برچسب #{tag_name} در وبلاگ Ahura",
            OG_URL=f"{SITE_URL}/tags/{slug}/",
            CONTENT=tag_detail_body,
            YEAR=year_str,
        ))

    # ── RSS ──────────────────────────────────────────────────────
    log.info("📡  تولید RSS Feed …")
    write_file(OUTPUT_DIR / "rss.xml", generate_rss(posts, SITE_URL))
    log.info("   → output/rss.xml")

    # ── Sitemap ──────────────────────────────────────────────────
    log.info("🗺️  تولید Sitemap.xml …")
    write_file(OUTPUT_DIR / "sitemap.xml", generate_sitemap(posts, tag_index, SITE_URL))
    write_file(OUTPUT_DIR / "robots.txt",
               "User-agent: *\nAllow: /\nSitemap: " + SITE_URL + "/sitemap.xml\n")

    # ── Search JSON ──────────────────────────────────────────────
    log.info("🔍  تولید search.json …")
    write_file(OUTPUT_DIR / "search.json", generate_search_json(posts, base=BASE))

    # ── Search Page ──────────────────────────────────────────────
    search_body = fill(tpl['search'], safe_keys=RAW, BASE=BASE)
    write_file(OUTPUT_DIR / "search" / "index.html", fill(tpl['base'], safe_keys=RAW,
        BASE=BASE,
        SVGS=tpl['svgs'],
        TITLE="جستجو — Ahura",
        DESC="جستجوی نوشته‌های وبلاگ Ahura",
        OG_URL=f"{SITE_URL}/search/",
        CONTENT=search_body,
        YEAR=year_str,
    ))

    # ── copy assets ──────────────────────────────────────────────
    log.info("📦  کپی assets …")
    copy_assets()

    log.info("✨  خروجی در: %s  (%d پست — %d تگ)", OUTPUT_DIR, len(posts), len(tag_index))
    log.info("   index      → %s", OUTPUT_DIR / 'index.html')
    log.info("   threads    → %s", OUTPUT_DIR / 'threads' / 'index.html')
    log.info("   tags       → %s", OUTPUT_DIR / 'tags' / 'index.html')
    log.info("   search     → %s", OUTPUT_DIR / 'search' / 'index.html')
    log.info("   rss        → %s", OUTPUT_DIR / 'rss.xml')
    log.info("   sitemap    → %s", OUTPUT_DIR / 'sitemap.xml')
    log.info("   search.json→ %s", OUTPUT_DIR / 'search.json')
    for p in posts:
        tags_str = ', '.join(p['meta']['tags']) if p['meta']['tags'] else 'بدون تگ'
        log.info("   %s [%s]", p['meta']['title'], tags_str)
    for tag_name in sorted(tag_index.keys()):
        slug = tag_slug(tag_name)
        log.info("   تگ #%s → %s/tags/%s/", tag_name, BASE, slug)
