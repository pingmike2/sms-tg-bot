/**
 * 接码聚合 Telegram Bot — 单人使用
 * 覆盖 nav.eooce.com → Tools → Free SMS 分区全部 29 个站点
 *
 * 环境变量：BOT_TOKEN / OWNER_ID / WEBHOOK_SECRET
 */

const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";

/* ===== 站点表：nav.eooce.com Tools→Free SMS 全部 29 个 ===== */
const SITES = [
  { id: "tempsmss", name: "tempsmss", home: "https://tempsmss.com/", ok: true },
  { id: "tigersms", name: "tiger-sms", home: "https://tiger-sms.com/free", ok: true },
  { id: "smsreceive", name: "sms-receive.net", home: "https://sms-receive.net/", ok: true },
  { id: "smsonline_co", name: "sms-online.co", home: "https://sms-online.co/receive-free-sms", ok: false, note: "CF TLS 指纹拦截" },
  { id: "supercloudsms", name: "supercloudsms", home: "https://www.supercloudsms.com/country/usa/1.html", ok: true },
  { id: "freereceivesms", name: "freereceivesms", home: "https://www.freereceivesms.com/", ok: true },
  { id: "smser", name: "smser", home: "https://smser.net/", ok: false, note: "API 需登录" },
  { id: "sms24", name: "sms24", home: "https://sms24.me/en", ok: false, note: "CF 拦截" },
  { id: "onlinesim", name: "onlinesim", home: "https://onlinesim.io/ru/free_numbers", ok: false, note: "需登录" },
  { id: "smsonline", name: "smsonline.cloud", home: "https://www.smsonline.cloud/zh", ok: false, note: "SSR 需 JS" },
  { id: "freephonenum", name: "freephonenum", home: "https://freephonenum.com/", ok: false, note: "JS 加密" },
  { id: "lubansms", name: "lubansms", home: "https://lubansms.com/receiveSms", ok: false, note: "需登录" },
  { id: "7sim", name: "7sim", home: "http://7sim.net/", ok: false, note: "CF 拦截" },
  { id: "receiveasms", name: "receiveasms", home: "https://www.receiveasms.com/", ok: false, note: "动态加载" },
  { id: "receivesmsonline_net", name: "receivesmsonline.net", home: "https://www.receivesmsonline.net/", ok: false, note: "CF 拦截" },
  { id: "receivefreesms", name: "receivefreesms", home: "https://receivefreesms.net/", ok: false, note: "CF 拦截" },
  { id: "receivesmsonline_in", name: "receivesmsonline.in", home: "https://receivesmsonline.in/number", ok: false, note: "CF 拦截" },
  { id: "jiemahao", name: "jiemahao", home: "https://jiemahao.com/", ok: false, note: "需登录" },
  { id: "bestsms", name: "bestsms", home: "https://bestsms.xyz/", ok: false, note: "动态加载" },
  { id: "zusms", name: "zusms", home: "https://www.zusms.com/", ok: false, note: "Nuxt 需 JS" },
  { id: "mytrashmobile", name: "mytrashmobile", home: "https://zh.mytrashmobile.com/numbers", ok: false, note: "CF 拦截" },
  { id: "smsjapan", name: "sms-japan", home: "https://sms-japan.com/", ok: false, note: "空页" },
  { id: "onlinesimpro", name: "online-sim.pro", home: "https://online-sim.pro/zh", ok: false, note: "CF 拦截" },
  { id: "tempnumber", name: "temp-number", home: "https://temp-number.com/", ok: false, note: "需登录" },
  { id: "clearcode", name: "clearcode", home: "https://clearcode.cn/", ok: false, note: "动态加载" },
  { id: "smsverification", name: "sms-verification", home: "https://sms-verification-number.com/free-numbers-cn/", ok: false, note: "CF 拦截" },
  { id: "mianfeijiema", name: "mianfeijiema", home: "https://www.mianfeijiema.com/", ok: true },
  { id: "receivesmscc", name: "receive-sms.cc", home: "https://receive-sms.cc/", ok: true },
  { id: "receivesmss", name: "receive-smss", home: "https://receive-smss.com/", ok: false, note: "CF 拦截" },
  { id: "smsman", name: "sms-man", home: "https://sms-man.com/cn/free-numbers", ok: false, note: "CF 拦截" },
];

