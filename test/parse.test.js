const fs = require("fs");
const src = fs.readFileSync(__dirname + "/../src/worker.js", "utf8");

// 抽出纯函数部分做离线测试（去掉 export default 与 tg 相关副作用）
const body = src
  .slice(src.indexOf("const ENT ="), src.indexOf("/* ---------------- 业务"))
  .replace(/^async function httpGet[\s\S]*?^}\n/m, "");

const scope = {};
const fn = new Function(body + "\nreturn {parseList, parseMessages, stripTags, decode};");
const { parseList, parseMessages } = fn();

function t(label, file) {
  const html = fs.readFileSync(__dirname + "/" + file, "utf8");
  if (label === "list") {
    const items = parseList(html);
    console.log("LIST count:", items.length);
    items.slice(0, 6).forEach((i) => console.log(" ", i.phone, "|", i.badges.join(","), "|", i.services.join("/"), "|", i.last));
    const bad = items.filter((i) => !/^\+\d{7,15}$/.test(i.phone));
    console.log("  异常号码:", bad.length);
  } else {
    const p = parseMessages(html);
    console.log("NUM meta:", JSON.stringify(p.meta), "msgs:", p.msgs.length);
    p.msgs.slice(0, 3).forEach((m) => console.log("  ", m.time, "|", m.from, "|", m.body.slice(0, 90), "| code:", m.codes[0] || m.digits[0] || "-"));
  }
}
t("list", "h1.html");
t("list", "us.html");
t("num", "n1.html");
t("num", "uk1.html");
t("num", "tm.json");
