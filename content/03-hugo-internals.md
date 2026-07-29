---
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

ادامه این پست در دست نوشتن است... ✍️