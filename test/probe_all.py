#!/usr/bin/env python3
# 探测 nav 导航 Free SMS 分区全部站点：首页可达性 + 列表/号码的接口形态
import json, re, sys, urllib.request, urllib.error, concurrent.futures

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

SITES = [
    ("smser", "https://smser.net/"),
    ("freereceivesms", "https://www.freereceivesms.com/"),
    ("sms24", "https://sms24.me/en"),
    ("onlinesim", "https://onlinesim.io/ru/free_numbers"),
    ("smsonline", "https://www.smsonline.cloud/zh"),
    ("wetalkapp", "https://wetalkapp.com/receive-sms/"),
    ("supercloudsms", "https://www.supercloudsms.com/country/usa/1.html"),
    ("freephonenum", "https://freephonenum.com/"),
    ("lubansms", "https://lubansms.com/receiveSms"),
    ("7sim", "http://7sim.net/"),
    ("receiveasms", "https://www.receiveasms.com/"),
    ("receivesmsonline_net", "https://www.receivesmsonline.net/"),
    ("smsonline_co", "https://sms-online.co/"),
    ("receivefreesms", "https://receivefreesms.net/"),
    ("receivesmsonline_in", "https://receivesmsonline.in/number"),
    ("smsreceive", "https://sms-receive.net/"),
    ("jiemahao", "https://jiemahao.com/"),
    ("bestsms", "https://bestsms.xyz/"),
    ("zusms", "https://www.zusms.com/"),
    ("mytrashmobile", "https://zh.mytrashmobile.com/numbers"),
    ("smsjapan", "https://sms-japan.com/"),
    ("onlinesimpro", "https://online-sim.pro/zh"),
    ("tempnumber", "https://temp-number.com/"),
    ("tigersms", "https://tiger-sms.shop/free"),
    ("clearcode", "https://clearcode.cn/"),
    ("tempsmss", "https://tempsmss.com/"),
    ("smsverification", "https://sms-verification-number.com/free-numbers-cn/#activity"),
    ("mianfeijiema", "https://www.mianfeijiema.com/"),
    ("receivesmss", "https://receive-smss.com/"),
    ("smsman", "https://sms-man.com/cn/free-numbers"),
]

def probe(item):
    name, url = item
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read().decode("utf-8", "ignore")
            code = r.getcode()
            final = r.geturl()
    except urllib.error.HTTPError as e:
        return {"name": name, "url": url, "code": e.code, "err": "HTTPError", "len": 0}
    except Exception as e:
        return {"name": name, "url": url, "code": 0, "err": str(e)[:90], "len": 0}

    phones = re.findall(r"\+\d{9,15}", body)
    digits = re.findall(r"\b\d{10,15}\b", body)
    return {
        "name": name,
        "url": url,
        "final": final,
        "code": code,
        "len": len(body),
        "plus_phones": len(set(phones)),
        "plain_digits": len(set(digits)),
        "sample": sorted(set(phones))[:3] or sorted(set(digits))[:3],
        "nextdata": "__NEXT_DATA__" in body,
        "nuxt": "__NUXT__" in body,
        "graphql": "graphql" in body.lower(),
        "ajax": "admin-ajax" in body or "/api/" in body,
    }

out = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    for r in ex.map(probe, SITES):
        out.append(r)

for r in out:
    print(f"{r['name']:22s} code={r.get('code')} len={r.get('len',0):7d} "
          f"plus={r.get('plus_phones',0):4d} digits={r.get('plain_digits',0):4d} "
          f"next={r.get('nextdata',False)} nuxt={r.get('nuxt',False)} ajax={r.get('ajax',False)} "
          f"{r.get('sample') or r.get('err','')}")

json.dump(out, open("/root/tempsms-tg-bot/probe.json", "w"), ensure_ascii=False, indent=1)
print("\n全部站点已探测，结果 probe.json")
