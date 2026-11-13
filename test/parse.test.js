// 离线自检：校验 worker.js 能被加载、关键纯函数行为正确、无硬编码密钥
// 用法：node test/parse.test.js
const fs = require("fs");
const path = require("path");
const os = require("os");

const ROOT = path.join(__dirname, "..");
const src = fs.readFileSync(path.join(ROOT, "worker.js"), "utf8");

let fail = 0;
const ok = (name, cond, extra = "") => {
  if (cond) console.log(`✅ ${name}`);
  else { console.log(`❌ ${name} ${extra}`); fail++; }
};

// 1. 结构检查
ok("有 export default", /export default\s*\{/.test(src));
ok("有 fetch 入口", /async\s+fetch\s*\(/.test(src));
ok("有 ADAPTERS", /const ADAPTERS\s*=/.test(src));
ok("有 SITES", /const SITES\s*=/.test(src));

// 2. 无硬编码密钥 / 真实子域
[
  [/ghp_[A-Za-z0-9]{20,}/, "GitHub token"],
  [/\d{8,10}:AA[A-Za-z0-9_-]{20,}/, "Telegram bot token"],
  [/pingmike\d*\.workers\.dev/, "真实 Workers 子域"],
  [/CLOUDFLARE_API_TOKEN\s*=\s*['"][^'"]+/, "硬编码 CF token"],
].forEach(([re, label]) => ok(`无硬编码 ${label}`, !re.test(src)));

// 3. 纯函数行为（把 worker.js 当 ES 模块跑）
const modPath = path.join(os.tmpdir(), `smsbot_check_${process.pid}.mjs`);
fs.writeFileSync(modPath, src + "\nexport { agoToSec, decodeEnt, plain, sortByActivity };\n");

(async () => {
  let m;
  try {
    m = await import("file://" + modPath);
  } catch (e) {
    console.log("❌ worker.js 无法加载:", e.message);
    fs.unlinkSync(modPath);
    process.exit(1);
  }

  ok("agoToSec('just now') === 0", m.agoToSec("just now") === 0, String(m.agoToSec("just now")));
  ok("agoToSec('2 hours ago') === 7200", m.agoToSec("2 hours ago") === 7200);
  ok("agoToSec('') === Infinity", m.agoToSec("") === Infinity);
  ok("decodeEnt 解 &amp;", m.decodeEnt("a &amp; b") === "a & b");
  ok("plain 去标签", m.plain("<b>hi</b>").trim() === "hi");

  const sorted = m.sortByActivity([
    { phone: "+1", lastSms: "3 hours ago" },
    { phone: "+2", lastSms: "just now" },
    { phone: "+3", lastSms: "5 minutes ago" },
  ]);
  ok("sortByActivity 把 just now 排最前", sorted[0].phone === "+2", JSON.stringify(sorted.map((x) => x.phone)));

  fs.unlinkSync(modPath);
  console.log(fail === 0 ? "\n全部通过" : `\n${fail} 项失败`);
  process.exit(fail === 0 ? 0 : 1);
})();
