#!/usr/bin/env python3
# 用临时邮箱注册 temp-number.com
import re, urllib.request, urllib.parse, json, gzip, http.cookiejar

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

mb = json.load(open("/tmp/mailtm.json"))
EMAIL = mb["address"]
PASSWORD = "TempNumber2026!"

def go(url, data=None, timeout=40, extra=None):
    h = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    if extra:
        h.update(extra)
    body = None
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        h["Content-Type"] = "application/x-www-form-urlencoded"
        h["Referer"] = "https://temp-number.com/sign-up"
        h["Origin"] = "https://temp-number.com"
    r = urllib.request.Request(url, headers=h, data=body)
    try:
        resp = opener.open(r, timeout=timeout)
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return resp.status, resp.geturl(), raw.decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        raw = e.read()
        if e.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return e.code, url, raw.decode("utf-8", "ignore")

print("=== 1) 取 sign-up 页与 csrf token ===")
st, url, h = go("https://temp-number.com/sign-up")
print("  status", st, "len", len(h))
tok = (re.search(r'name="_token"\s+value="([^"]+)"', h) or [None, ""])[1]
if not tok:
    tok = (re.search(r'value="([^"]+)"\s+name="_token"', h) or [None, ""])[1]
print("  csrf token:", tok[:30] + "..." if tok else "NOT FOUND")
cookies = [c.name for c in cj]
print("  cookies:", cookies)

print("\n=== 2) 提交注册 ===")
payload = {
    "_token": tok,
    "full_name": "Alex Carter",
    "email": EMAIL,
    "password": PASSWORD,
    "password_confirmation": PASSWORD,
    "terms": "on",
}
st, url, h = go("https://temp-number.com/sign-up", payload)
print("  status", st, "final", url, "len", len(h))

# 判断结果
t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>", " ", h, flags=re.S)))
errs = re.findall(r'(?:error|invalid|already|failed|wrong)[^<>]{0,90}', h, re.I)
if "/login" in url or "/dashboard" in url or "sign out" in h.lower() or "logout" in h.lower():
    print("  >>> 看起来注册成功（已跳转/已登录）")
for e in errs[:5]:
    print("  hint:", e.strip()[:100])
print("\n  页面文字片段:", t[:400])
