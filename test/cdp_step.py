#!/usr/bin/env python3
# 走分步表单：先看第一步有哪些字段/步骤
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
        return "EXC: " + str(res["exceptionDetails"].get("exception", {}).get("description", ""))[:120]
    return res.get("result", {}).get("value")

send("Runtime.enable")
print("=== 所有 auth-step 及可见性 ===")
print(ev("""(() => [...document.querySelectorAll('.auth-step')].map((s,i) => {
  const r = s.getBoundingClientRect();
  const h = s.querySelector('h1,h2,h3,.title');
  return `step${i}: ${Math.round(r.width)}x${Math.round(r.height)} disp=${getComputedStyle(s).display} | ${(h?h.innerText:s.innerText).slice(0,50).replace(/\\n/g,' ')}`;
}).join('\\n') || 'none')()"""))

print("\n=== 当前可见的 input/button ===")
print(ev("""(() => [...document.querySelectorAll('input,button')].filter(e=>{
  const r=e.getBoundingClientRect(); return r.width>0 && r.height>0;
}).map(e => `${e.tagName} name=${e.name||'-'} type=${e.type||'-'} ph=${e.placeholder||'-'} txt=${(e.innerText||'').slice(0,25)}`).join('\\n') || 'none')()"""))

print("\n=== 可见区域文本 ===")
print((ev("""(() => {
  const st = [...document.querySelectorAll('.auth-step')].find(s=>getComputedStyle(s).display!=='none');
  return st ? st.innerText.slice(0,400) : document.body.innerText.slice(0,400);
})()""") or "").replace("\n", " | "))
ws.close()
