#!/usr/bin/env python3
"""Ahura Blog — Template Helpers, Safe fill, RSS/Sitemap/Search generators"""

import re
import json
from datetime import datetime
from html import escape as html_escape


def tag_slug(tag):
    """تبدیل اسم تگ به slug URL-friendly"""
    slug = tag.strip().replace(' ', '-').replace('\u200c', '-')
    slug = re.sub(r'[^\w\-\u0600-\u06FF]', '', slug)
    return slug or 'untitled'


def render_tags_html(tags_list, base=''):
    """تبدیل لیست تگ‌ها به HTML badgeها با base prefix"""
    if not tags_list:
        return ''
    parts = []
    for tag in sorted(tags_list):
        slug = tag_slug(tag)
        parts.append(f'<a href="{base}/tags/{slug}/" class="tag-badge">{html_escape(tag)}</a>')
    return ''.join(parts)


def render_thread_item(post, idx, base='', with_tags=True):
    """ساخت thread-item یکسان برای لیست اصلی و صفحات تگ"""
    m = post['meta']
    tags_html = render_tags_html(m['tags'], base=base) if with_tags else ''
    return f'''
            <a href="{base}/threads/{html_escape(post['slug'])}/" class="thread-item fl aliI-CE">
                <div class="thread-number-ini">#{idx}</div>
                <h2>{html_escape(m['title'])}</h2>
                <div class="actions fl aliI-CE">
                    {tags_html}
                </div>
            </a>'''


def build_tag_index(posts):
    """ساخت ایندکس تگ‌ها: {tag_name: [post, ...]}"""
    index = {}
    for p in posts:
        for tag in p['meta']['tags']:
            index.setdefault(tag, []).append(p)
    return index


def fill(template, safe_keys=None, **kw):
    """جایگزینی {{ KEY }} با مقدار — با html.escape روی همه مقادیر متنی.
    safe_keys: مجموعه‌ای از keyها که RAW (بدون escape) جایگزین بشن.
    مثال: fill(tpl, safe_keys={'BODY','TAGS'}, TITLE="hello", BODY="<b>raw</b>")
    """
    safe = set(safe_keys or [])
    for k, v in kw.items():
        placeholder = '{{ ' + k + ' }}'
        if k in safe:
            template = template.replace(placeholder, str(v))
        elif isinstance(v, str):
            template = template.replace(placeholder, html_escape(v))
        else:
            template = template.replace(placeholder, str(v))
    return template


def generate_rss(posts, site_url):
    """ساخت فایل RSS 2.0 از پست‌ها"""
    items = ''
    for p in posts:
        m = p['meta']
        url = f"{site_url}/threads/{m['slug']}/"
        desc = re.sub(r'<[^>]+>', '', p['body'])
        desc = desc[:500]
        desc = html_escape(desc)
        items += f'''    <item>
      <title>{html_escape(m['title'])}</title>
      <link>{url}</link>
      <guid>{url}</guid>
      <pubDate>{m['date'].strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
      <category>{html_escape(m['category'])}</category>
      <description>{desc}</description>
    </item>
'''
    now = datetime.now()
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Ahura — وبلاگ شخصی</title>
    <link>{site_url}</link>
    <description>وبلاگ شخصی Ahura — برنامه‌نویسی، هوش مصنوعی، پروژه‌های شخصی</description>
    <language>fa</language>
    <lastBuildDate>{now.strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
    <atom:link href="{site_url}/rss.xml" rel="self" type="application/rss+xml"/>
{items}  </channel>
</rss>'''
    return rss


def generate_sitemap(posts, tag_index, site_url):
    """ساخت Sitemap.xml"""
    urls = [f'''  <url>
    <loc>{site_url}/</loc>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{site_url}/threads/</loc>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{site_url}/tags/</loc>
    <priority>0.7</priority>
  </url>
''']
    for p in posts:
        m = p['meta']
        urls.append(f'''  <url>
    <loc>{site_url}/threads/{m['slug']}/</loc>
    <lastmod>{m['date'].strftime('%Y-%m-%d')}</lastmod>
    <priority>0.6</priority>
  </url>
''')
    for tag_name in sorted(tag_index.keys()):
        slug = tag_slug(tag_name)
        urls.append(f'''  <url>
    <loc>{site_url}/tags/{slug}/</loc>
    <priority>0.5</priority>
  </url>
''')
    sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{"".join(urls)}</urlset>'''
    return sitemap


def generate_search_json(posts, base=''):
    """ساخت search.json برای جستجوی آفلاین"""
    data = []
    for p in posts:
        m = p['meta']
        clean_body = re.sub(r'<[^>]+>', '', p['body'])
        clean_body = clean_body[:2000]
        data.append({
            't': m['title'],
            'c': m['category'],
            'g': m['tags'],
            's': m['status'],
            'u': f"/threads/{m['slug']}/",  # بدون BASE — JS خودش اضافه می‌کند
            'b': clean_body,
        })
    return json.dumps(data, ensure_ascii=False, indent=2)
