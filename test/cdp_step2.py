#!/usr/bin/env python3
# 分步注册：step0 填 name/email/country → Continue → step1 密码 + Turnstile
import json, time, urllib.request
import websocket

tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=10))
tgt = [t for t in tabs if t["type"] == "page" and "sign-up" in t.get("url", "")][0]
ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=90)
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
mb = json.load(open("/tmp/mailtm.json"))
EMAIL = mb["address"]

# step0 填值
p = json.dumps({"full_name": "Alex Carter", "email": EMAIL})
print("step0 fill:", ev("""
(() => {
  const v = %s;
  const setter = (el, val) => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el, val);
    ['input','change','blur'].forEach(e => el.dispatchEvent(new Event(e,{bubbles:true})));
  };
  const done=[];
  for (const [k,val] of Object.entries(v)) {
    const el=document.querySelector(`[name="${k}"]`);
    if(el){setter(el,val);done.push(k);}
  }
  return done.join(',');
})()
""" % p))

# 选国家 = China（点按钮后从列表选）
print("country:", ev("""(() => {
  const btns = [...document.querySelectorAll('button')].filter(b=>b.getBoundingClientRect().height>0);
  const sel = btns.find(b => /China|country|Select/i.test(b.innerText));
  if (!sel) return 'no country btn';
  sel.click();
  return 'clicked: ' + sel.innerText.slice(0,20);
})()"""))
time.sleep(2)

print("选择 China:", ev("""(() => {
  const opts = [...document.querySelectorAll('li, .dropdown-item, [role=option]')].filter(e=>e.getBoundingClientRect().height>0);
  const cn = opts.find(o => o.innerText.trim() === 'China');
  if (!cn) return 'China not found; opts=' + opts.slice(0,5).map(o=>o.innerText.trim()).join('/');
  cn.click();
  return 'selected China';
})()"""))
time.sleep(2)

print("点 Continue:", ev("""(() => {
  const b = [...document.querySelectorAll('button')].find(x => x.getBoundingClientRect().height>0 && /Continue|Next|Send/i.test(x.innerText));
  if (!b) return 'no continue';
  b.click();
  return 'clicked: ' + b.innerText.trim();
})()"""))
time.sleep(8)

print("\n=== 步骤状态 ===")
print(ev("""(() => [...document.querySelectorAll('.auth-step')].map((s,i) =>
  `step${i} disp=${getComputedStyle(s).display} h=${Math.round(s.getBoundingClientRect().height)}`
).join('\\n'))()"""))
print("\n=== 可见 input ===")
print(ev("""(() => [...document.querySelectorAll('input')].filter(e=>e.getBoundingClientRect().height>0)
  .map(e=>`${e.name||'-'} type=${e.type}`).join('\\n')||'none')()"""))
print("\n=== turnstile 容器 ===")
print(ev("""(() => { const c=document.querySelector('.cf-turnstile'); if(!c) return 'none';
  const r=c.getBoundingClientRect(); return Math.round(r.width)+'x'+Math.round(r.height); })()"""))
print("token len:", ev("""(() => { const e=document.querySelector('[name="cf-turnstile-response"]'); return e?e.value.length:-1 })()"""))
print("\n=== 页面提示 ===")
print((ev("document.body.innerText") or "")[-300:].replace("\n", " | "))
ws.close()
