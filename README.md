# sms-tg-bot — 聚合免费接码站点的 Telegram 机器人（Cloudflare Workers）

一个跑在 Cloudflare Workers 上的单人 Telegram 机器人，把导航站 Free SMS 分区里的
免费接码站点聚合成一个入口：点站点 → 选号码 → 直接看验证码，不用在十几个网站之间来回跳。
默认只允许一个 Telegram 账号使用。

整个仓库只有一个核心文件 **`worker.js`**，复制粘贴到 Cloudflare 控制台即可部署，不需要 npm、不需要 wrangler。

## 部署教程（控制台手动操作，约 5 分钟）

### 第 1 步：建一个 Bot 拿 Token

1. 在 Telegram 里找 [@BotFather](https://t.me/BotFather)，发 `/newbot`
2. 按提示起名，拿到形如 `123456:ABC-DEF...` 的 **Bot Token**（令牌）
3. 记下你的 **Telegram 数字 ID**（找 [@userinfobot](https://t.me/userinfobot) 发任意消息即可看到）

### 第 2 步：创建 Worker

1. 打开 [Cloudflare Dashboard](https://dash.cloudflare.com/) → **Workers & Pages** → **Create** → **Worker** → 随便起个名字（如 `sms-tg-bot`）→ **Deploy**
2. 点 **Edit code**（编辑代码），把 `worker.js` 的内容**全部选中、全部粘贴**进去，覆盖默认代码
3. 右上角 **Deploy**（部署）保存

### 第 3 步：设置环境变量（密钥）

保持同一个 Worker 页面，点 **Settings**（设置）→ **Variables**（变量）：

| 变量 | 必填 | 值 |
|---|---|---|
| `BOT_TOKEN` | 是 | 第 1 步拿到的 `123456:ABC...` |
| `OWNER_ID` | 是 | 你的 Telegram 数字 ID（只允许这一个人用） |
| `WEBHOOK_SECRET` | **是** | 自己生成一串（如 `openssl rand -hex 24`）。不填则 `/setup` 直接返回 500，无法注册 webhook |

点 **Encrypt**（加密）保存三个变量；然后 **Deploy** 使变量生效。

### 第 4 步：注册 webhook（把 Telegram 的消息转发给 Worker）

**直接在浏览器打开这一行就完成了**（把 `WEBHOOK_SECRET` 换成第 3 步里你自己设的那串）：

```
https://<你的worker子域>.workers.dev/setup/<你的WEBHOOK_SECRET>
```

页面显示 `✅ 注册成功，现在可以给机器人发 /start 了` 就好了。

> `WEBHOOK_SECRET` 就是这步的口令，写在路径里别人猜不到。没配 Secret 打开会提示先配置；
> 口令写错会返回 403。

注册后 Telegram 把消息推到 `https://<你的worker子域>.workers.dev/tg/<BOT_TOKEN>`，
路径带 token + `x-telegram-bot-api-secret-token` 双边校验，其他人碰不到。

### 第 5 步：用起来

给机器人发 `/start`，点站点按钮 → 选号码 → 看验证码。

---

## 架构

```
Telegram  ──webhook──▶  Worker (worker.js)
                          │
                          ├─ 鉴权：路径含 BOT_TOKEN + secret_token 头，缺一 403
                          ├─ 白名单：from.id !== OWNER_ID → 拒（私有机器人）
                          │
                          ▼
                    ADAPTERS[site].list()  ──▶ 号码列表（带最近短信时间，按活跃度排序）
                    ADAPTERS[site].read()  ──▶ 短信正文 + 解出的验证码
                          │
                          ▼
                   各接码站点（直连 HTTP，无浏览器）
```

Worker 内缓存 45~60 秒，避免重复打站。免费版 50 subrequest 上限是硬约束：
列表页只抓 1 次，读码时才多抓 1~2 次，不在列表阶段逐号抓落地页。

## 支持状态

| 站点 | 列表 | 读码 | 说明 |
|---|---|---|---|
| `tempsmss` | ✅ | ✅ | 全解密，验证码直出 |
| `tiger-sms` | ✅ | ✅ | 带 Active 徽章与 Last SMS 时间 |
| `freereceivesms` | ✅ | ✅ | 完整国际号码 |
| `supercloudsms` | ✅ | ✅ | |
| `mianfeijiema` | ✅ | ✅ | 18 个号，验证码带 `data-clipboard-text` 明文，15/15 解出 |
| `receive-sms.cc` | ✅ | ✅ | 24 个号，`div.con` 明文，如 `Account: 786132` / `Verification code: 6914` |
| `sms-receive.net` | ✅ | ⚠️ | 列表 85 个号，但读码接口对现有号码全返 `[]` |
| 其余 22 个 | — | — | CF 拦截 / 需登录 / 纯 JS 渲染 / 需注册，按钮里不出现 |

站点清单来自导航站 Tools → Free SMS 分区，共 30 个，其中 8 个可直接用；不可用的也保留在
「全部站点状态」里并注明原因，方便日后上游恢复时快速接回。

### tempsmss 验证码解密

静态页面 HTML 里的验证码本身是 `••••••`（不是前端遮挡），真码只在
`POST https://tempsmss.com/wp-admin/admin-ajax.php` 的
`sms_receiver_get_messages` 响应里，以 `<span class="sms-spoiler" data-c="...">`
存放，`data-c` 为 base64。

`read()` 做的事：

1. 抓号码页，取 `data-post`（post_id）与 `security`（nonce）
2. POST 上面那个接口，拿到含明文的 HTML
3. 把所有 `sms-spoiler` 的 `data-c` 做 base64 解码
4. 正文里还残留 `•` 就标记解密失败，宁可不显示也不送假数据

验证码识别支持纯数字 4~8 位，也支持 `732-344` 这类分段格式（WhatsApp 用）。

## 运维

```bash
# 看实时日志（Dashboard → Worker → Logs，或命令行：
npx wrangler@latest tail <worker名>

# 健康检查（返回站点数与适配器数）
curl -s "https://<你的worker子域>.workers.dev/health"
# → ok sites=30 adapters=8

# 重设 webhook（改了 WEBHOOK_SECRET 后浏览器打开这个地址）
# https://<你的worker子域>.workers.dev/setup/<你的WEBHOOK_SECRET>

# 本地自检（仓库内，不需要部署）
node test/parse.test.js   # 结构 + 纯函数 + 密钥扫描
node test/auth.test.js    # /setup、/tg 鉴权、OWNER_ID 白名单
```

### 机器人不回复怎么办

先看 Logs（或 `wrangler tail`）。最常见原因是**免费版 50 subrequest 上限**被撑爆，
表现是日志无异常但消息不发出去 —— 检查是不是在列表阶段就逐号抓了落地页。

### 验证码显示成 •••••• 怎么办

说明 ajax 接口那条路没通（nonce 过期或站点改版）。直接抓页面看 `sms-spoiler` 是否还在，
`data-c` 是不是 base64。若站点改成别的编码，`read()` 里的 `atob` 要跟着换。

## 注意事项

- **只给一个人用**：`OWNER_ID` 之外的用户会被直接拒绝，这是设计而非缺陷。
- **免费版 50 subrequest 上限**是硬约束，新增适配器时别在 `list()` 里逐号发请求。
- 部分站点用 TLS 指纹拦截（如 `sms-online.co`：`curl` 200 但 `node fetch` / Workers 403），
  这类站点纯 HTTP 绕不过去，已在清单里标为不可用，不做假数据兜底。
- 号码是公共号，验证码可能被别人读到；同一个号可能被要求 KYC（要姓名/邮箱），换号即可。
- 站点改版会导致解析失效，`test/parse.test.js` 可用来快速复测。
- 本 Worker 不收集、不存储任何用户数据；缓存只在 Worker 内存里，随 isolate 回收。
- 密钥（`BOT_TOKEN` / `OWNER_ID` / `WEBHOOK_SECRET`）只通过 Cloudflare 控制台的
  Variables（Encrypt 加密）写入，不进仓库、不进代码。

## 致谢 (Acknowledgements)

| 项目 | 在本项目里干什么活 |
|---|---|
| [Cloudflare Workers](https://workers.cloudflare.com/) | 运行环境与 webhook 入口 |
| [Telegram Bot API](https://core.telegram.org/bots/api) | 机器人消息与回调按钮 |
| [nav.eooce.com](https://nav.eooce.com/) | Free SMS 站点清单来源 |

## 免责声明 (Disclaimer)

本项目仅供学习、研究与个人技术实验使用，请勿用于违反所访问站点服务条款或当地法律的行为。

与上述任何接码站点、Telegram、Cloudflare 均无关联、无背书（not affiliated or endorsed）。

各站点可用性完全取决于对方策略（改版、加墙、限流、下线），本项目不担保持续可用或稳定。

如果需要稳定的验证码接收通道，请使用正规付费短信服务的官方套餐。

使用产生的一切风险由使用者自行承担；软件本体按 LICENSE 提供，AS IS。

## License

[MIT](./LICENSE) © 2026 [pingmike2](https://github.com/pingmike2)