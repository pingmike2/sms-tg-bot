#!/usr/bin/env python3
# 检查 turnstile 脚本是否加载成功
import json, time, urllib.request
import websocket

tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=10))
tgt = [t for t in tabs if t["type"] == "page" and "sign-up" in t.get("url", "")][0]
ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=60)
_id = [0]
def send(method, **params):
    _id[0] += 1
    ws.send(json.dumps({"id": _id[0], "method": method, "params": params}))
    while True:
        m = json.loads(ws.recv())
        if m.get("id") == _id[0]:
            return m
def ev(e):
    r = send("Runtime.evaluate", expression=e, returnByValue=True, awaitPromise=True)
    res = r.get("result", {})
    if "exceptionDetails" in res:
        return "EXC: " + str(res["exceptionDetails"].get("exception", {}).get("description", ""))[:150]
    return res.get("result", {}).get("value")

send("Runtime.enable")
print("turnstile global:", ev("typeof turnstile"))
print("script tags:", ev("""(() => [...document.querySelectorAll('script[src]')].filter(s=>/turnstile|challenge/i.test(s.src)).map(s=>s.src.slice(0,90)).join('\\n')||'none')()"""))
print("data-sitekey:", ev("""(() => {
  const c = document.querySelector('.cf-turnstile');
  return c ? (c.getAttribute('data-sitekey')||'no-key') : 'no-el';
})()"""))
print("display computed:", ev("""(() => {
  const c = document.querySelector('.cf-turnstile');
  if(!c) return 'no-el';
  const s = getComputedStyle(c);
  const p = c.parentElement ? getComputedStyle(c.parentElement) : null;
  return 'self: display='+s.display+' vis='+s.visibility+' | parent: display='+(p?p.display:'?')+' vis='+(p?p.visibility:'?');
})()"""))
print("\n=== 手动调 render ===")
print(ev("""(() => {
  if (typeof turnstile === 'undefined') return 'turnstile undefined';
  try {
    const c = document.querySelector('.cf-turnstile');
    const sk = c.getAttribute('data-sitekey');
    turnstile.render(c, {sitekey: sk, callback: t => { window.__tt = t; }});
    return 'render called, sitekey='+sk.slice(0,20);
  } catch(e) { return 'ERR: '+e.message; }
})()"""))
time.sleep(8)
print("after render size:", ev("""(() => {
  const c=document.querySelector('.cf-turnstile'); const r=c.getBoundingClientRect();
  return Math.round(r.width)+'x'+Math.round(r.height);
})()"""))
print("token:", ev("""(() => { const e=document.querySelector('[name="cf-turnstile-response"]'); return e?e.value.length:-1 })()"""))
print("iframes:", ev("""(() => [...document.querySelectorAll('iframe')].map(f=>f.src.slice(0,90)).join('\\n')||'none')()"""))
ws.close()
