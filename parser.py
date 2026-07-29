#!/usr/bin/env python3
"""Ahura Blog — Markdown Parser & Frontmatter"""

import os
import re
from datetime import datetime
from pathlib import Path
import markdown


def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(path, content):
    path = Path(path) if not isinstance(path, Path) else path
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✓ {path}")


def parse_frontmatter(content, filepath=None):
    """استخراج frontmatter (---...---) و body از Markdown.
    اگر فیلد date وجود نداشته باشد، از mtime فایل استفاده می‌کند.
    """
    meta = {
        'title': '',
        'date': None,  # filled with mtime fallback
        'category': 'عمومی',
        'status': 'done',
        'tags': [],
    }
    body = content

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_lines = parts[1].strip().split('\n')
            body = parts[2].strip()
            for line in fm_lines:
                if ':' in line:
                    key, val = line.split(':', 1)
                    key = key.strip().lower()
                    val = val.strip().strip('"').strip("'")
                    if key in ('title', 'category', 'status'):
                        meta[key] = val
                    elif key == 'date':
                        try:
                            meta['date'] = datetime.fromisoformat(val)
                        except ValueError:
                            pass
                    elif key == 'tags':
                        meta['tags'] = [t.strip() for t in val.split(',') if t.strip()]

    # Fallback: از mtime فایل به جای datetime.now()
    if meta['date'] is None:
        if filepath:
            mtime = os.path.getmtime(filepath)
            meta['date'] = datetime.fromtimestamp(mtime)
        else:
            meta['date'] = datetime.now()

    return meta, body


# ─── custom-box style callouts ────────────────────────────────────────

_BOX_DEFS = {
    'info':         ('info',        '📘 اطلاعات'),
    'warning':      ('warning',     '⚠️ هشدار'),
    'error':        ('error',       '❌ خطا'),
    'project':      ('project',     '📁 پروژه'),
    'exercise':     ('exercise',    '✏️ تمرین'),
    'bestpractice': ('bestPractice','💡 بهترین روش'),
}


def convert_custom_boxes(md_text):
    """تبدیل [info: ...] ... [/info] به HTML در مارکداون (قبل از پردازش)"""

    for tag, (css_class, default_title) in _BOX_DEFS.items():
        pattern = re.compile(
            rf'\[{tag}:?\s*(.*?)\]\s*\n?(.*?)\n?\s*\[/{tag}\]',
            re.DOTALL | re.IGNORECASE
        )

        def replacer(m, dt=default_title, cc=css_class):
            title = m.group(1).strip() or dt
            contents = m.group(2).strip()
            return (
                f'\n<details class="box {cc}" markdown="1">\n'
                f'<summary>{dt}: {title}</summary>\n'
                f'<div class="box-content" markdown="1">\n\n{contents}\n\n</div>\n'
                f'</details>\n'
            )

        md_text = pattern.sub(replacer, md_text)

    return md_text


def md_to_html(md_text):
    """تبدیل مارکداون به HTML با python-markdown"""
    extensions = [
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.tables',
        'markdown.extensions.nl2br',
        'markdown.extensions.smarty',
        'markdown.extensions.extra',
        'markdown.extensions.md_in_html',
    ]
    return markdown.markdown(md_text, extensions=extensions)
