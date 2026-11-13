# 贡献指南

面向要改 `worker.js` 的人（包括未来接手的 AI）。只想**用**机器人的看 README。

## 硬约束（违反直接拒）

- **零依赖**：不引入 npm 包，只用 Workers 运行时自带能力（`fetch` / `atob` / `URLSearchParams`）。
  仓库没有 `package.json`，别加。
- **免费版 50 subrequest 上限**：一次 webhook 调用内所有 `fetch` 加起来不能逼近 50。
  列表阶段只允许 1 个请求；需要逐号补全的放到 `read()` 里按需做。
- **不做假数据兜底**：解析不到就返回空并说明，不许用正则凑出看起来像验证码的东西。
  历史事故：`sms-receive.net` 的 JS 模板行 `${json[i].mesaj}` 被当成短信正文发出去过。

## 结构约定

新增站点 = 在 `SITES` 加一条 + 在 `ADAPTERS` 写两个函数：

```js
{
  list: async () => [{ phone, slug, lastSms?, active? }],   // 必须是个数组
  read: async (slug) => ({ phone, msgs: [{ from, time, body, code, masked }] })
}
```

- `list()` 里用 `sortByActivity(out)` 收尾，让最近有短信的排前面；站点没有时间信息
  就留空，**不要编造**排序依据。
- `read()` 解不出验证码时把 `masked: true` 带上，渲染层会显示「已打码，解密失败」，
  比悄悄显示 `••••••` 强。
- 站点不通就把它在 `SITES` 里标 `ok: false` 并写 `note` 说明原因，按钮里自然消失，
  但在「全部站点状态」里仍可见，方便上游恢复时接回。

## 测试

没有测试框架，靠脚本直连真实站点验证：

```bash
node test/parse.test.js    # 解析逻辑
node test/e2e.js           # 端到端（会真打站点，拦截 Telegram API）
python3 test/probe_all.py  # 批量探测站点可达性
```

调试时想看某站真实返回，先 `curl -A 'Mozilla/5.0 Chrome/131' <url>` 存到本地再分析，
别靠猜 HTML 结构。注意 `curl` 能过不代表 Worker 能过 —— 有的站按 TLS 指纹拦
（`sms-online.co` 就是：curl 200，`node fetch` 403）。

## PR 规范

- 一个 PR 一件事，标题前缀 `feat:` / `fix:` / `docs:`
- 改了适配器行为要同步更新 README 的「支持状态」表
- 提交前自己扫一遍敏感信息：

```bash
grep -rinE "password|secret|token|api[_-]?key|ghp_|workers\.dev" --include="*.js" --include="*.md" .
```

`BOT_TOKEN` / `OWNER_ID` / `WEBHOOK_SECRET` / `CLOUDFLARE_API_TOKEN` 一律走
`wrangler secret put`（或 Cloudflare 控制台 Variables）写入，任何真值都不进仓库。
仓库里只有一个文件 `worker.js`，部署方式见 README 的手动部署教程。

## 发版

改完先本地跑通解析测试，再 `npx wrangler@latest deploy`，然后
`curl -s <worker地址>/health` 确认 `sites=` 与 `adapters=` 对得上。
