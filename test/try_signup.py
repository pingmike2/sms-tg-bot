#!/usr/bin/env python3
# 1) 拿一个临时邮箱  2) 看 temp-number 注册表单要什么字段
import re, urllib.request, urllib.parse, json, gzip

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

def req(url, data=None, headers=None, timeout=30):
    h = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        h.update(headers)
    if data is not None:
        if isinstance(data, dict):
            data = urllib.parse.urlencode(data).encode()
            h["Content-Type"] = "application/x-www-form-urlencoded"
    r = urllib.request.Request(url, headers=h, data=data)
    with urllib.request.urlopen(r, timeout=timeout) as f:
        raw = f.read()
        if f.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return f.status, raw.decode("utf-8", "ignore")

print("=== 1) 临时邮箱：mail.tm ===")
try:
    st, body = req("https://api.mail.tm/domains")
    doms = json.loads(body)
    domain = doms["hydra:member"][0]["domain"]
    print("  可用域名:", domain)

    import random, string
    user = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    addr = f"{user}@{domain}"
    pw = "".join(random.choices(string.ascii_letters + string.digits, k=14))
    st, body = req("https://api.mail.tm/accounts", data={"address": addr, "password": pw})
    print("  注册邮箱:", st, addr)
    st, body = req("https://api.mail.tm/token", data={"address": addr, "password": pw})
    tok = json.loads(body).get("token", "")
    print("  拿到 token:", bool(tok), "len", len(tok))
    with open("/tmp/mailtm.json", "w") as f:
        json.dump({"address": addr, "password": pw, "token": tok}, f)
except Exception as e:
    print("  ERR:", str(e)[:150])

print("\n=== 2) temp-number 注册页字段 ===")
for u in ["https://temp-number.com/signup", "https://temp-number.com/register", "https://temp-number.com/sign-in"]:
    try:
        st, h = req(u)
        print(f"\n  {u} -> {st} len={len(h)}")
        for f in re.findall(r'<input[^>]*>', h)[:10]:
            if any(k in f.lower() for k in ["email", "password", "name", "text"]):
                nm = (re.search(r'name="([^"]+)"', f) or [None, "?"])[1]
                ty = (re.search(r'type="([^"]+)"', f) or [None, "?"])[1]
                print(f"      name={nm} type={ty}")
        for f in re.findall(r'<form[^>]*>', h)[:3]:
            print("      form:", f[:130])
    except Exception as e:
        print(f"  {u} -> ERR {str(e)[:80]}")
