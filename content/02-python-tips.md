---
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

ادامه داره... 📝