#!/usr/bin/env python3
# 打开 wetalkapp 号码页，勾接口的真实行为（含阿里云验证码调用）
import json, time, urllib.request
import websocket

req = urllib.request.Request("http://127.0.0.1:9222/json/new?https://wetalkapp.com/receive-sms-online-usa-12542492894/", method="PUT")
t = json.load(urllib.request.urlopen(req, timeout=15))
ws = websocket.create_connection(t["webSocketDebuggerUrl"], timeout=200)
_id = [0]
events = []
def send(method, **params):
    _id[0] += 1
    ws.send(json.dumps({"id": _id[0], "method": method, "params": params}))
    while True:
        m = json.loads(ws.recv())
        if m.get("method"):
            events.append(m)
        if m.get("id") == _id[0]:
            return m
def ev(e):
    r = send("Runtime.evaluate", expression=e, returnByValue=True, awaitPromise=True)
    res = r.get("result", {})
    if "exceptionDetails" in res:
        return "EXC: " + str(res["exceptionDetails"].get("exception", {}).get("description", ""))[:150]
    return res.get("result", {}).get("value")

send("Network.enable")
send("Runtime.enable")
time.sleep(12)
print("title:", ev("document.title"))
print("aliyunCaptcha:", ev("typeof window.aliyunCaptcha"))
print("vue messages len:", ev("(() => { try { return document.querySelector('#receiveSMS').__vue__.messages.length } catch(e){ return 'ERR '+e.message } })()"))

# 直接调接口（网页上下文，带上 Origin/Referer）
print("\n直接 fetch smslist:", ev("""(async () => {
  try {
    const r = await fetch('https://api.wetalkapp.com/web/smslist?month=2026-11&number=12542492894&items=50&page=1', {
      headers: {'Accept':'application/json','X-Requested-With':'XMLHttpRequest'}
    });
    const t = await r.text();
    return 'status=' + r.status + ' body=' + t.slice(0,200);
  } catch(e) { return 'ERR ' + e.message; }
})()"""))

# 尝试阿里云验证码 verify()
print("\n调用 aliyunCaptcha.verify():", ev("""(async () => {
  try {
    if (!window.aliyunCaptcha) return 'no aliyunCaptcha';
    const r = await Promise.race([
      window.aliyunCaptcha.verify(),
      new Promise(res => setTimeout(()=>res('TIMEOUT_15s'), 15000))
    ]);
    return 'verify result: ' + String(r).slice(0,120);
  } catch(e) { return 'ERR ' + e.message; }
})()"""))

print("\n验证码容器:", ev("""(() => {
  const c = document.querySelector('#aliyunCaptcha');
  if (!c) return 'none';
  const r = c.getBoundingClientRect();
  return Math.round(r.width) + 'x' + Math.round(r.height) + ' html=' + c.innerHTML.slice(0,150);
})()"""))

# 收网络请求
ws.settimeout(2)
deadline = time.time() + 8
while time.time() < deadline:
    try:
        m = json.loads(ws.recv())
        if m.get("method"):
            events.append(m)
    except Exception:
        pass
ws.settimeout(200)
print("\n=== wetalk/aliyun 请求 ===")
for e in events:
    p = e.get("params", {})
    if e.get("method") == "Network.requestWillBeSent":
        u = p.get("request", {}).get("url", "")
        if "wetalk" in u or "aliyun" in u or "captcha" in u:
            print("REQ ", u[:110])
ws.close()
