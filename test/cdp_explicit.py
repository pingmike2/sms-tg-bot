#!/usr/bin/env python3
# explicit 模式重新加载 turnstile api.js，再 render
import json, time, urllib.request
import websocket

tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=10))
tgt = [t for t in tabs if t["type"] == "page" and "sign-up" in t.get("url", "")][0]
ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=200)
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
        return "EXC: " + str(res["exceptionDetails"].get("exception", {}).get("description", ""))[:200]
    return res.get("result", {}).get("value")

send("Runtime.enable")
# 先在 step0 填邮箱，确保 step1 可进
mb = json.load(open("/tmp/mailtm.json"))
print("== 重新注入 api.js (explicit) ==")
print(ev("""(async () => {
  // 清除旧的
  try { turnstile.remove(); } catch(e) {}
  document.querySelectorAll('script[src*=turnstile]').forEach(s => s.remove());
  const s = document.createElement('script');
  s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?onload=__tsReady&render=explicit';
  s.async = true;
  s.defer = true;
  window.__tsReady = false;
  window.__tsReadyCb = () => { window.__tsReady = true; };
  document.head.appendChild(s);
  for (let i=0;i<40;i++) { await new Promise(r=>setTimeout(r,500)); if (window.turnstile && window.turnstile.render) break; }
  return 'loaded=' + (typeof turnstile) + ' ready=' + window.__tsReady;
})()"""))

# 进入 step1
p = json.dumps({"full_name": "Alex Carter", "email": mb["address"]})
ev("""
(() => {
  const v = %s;
  const setter=(el,val)=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,val);
    ['input','change','blur'].forEach(e=>el.dispatchEvent(new Event(e,{bubbles:true})));};
  for (const [k,val] of Object.entries(v)) { const el=document.querySelector(`[name="${k}"]`); if(el) setter(el,val); }
  return 1;
})()
""" % p)
ev("""(() => { const b=[...document.querySelectorAll('button')].find(x=>x.getBoundingClientRect().height>0 && /Continue/i.test(x.innerText)); if(b) b.click(); return 1; })()""")
time.sleep(5)
print("step1 h:", ev("""(() => { const s=[...document.querySelectorAll('.auth-step')].find(x=>getComputedStyle(x).display!=='none'); return s?Math.round(s.getBoundingClientRect().height):-1; })()"""))
print("terms 位置:", ev("""(() => { const c=document.querySelector('.cf-turnstile'); if(!c) return 'none'; const r=c.getBoundingClientRect(); return Math.round(r.width)+'x'+Math.round(r.height); })()"""))

print("\n== 等 turnstile 脚本 ready ==")
print(ev("""(async () => {
  for (let i=0;i<30;i++) {
    if (window.turnstile && window.turnstile.render) return 'ready after ' + (i*0.5) + 's';
    await new Promise(r=>setTimeout(r,500));
  }
  return 'timeout';
})()"""))

print("\n== render ==")
print(ev("""(() => {
  try {
    const c = document.querySelector('.cf-turnstile');
    if (!c) return 'no container';
    c.innerHTML = '';
    window.__tok3 = null; window.__tErr3 = null;
    const id = turnstile.render(c, {
      sitekey: '0x4AAAAAAAGhGJU0btRzc26Z',
      theme: 'light',
      callback: t => { window.__tok3 = t; },
      'error-callback': e => { window.__tErr3 = String(e); },
      'timeout-callback': () => { window.__tErr3 = 'timeout'; }
    });
    return 'rendered id=' + id;
  } catch(e) { return 'ERR: ' + e.message; }
})()"""))

for i in range(20):
    time.sleep(3)
    tok = ev("window.__tok3 ? window.__tok3.length : 0")
    iframes = ev("document.querySelectorAll('iframe').length")
    err = ev("window.__tErr3 || 'none'")
    print(f"  t+{3*(i+1)}s token={tok} iframes={iframes} err={err}")
    if isinstance(tok, int) and tok > 20:
        print(">>> 通过", ev("window.__tok3.slice(0,50)"))
        break
ws.close()
