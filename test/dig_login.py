#!/usr/bin/env python3
# 深入 mianfeijiema / lubansms：找号码页与读码接口
import re, urllib.request, gzip

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return raw.decode("utf-8", "ignore")

def plain(h):
    h = re.sub(r"<script.*?</script>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()

print("="*70)
print("mianfeijiema 号码链接形态")
h = get("https://www.mianfeijiema.com/")
links = set(re.findall(r'href="([^"]*(?:sms|number|phone|jiema)[^"]*)"', h, re.I))
for l in sorted(links)[:15]:
    print("  ", l)

# 号码节点
nodes = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>\s*[\+]?1\d{10}', h)
print("\n带号码的 a 标签:", nodes[:5])

# 找 ajax 接口
print("\n脚本里的接口:")
for m in re.findall(r'(?:url|action|api|ajax)\s*[:=]\s*["\']([^"\']{4,80})["\']', h, re.I):
    print("  ", m)

print("\n" + "="*70)
print("lubansms 号码链接")
h2 = get("https://lubansms.com/receiveSms")
links2 = set(re.findall(r'href="([^"]*(?:sms|receive|number)[^"]*)"', h2, re.I))
for l in sorted(links2)[:15]:
    print("  ", l)
phones2 = set(re.findall(r'1[13][0-9]{9}', h2))
print("号码:", list(phones2)[:5])