/* ===== 基础工具 ===== */
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const mem = new Map();
const cGet = (k, ttl) => { const v = mem.get(k); return v && Date.now() - v.t < ttl ? v.d : null; };
const cSet = (k, d) => { mem.set(k, { t: Date.now(), d }); if (mem.size > 300) mem.delete(mem.keys().next().value); };

function decodeEnt(s) {
  return s.replace(/&(#x?[0-9a-f]+|[a-z]+);/gi, (m, e) => {
    if (e[0] === "#") {
      const n = e[1].toLowerCase() === "x" ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10);
      return Number.isFinite(n) ? String.fromCodePoint(n) : m;
    }
    return ({ amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " " })[e.toLowerCase()] ?? m;
  });
}
function plain(html) {
  const t = html
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<svg[\s\S]*?<\/svg>/gi, " ")
    .replace(/<[^>]+>/g, " ");
  return decodeEnt(t).replace(/\s+/g, " ").trim();
}

async function getText(url, ttl = 60) {
  const k = "g:" + url;
  if (ttl > 0) { const h = cGet(k, ttl); if (h) return h; }
  const r = await fetch(url, {
    headers: { "user-agent": UA, "accept-language": "en-US,en;q=0.9", accept: "text/html,application/json,*/*" },
    cf: { cacheTtl: 0 },
  });
  const text = await r.text();
  if (ttl > 0 && r.status < 400) cSet(k, text);
  return text;
}

async function tg(env, method, payload) {
  const r = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload),
  });
  return r.json().catch(() => ({ ok: false }));
}
async function send(env, chatId, text, extra = {}) {
  const parts = [];
  let rest = text;
  while (rest.length > 3800) {
    let cut = rest.lastIndexOf("\n", 3800);
    if (cut < 1000) cut = 3800;
    parts.push(rest.slice(0, cut)); rest = rest.slice(cut);
  }
  parts.push(rest);
  let last;
  for (const p of parts) {
    last = await tg(env, "sendMessage", { chat_id: chatId, text: p, parse_mode: "HTML", link_preview_options: { is_disabled: true }, ...extra });
    if (!last.ok) last = await tg(env, "sendMessage", { chat_id: chatId, text: p.replace(/<[^>]+>/g, ""), link_preview_options: { is_disabled: true } });
  }
  return last;
}

/* ===== 活跃时间解析 & 排序 ===== */
// 把 "1 minute ago" / "5分钟前" / "1小时前" 等转成秒，用于排序
function agoToSec(s) {
  if (!s) return Infinity;
  const t = String(s).toLowerCase();
  const n = parseFloat((/(\d+(?:\.\d+)?)/.exec(t) || [])[1]);
  if (!Number.isFinite(n)) return Infinity;
  if (/second|秒/.test(t)) return n;
  if (/minute|分钟|分鐘/.test(t)) return n * 60;
  if (/hour|小时|小時/.test(t)) return n * 3600;
  if (/day|天/.test(t)) return n * 86400;
  if (/month|月/.test(t)) return n * 2592000;
  if (/year|年/.test(t)) return n * 31536000;
  return Infinity;
}
// 列表排序：最近有短信的排前面；无时间信息的按原始顺序垫底
function sortByActivity(items) {
  return items
    .map((it, i) => ({ it, i, sec: it.lastSms ? agoToSec(it.lastSms) : Infinity }))
    .sort((a, b) => (a.sec === b.sec ? a.i - b.i : a.sec - b.sec))
    .map((x) => x.it);
}

