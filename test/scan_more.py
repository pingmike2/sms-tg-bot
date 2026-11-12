#!/usr/bin/env python3
# 检查其余站点是否有免登录的号码页
import re, urllib.request, gzip

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return raw.decode("utf-8", "ignore")

def scan(name, urls):
    print(f"\n{'='*66}\n{name}")
    for u in urls:
        try:
            h = get(u)
            # 找电话号链接或电话号
            ph_links = set(re.findall(r'href="([^"]{0,80}?\d{9,13}[^"]{0,40})"', h))
            raw_nums = set(re.findall(r'\+?1\d{10}\b', h))
            print(f"  {u}\n    len={len(h)} 号码链接={len(ph_links)} 裸号={len(raw_nums)}")
            for x in list(ph_links)[:4]:
                print("      link:", x[:90])
            for x in list(raw_nums)[:3]:
                print("      num:", x)
        except Exception as e:
            print(f"  {u} -> ERR {str(e)[:70]}")

scan("jiemahao", [
    "https://jiemahao.com/",
    "https://jiemahao.com/usa",
    "https://jiemahao.com/api/sms",
])
scan("temp-number", [
    "https://temp-number.com/temporary-numbers/",
    "https://temp-number.com/numbers",
])
scan("onlinesim", [
    "https://onlinesim.io/en/free_numbers",
    "https://onlinesim.io/api/getFreePhoneList?country=7",
])
scan("smser", [
    "https://smser.net/",
    "https://smser.net/en/",
])
