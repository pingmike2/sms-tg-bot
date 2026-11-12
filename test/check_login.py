#!/usr/bin/env python3
# 逐个检查"需登录"类站点的真实登录要求
import re, urllib.request, gzip, json

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

SITES = {
    "smser":      "https://smser.net/",
    "onlinesim":  "https://onlinesim.io/en/free_numbers",
    "lubansms":   "https://lubansms.com/receiveSms",
    "jiemahao":   "https://jiemahao.com/",
    "tempnumber": "https://temp-number.com/",
    "mianfeijiema": "https://www.mianfeijiema.com/",
}

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return r.status, r.url, raw.decode("utf-8", "ignore")

def plain(h):
    h = re.sub(r"<script.*?</script>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()

for name, url in SITES.items():
    print(f"\n{'='*60}\n{name}  {url}")
    try:
        st, final, h = get(url)
        print(f"  HTTP {st}  len={len(h)}  final={final}")
        # 登录/注册相关线索
        has_login = bool(re.search(r'(sign\s*in|log\s*in|登录|注册|signup|sign_up|register)', h, re.I))
        print(f"  含登录/注册字样: {has_login}")
        # 表单？需要 email？
        forms = re.findall(r'<form[^>]*>', h, re.I)
        print(f"  form 标签: {len(forms)}")
        for f in forms[:3]:
            print("    ", f[:120])
        # 邮箱输入框
        emails = re.findall(r'<input[^>]*type=["\']email["\'][^>]*>', h, re.I)
        pwd = re.findall(r'<input[^>]*type=["\']password["\'][^>]*>', h, re.I)
        print(f"  email输入框: {len(emails)}  password输入框: {len(pwd)}")
        # 号码线索
        phones = set(re.findall(r'\+?1[0-9]{10}\b', h))
        print(f"  疑似号码数: {len(phones)} {list(phones)[:3]}")
        t = plain(h)[:200]
        print(f"  文本: {t}")
    except Exception as e:
        print(f"  ERR {type(e).__name__}: {str(e)[:100]}")