/* ===== 各站适配器 ===== */
const ADAPTERS = {
  tempsmss: {
    list: async () => {
      const html = await getText("https://tempsmss.com/receive-sms/", 45);
      const out = [], seen = new Set();
      for (const m of html.matchAll(/<div class="custom-country-box">\s*<a href="https:\/\/[^"]+?\/receive-sms\/([^"\/]+)\/?"/g)) {
        if (seen.has(m[1])) continue;
        seen.add(m[1]);
        const seg = html.slice(m.index, m.index + 1400);
        const h3 = /<h3>([\s\S]{0,40}?)<\/h3>/.exec(seg);
        let ph = h3 ? plain(h3[1]).replace(/\D/g, "") : "";
        // 号太短说明 h3 取到的是打码值，依次退回 data-phone / slug 尾部数字
        if (!/^\d{9,15}$/.test(ph)) {
          const dp = /data-phone="(\d{9,15})"/.exec(seg);
          if (dp) ph = dp[1];
        }
        if (!/^\d{9,15}$/.test(ph)) {
          const tail = /(\d{9,15})$/.exec(m[1]);
          if (tail) ph = tail[1];
        }
        // 还凑不出完整号就留空，让上层按 slug 显示，不展示 +1****17 这种残号
        if (!/^\d{9,15}$/.test(ph)) ph = "";
        // 卡片里有 "Last SMS N minutes ago" / "Added N hours ago"
        const ptxt = plain(seg);
        const lastSms = (/Last SMS\s+(\d+\s+(?:second|minute|hour|day|month|year)s?\s+ago|just now)/i.exec(ptxt) || [])[1] || "";
        const added = (/Added\s+(\d+\s+(?:second|minute|hour|day|month|year)s?\s+ago)/i.exec(ptxt) || [])[1] || "";
        out.push({ phone: ph ? "+" + ph : "", slug: m[1], lastSms: lastSms.trim(), added: added.trim() });
      }
      return sortByActivity(out);
    },
    read: async (slug) => {
      const pageUrl = `https://tempsmss.com/receive-sms/${slug}/`;
      const html = await getText(pageUrl, 0);
      let phone = (/data-phone="(\d{9,15})"/.exec(html) || [])[1] || "";
      const postId = (/data-post="(\d+)"/.exec(html) || [])[1] || "";
      const nonce = (/"security"\s*:\s*["']([a-z0-9]+)/.exec(html) || [])[1] || "";

      // 静态页里的验证码是 ••••••；真码在 admin-ajax 的 sms_receiver_get_messages 里（sms-spoiler data-c = base64）
      let body = html;
      if (postId && nonce) {
        try {
          const rf = await fetch("https://tempsmss.com/wp-admin/admin-ajax.php", {
            method: "POST",
            headers: {
              "user-agent": UA,
              "content-type": "application/x-www-form-urlencoded",
              "x-requested-with": "XMLHttpRequest",
              referer: pageUrl,
              origin: "https://tempsmss.com",
            },
            body: new URLSearchParams({
              action: "sms_receiver_get_messages",
              phone: phone,
              post_id: postId,
              page_url: pageUrl,
              security: nonce,
            }).toString(),
          });
          const t = await rf.text();
          if (t && t.includes("receivedmessage")) body = t;
        } catch (_) {}
      }

      if (!phone) phone = (/data-phone="(\d{9,15})"/.exec(body) || [])[1] || "";
      const msgs = [];
      for (const b of body.split('<div class="receivedmessage">').slice(1)) {
        const time = plain((/<div class="time">([\s\S]*?)<\/div>/.exec(b) || [, ""])[1]);
        const from = plain((/<div class="from">([\s\S]*?)<\/div>/.exec(b) || [, ""])[1]).replace(/^From:\s*/i, "");
        const bodyHtml = (/<p class="msg[^"]*">([\s\S]*?)<\/p>/.exec(b) || [, ""])[1];
        // 解密所有 sms-spoiler（data-c 是 base64）
        let decoded = bodyHtml.replace(/<span class="sms-spoiler"[^>]*data-c="([^"]+)"[^>]*>[\s\S]*?<\/span>/gi, (m, c) => {
          try { return atob(c); } catch { return m; }
        });
        let text = plain(decoded).replace(/\s*·\s*Source:\s*\S+$/i, "").trim();
        // 还有残留的 • 就说明没解出来
        const masked = /•/.test(text);
        // 验证码：纯数字 4-8 位，或 732-344 / 123 456 这类分段格式
        let code = "";
        if (!masked) {
          const m1 = /(?<![\d-])(\d{3}[- ]\d{3})(?![\d-])/.exec(text);   // 732-344
          const m2 = /(?<![\d-])(\d{4,8})(?![\d-])/.exec(text);
          code = (m1 ? m1[1] : "") || (m2 ? m2[1] : "");
        }
        msgs.push({ time, from, body: text, code, masked });
      }
      return { phone: phone ? "+" + phone : slug, msgs };
    },
  },

  tigersms: {
    list: async () => {
      const html = await getText("https://tiger-sms.com/free", 45);
      const out = [], seen = new Set();
      // 只取真实号码卡片 <a class="t_free__num" ...>，卡片内有号码/Active/Last SMS
      for (const m of html.matchAll(/<a class="t_free__num"[^>]*href="https:\/\/tiger-sms\.com\/free\/([a-z-]+)\/(\d{7,15})"[\s\S]*?<\/a>/g)) {
        const key = m[1] + "/" + m[2];
        if (seen.has(key)) continue;
        seen.add(key);
        const seg = plain(m[0]);
        const lastSms = (/Last SMS\s+(\d+\s+(?:second|minute|hour|day|month|year)s?\s+ago|just now)/i.exec(seg) || [])[1] || "";
        const active = /is-live|>Active</.test(m[0]);
        out.push({ phone: "+" + m[2], slug: key, lastSms: lastSms.trim(), active });
      }
      // 兜底：卡片结构变了就退回裸链接（无活跃时间）
      if (!out.length) {
        for (const m of html.matchAll(/https:\/\/tiger-sms\.com\/free\/([a-z-]+)\/(\d{7,15})/g)) {
          const key = m[1] + "/" + m[2];
          if (seen.has(key)) continue;
          seen.add(key);
          out.push({ phone: "+" + m[2], slug: key, lastSms: "" });
        }
      }
      return sortByActivity(out);
    },
    read: async (slug) => {
      const html = await getText(`https://tiger-sms.com/free/${slug}`, 0);
      const txt = plain(html);
      const phone = (/\+\d{7,15}/.exec(txt) || [])[0] || "+" + slug.split("/")[1];
      const msgs = [];
      for (const m of txt.matchAll(/\b(\d{4,8})\s+Copied\s+([A-Za-z0-9 ._+-]{0,24}?)\s+(\d+\s+(?:second|minute|hour|day|month)s?\s+ago)\s+([\s\S]{5,240}?)(?=\s\d{4,8}\s+Copied|$)/g)) {
        msgs.push({ code: m[1], from: m[2].trim(), time: m[3], body: m[4].trim().slice(0, 220) });
        if (msgs.length >= 12) break;
      }
      return { phone, msgs };
    },
  },

  smsreceive: {
    list: async () => {
      const html = await getText("https://sms-receive.net/", 45);
      const out = [], seen = new Set();
      for (const m of html.matchAll(/href="(\d{10,15}-[A-Za-z]+)"/g)) {
        if (seen.has(m[1])) continue;
        seen.add(m[1]);
        out.push({ phone: "+" + m[1].split("-")[0], slug: m[1] });
      }
      return out;
    },
    read: async (slug) => {
      const num = slug.split("-")[0];
      // 真实数据源：/{phone}/get_sms_register.php?phone=NNN 返回 JSON
      try {
        const raw = await getText(`https://sms-receive.net/${num}/get_sms_register.php?phone=${num}`, 0);
        const arr = JSON.parse(raw);
        if (Array.isArray(arr) && arr.length) {
          const msgs = arr.slice(0, 15).map((j) => {
            const body = String(j.mesaj || "").trim();
            return {
              from: String(j.telefon || "").slice(0, 26),
              body: body.slice(0, 220),
              time: String(j.data || "").slice(0, 19),
              code: (/\b\d{4,8}\b/.exec(body) || [""])[0],
            };
          });
          return { phone: "+" + num, msgs };
        }
      } catch (_) {}
      // 兜底：静态表格
      const html = await getText(`https://sms-receive.net/${slug}`, 0);
      const msgs = [];
      for (const row of html.split("<tr").slice(1)) {
        const cells = [...row.matchAll(/<td[^>]*>([\s\S]*?)<\/td>/g)].map((x) => plain(x[1]));
        const body = cells[1] || "";
        // 过滤 JS 模板残留（如 ${json[i].mesaj}）、占位符、HTML 标签残余和过短噪声
        if (!body || body.length < 6) continue;
        if (/\$\{|json\[|function|var |let |const |undefined|null/.test(body)) continue;
        if (/^[\s\W]+$/.test(body)) continue;
        if (!/[A-Za-z0-9\u4e00-\u9fa5]{4,}/.test(body)) continue;
        // 必须像一条真短信：含数字验证码 或 含常见服务词
        if (!/\b\d{4,8}\b/.test(body) && !/(code|verify|verification|code:|otp|验证码)/i.test(body)) continue;
        if (cells.length >= 3) {
          msgs.push({ from: (cells[0] || "").slice(0, 26), body: body.slice(0, 220), time: cells[2] || "", code: (/\b\d{4,8}\b/.exec(body) || [""])[0], masked: false });
        }
        if (msgs.length >= 15) break;
      }
      return { phone: "+" + num, msgs };
    },
  },

  mianfeijiema: {
    list: async () => {
      const html = await getText("https://www.mianfeijiema.com/", 45);
      const out = [], seen = new Set();
      // 号码页 /sms/<号码>，页面同时给全号
      for (const m of html.matchAll(/href="\/sms\/(\d{8,15})"/g)) {
        if (seen.has(m[1])) continue;
        seen.add(m[1]);
        out.push({ phone: "+" + m[1], slug: m[1], lastSms: "" });
      }
      return sortByActivity(out);
    },
    read: async (slug) => {
      const html = await getText(`https://www.mianfeijiema.com/sms/${slug}`, 0);
      const msgs = [];
      // 消息结构：div.rowbox.message_details > .sender / .msg / .time
      for (const b of html.split(/class="rowbox message_details"/).slice(1)) {
        const sender = plain((/col-md-3 sender">([\s\S]*?)<\/div>/.exec(b) || [, ""])[1]);
        const msgHtml = (/col-md-6 msg">([\s\S]*?)<\/div>/.exec(b) || [, ""])[1];
        const time = plain((/col-md-3 time">([\s\S]*?)<\/div>/.exec(b) || [, ""])[1]);
        // 广告行跳过
        if (!msgHtml || /adsbygoogle|pagead2/.test(msgHtml)) continue;
        // 验证码优先取 data-clipboard-text（站点自己给的明文）
        const clip = (/data-clipboard-text="([^"]*)"/.exec(msgHtml) || [])[1] || "";
        let text = plain(msgHtml).trim();
        if (text.length < 5) continue;
        const code = clip || (/(?<![\d-])(\d{3}[- ]\d{3})(?![\d-])/.exec(text) || [])[1] || (/(?<![\d-])(\d{4,8})(?![\d-])/.exec(text) || [])[1] || "";
        msgs.push({ from: sender.slice(0, 26), body: text.slice(0, 240), time, code, masked: /•/.test(text) });
        if (msgs.length >= 15) break;
      }
      return { phone: "+" + slug, msgs };
    },
  },

  receivesmscc: {
    list: async () => {
      const html = await getText("https://receive-sms.cc/", 45);
      const out = [], seen = new Set();
      // 链接形如 /US-Phone-Number/12543207598
      for (const m of html.matchAll(/href="\/([A-Za-z-]+-Phone-Number)\/(\d{7,15})"/g)) {
        if (seen.has(m[2])) continue;
        seen.add(m[2]);
        out.push({ phone: "+" + m[2], slug: `${m[1]}/${m[2]}`, lastSms: "" });
      }
      // 部分站把号放在标题里
      if (!out.length) {
        for (const m of html.matchAll(/href="\/(\d{7,15})"/g)) {
          if (seen.has(m[1])) continue;
          seen.add(m[1]);
          out.push({ phone: "+" + m[1], slug: m[1], lastSms: "" });
        }
      }
      return out;
    },
    read: async (slug) => {
      const url = slug.includes("/") ? `https://receive-sms.cc/${slug}` : `https://receive-sms.cc/${slug}`;
      const html = await getText(url, 0);
      const msgs = [];
      // 每条：div.form(From X) + span.time + div.con(正文)
      for (const b of html.split(/class="row list-message"/).slice(1)) {
        for (const it of b.split(/<div class="item">/).slice(1)) {
          const from = plain((/class="form">([\s\S]*?)<\/div>/.exec(it) || [, ""])[1]).replace(/^From\s*/i, "");
          const time = plain((/class="time">([\s\S]*?)<\/span>/.exec(it) || [, ""])[1]);
          const text = plain((/class="con">([\s\S]*?)<\/div>/.exec(it) || [, ""])[1]).trim();
          if (!text || text.length < 4) continue;
          if (/^\s*No messages?\b/i.test(text)) continue;
          const code = (/(?<![\d-])(\d{3}[- ]\d{3})(?![\d-])/.exec(text) || [])[1]
            || (/(?<![\d-])(\d{4,8})(?![\d-])/.exec(text) || [])[1] || "";
          msgs.push({ from: from.slice(0, 26), body: text.slice(0, 240), time, code, masked: /•/.test(text) });
          if (msgs.length >= 15) break;
        }
        if (msgs.length >= 15) break;
      }
      const ph = (/\+?(\d{10,15})/.exec(slug.split("/").pop() || "") || [])[1] || slug;
      return { phone: "+" + ph, msgs };
    },
  },

  smsonline_co: {
    list: async () => {
      // /receive-free-sms 就是真实列表页（首页 302 到这里）
      const html = await getText("https://sms-online.co/receive-free-sms", 45);
      const out = [], seen = new Set();
      for (const m of html.matchAll(/receive-free-sms\/(\d{7,15})/g)) {
        if (seen.has(m[1])) continue;
        seen.add(m[1]);
        out.push({ phone: "+" + m[1], slug: m[1] });
      }
      return out;
    },
    read: async (slug) => {
      const txt = plain(await getText(`https://sms-online.co/receive-free-sms/${slug}`, 0));
      const msgs = [];
      // 结构：<发送方> <时间描述> <正文> 或者 <正文> <发送号> <时间描述>
      const re = /([A-Za-z0-9 ._:+\-\/]{2,30}?)\s+(\d+\s+(?:year|month|day|hour|minute|second)s?\s+ago|just now)\s+([\s\S]{5,240}?)(?=\s+[A-Za-z0-9 ._:+\-\/]{2,30}?\s+\d+\s+(?:year|month|day|hour|minute|second)s?\s+ago|\s*$)/g;
      for (const m of txt.matchAll(re)) {
        const body = m[3].trim();
        if (body.length < 5) continue;
        msgs.push({ from: m[1].trim().slice(0, 24), time: m[2], body: body.slice(0, 220), code: (/\b\d{4,8}\b/.exec(body) || [""])[0] });
        if (msgs.length >= 12) break;
      }
      if (!msgs.length) {
        // 兜底：只截正文段落；拿不到结构化字段就不硬凑验证码
        const i = txt.indexOf("List of last 100 SMS messages");
        if (i > 0) {
          const seg = txt.slice(i + 30, i + 1200).trim();
          if (seg.length > 20) msgs.push({ from: "", time: "", body: seg.slice(0, 300), code: "", masked: false });
        }
      }
      return { phone: "+" + slug, msgs };
    },
  },

  supercloudsms: {
    list: async () => {
      const html = await getText("https://www.supercloudsms.com/country/usa/1.html", 45);
      const out = [], seen = new Set();
      for (const m of html.matchAll(/\/message\/(\d{7,15})\.html/g)) {
        if (seen.has(m[1])) continue;
        seen.add(m[1]);
        out.push({ phone: "+" + m[1], slug: m[1] });
      }
      return out;
    },
    read: async (slug) => {
      const html = await getText(`https://www.supercloudsms.com/message/${slug}.html`, 0);
      const msgs = [];
      // 消息正文在 <div class="card-body"> 里
      for (const b of html.split(/<div class="card-body[^"]*">/).slice(1)) {
        const body = plain(b).slice(0, 300).trim();
        if (body.length < 10) continue;
        if (/adsbygoogle|广告位招租/.test(body)) continue;
        msgs.push({ body: body.slice(0, 240), from: "", time: "", code: (/\b\d{4,8}\b/.exec(body) || [""])[0] });
        if (msgs.length >= 12) break;
      }
      const ph = (/\+(\d{7,15})/.exec(plain(html)) || [])[1] || slug;
      return { phone: "+" + ph, msgs };
    },
  },


  freereceivesms: {
    list: async () => {
      const html = await getText("https://www.freereceivesms.com/", 45);
      const out = [], seen = new Set();
      // 卡片：<h4>+39 3508910943</h4> ... <h5>国家</h5> ... href="/it/7318472.html"
      for (const b of html.split(/number-boxes-item/).slice(1)) {
        const href = (/href="(\/([a-z]{2})\/(\d{7,10})\.html)"/.exec(b) || []);
        const slug = (href[1] || "").replace(/^\//, "").replace(/\.html$/, "");
        if (!slug || seen.has(slug)) continue;
        seen.add(slug);
        const raw = (/(<h4[^>]*>[\s\S]*?<\/h4>)/.exec(b) || [,""])[1];
        const phone = plain(raw).replace(/\s+/g, "");
        if (!/^\+\d{7,15}$/.test(phone)) continue;
        out.push({ phone, slug, lastSms: "" });
      }
      // 兜底：只取链接
      if (!out.length) {
        for (const m of html.matchAll(/href="\/([a-z]{2}\/\d{7,10})\.html"/g)) {
          if (seen.has(m[1])) continue;
          seen.add(m[1]);
          out.push({ phone: "", slug: m[1], extra: m[1].split("/")[0], lastSms: "" });
        }
      }
      return sortByActivity(out);
    },
    read: async (slug) => {
      const txt = plain(await getText(`https://www.freereceivesms.com/${slug}.html`, 0));
      const phone = (/\+\d{7,15}/.exec(txt) || [])[0] || "";
      const msgs = [];
      const re = /([\s\S]{12,240}?)\s+(\d+\s*(?:天前|小时前|分钟前|days? ago|hours? ago|minutes? ago))/g;
      for (const m of txt.matchAll(re)) {
        const body = m[1].trim();
        if (!/[A-Za-z0-9\u4e00-\u9fa5]{6,}/.test(body)) continue;
        if (/点击复制|刷新本页面|他人也可/.test(body)) continue;
        msgs.push({ body: body.slice(-200), time: m[2], from: "", code: (/\b\d{4,8}\b/.exec(body) || [""])[0] });
        if (msgs.length >= 10) break;
      }
      return { phone, msgs };
    },
  },
};

/* ===== 渲染 ===== */
function siteKB() {
  const rows = [];
  const works = SITES.filter((s) => s.ok);
  for (let i = 0; i < works.length; i += 2) {
    rows.push(works.slice(i, i + 2).map((s) => ({ text: s.name, callback_data: "s:" + s.id })));
  }
  rows.push([{ text: "📋 全部 29 个站点状态", callback_data: "s:__all" }]);
  return { inline_keyboard: rows };
}

function fmtSiteList(site, items) {
  if (!items.length) return `<b>${esc(site.name)}</b>\n没抓到号码（站点可能改版/被拦）。`;
  const hasTime = items.some((it) => it.lastSms);
  const lines = items.slice(0, 24).map((it, i) => {
    const ph = it.phone || (it.extra ? `${it.extra}/${it.slug.split("/")[1]}` : it.slug);
    const t = it.lastSms ? ` · ${esc(it.lastSms)}` : it.added ? ` · 新增 ${esc(it.added)}` : "";
    const live = it.active ? "🟢 " : "";
    return `${live}${i + 1}. <code>${esc(ph)}</code>${t}`;
  });
  const head = hasTime
    ? `<b>${esc(site.name)}</b> 号码（${items.length}）— 按最近收短信时间排序`
    : `<b>${esc(site.name)}</b> 号码（${items.length}）`;
  return `${head}\n点下面按钮看短信：\n\n${lines.join("\n")}`;
}

function phoneKB(siteId, items) {
  const rows = [];
  const top = items.slice(0, 16);
  for (let i = 0; i < top.length; i += 2) {
    rows.push(top.slice(i, i + 2).map((it) => {
      // 直接用适配器给的号；只有真没有时才从 slug 抽完整数字（不截尾、不加 *）
      const label = it.phone || "+" + String(it.slug).replace(/\D/g, "");
      return { text: (it.active ? "🟢 " : "") + label, callback_data: `r:${siteId}:${it.slug}` };
    }));
  }
  rows.push([{ text: "⬅️ 返回站点", callback_data: "s:__all" }]);
  return { inline_keyboard: rows };
}

function fmtMsgs(site, res) {
  const head = `<b>${esc(site.name)}</b> · <code>${esc(res.phone || "?")}</code>`;
  // 适配器明确标记不可读时，把原因原样告诉用户，不装成“暂无短信”
  if (res.ok === false) return `${head}\n⛔ ${esc(res.note || "该站不可读码")}`;
  if (!res.msgs.length) return `${head}\n暂无短信（可能需要刷新，或该号已失效）。`;
  const body = res.msgs.slice(0, 6).map((m) => {
    const t = [m.time, m.from].filter(Boolean).join(" · ");
    // 正文里的验证码单独高亮，避免被淹没
    let text = (m.body || "").slice(0, 300);
    if (m.code && text.includes(m.code)) text = text.replace(m.code, `<b>${esc(m.code)}</b>`);
    else text = esc(text);
    const tail = m.code ? `\n👉 验证码：<code>${esc(m.code)}</code>` : m.masked ? "\n⚠️ 该条已打码，解密失败" : "";
    return `⏱ ${esc(t)}\n${text}${tail}`;
  });
  return `${head}\n\n${body.join("\n\n")}`;
}

/* ===== 路由 ===== */
async function handle(env, up) {
  if (up.callback_query) {
    const cq = up.callback_query;
    const chatId = cq.message.chat.id;
    if (String(cq.from.id) !== String(env.OWNER_ID)) {
      return tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: "私有机器人", show_alert: true });
    }
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id });
    const parts = (cq.data || "").split(":");
    const act = parts[0];

    if (act === "s") {
      const id = parts[1];
      if (id === "__all") {
        const works = SITES.filter((s) => s.ok).map((s) => `✅ ${s.name}`).join("\n");
        const dead = SITES.filter((s) => !s.ok).map((s) => `⛔ ${s.name} — ${s.note}`).join("\n");
        return send(env, chatId, `<b>Free SMS 站点（导航站全集 ${SITES.length} 个）</b>\n\n<b>可直接用 7 个：</b>\n${works}\n\n<b>其余 ${SITES.length - 7} 个：</b>\n${dead}`, { reply_markup: siteKB() });
      }
      const site = SITES.find((s) => s.id === id);
      const ad = ADAPTERS[id];
      if (!site || !ad) return send(env, chatId, "该站点暂不支持（需登录/被墙）。", { reply_markup: siteKB() });
      try {
        const items = await ad.list();
        return send(env, chatId, fmtSiteList(site, items), { reply_markup: phoneKB(id, items) });
      } catch (e) {
        return send(env, chatId, `抓取失败：${esc(String(e).slice(0, 160))}`, { reply_markup: siteKB() });
      }
    }

    if (act === "r") {
      const siteId = parts[1];
      const slug = parts.slice(2).join(":");
      const site = SITES.find((s) => s.id === siteId);
      const ad = ADAPTERS[siteId];
      if (!ad) return send(env, chatId, "站点不可用。");
      try {
        const res = await ad.read(slug);
        return send(env, chatId, fmtMsgs(site, res), {
          reply_markup: { inline_keyboard: [[{ text: "🔄 刷新", callback_data: `r:${siteId}:${slug}` }, { text: "⬅️ 返回", callback_data: "s:__all" }]] },
        });
      } catch (e) {
        return send(env, chatId, `读取失败：${esc(String(e).slice(0, 160))}`);
      }
    }
    return;
  }

  const msg = up.message || up.edited_message;
  if (!msg) return;
  const chatId = msg.chat.id;
  if (String(msg.from?.id) !== String(env.OWNER_ID)) return send(env, chatId, "🔒 私有机器人，仅主人可用。");

  const text = (msg.text || "").trim();
  const num = text.replace(/\D/g, "");
  if (/^\d{7,15}$/.test(num)) {
    for (const s of SITES.filter((x) => x.ok)) {
      const ad = ADAPTERS[s.id];
      if (!ad) continue;
      try {
        const items = await ad.list();
        const hit = items.find((it) => (it.phone || "").replace(/\D/g, "").endsWith(num.slice(-6)) || String(it.slug).includes(num.slice(-6)));
        if (hit) return send(env, chatId, fmtMsgs(s, await ad.read(hit.slug)));
      } catch {}
    }
    return send(env, chatId, "没找到这个号。");
  }

  return send(
    env,
    chatId,
    `<b>接码聚合</b>\n\n覆盖导航站 Tools→Free SMS 全部 ${SITES.length} 个站点，其中 <b>7 个可直接用</b>：\ntempsmss / tiger-sms / sms-receive.net / supercloudsms / freereceivesms / mianfeijiema / receive-sms.cc\n\n点按钮选站点，或直接发号码。`,
    { reply_markup: siteKB() }
  );
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/setup") {
      return new Response(JSON.stringify(await tg(env, "setWebhook", {
        url: url.origin + "/tg/" + env.BOT_TOKEN,
        secret_token: env.WEBHOOK_SECRET || undefined,
        allowed_updates: ["message", "callback_query"],
        drop_pending_updates: true,
      }), null, 2), { headers: { "content-type": "application/json" } });
    }
    if (url.pathname === "/health") return new Response(`ok sites=${SITES.length} adapters=${Object.keys(ADAPTERS).length}`);

    const m = url.pathname.match(/^\/tg\/(.+)$/);
    if (!m || request.method !== "POST") return new Response("nf", { status: 404 });
    if (m[1] !== env.BOT_TOKEN) return new Response("forbidden", { status: 403 });
    if (env.WEBHOOK_SECRET && request.headers.get("x-telegram-bot-api-secret-token") !== env.WEBHOOK_SECRET) {
      return new Response("forbidden", { status: 403 });
    }
    let up;
    try { up = await request.json(); } catch { return new Response("bad", { status: 400 }); }
    ctx.waitUntil(handle(env, up).catch((e) => console.error("ERR", String(e))));
    return new Response("ok");
  },
};
