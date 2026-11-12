#!/usr/bin/env python3
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
    r = send("Runtime.evaluate", expression=e, returnByValue=True)
    return r.get("result", {}).get("result", {}).get("value")

send("Runtime.enable")
print("=== 页面上 turnstile 相关元素 ===")
print(ev("""(() => {
  const out = [];
  document.querySelectorAll('*').forEach(el => {
    const id = (el.id||'') + ' ' + (el.className||'');
    if (/turnstile|captcha|challenge/i.test(id)) out.push(el.tagName + ' #' + el.id + ' .' + (el.className||'').toString().slice(0,60));
  });
  return out.slice(0,15).join('\\n') || 'none';
})()"""))

print("\n=== iframe 列表 ===")
print(ev("""(() => [...document.querySelectorAll('iframe')].map(f =>
  (f.src||'(no src)').slice(0,100) + ' | visible=' + (f.offsetWidth>0)
).join('\\n') || 'none')()"""))

print("\n=== 容器尺寸（判断是否可见）===")
print(ev("""(() => {
  const c = document.querySelector('.cf-turnstile, [data-sitekey], #cf-turnstile');
  if (!c) return 'no container';
  const r = c.getBoundingClientRect();
  return `${c.tagName} w=${Math.round(r.width)} h=${Math.round(r.height)} visible=${r.width>0&&r.height>0}`;
})()"""))
ws.close()
