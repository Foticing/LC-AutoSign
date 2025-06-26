# 嘉立创自动签到脚本

通过此 Python 脚本可实现对嘉立创多个账号的自动签到，并通过 Server 酱推送每日金豆签到结果通知。

## ✨ 项目功能

- 支持多个嘉立创账号的并发签到
- 自动判断是否为第七天签到并领取额外金豆
- 自动获取并展示当前金豆余额
- 按照不同通知 `SendKey` 分组推送汇总结果
- 使用 Server 酱推送签到结果到微信

## 📦 使用前准备

### 1. 获取 `TOKEN_LIST`

1. 打开 [嘉立创官网](https://m.jlc.com)
2. 使用浏览器调试工具（F12）登录账户
3. 在 Network 中找到包含 `X-JLC-AccessToken` 的请求头，提取值作为 AccessToken
4. 多个账号用英文逗号 `,` 分隔

### 2. 获取 `SEND_KEY_LIST`

1. 注册并登录 [Server酱](https://sct.ftqq.com/)
2. 创建通道，获取 `SendKey`
3. 多个账号用英文逗号 `,` 分隔，需与 `TOKEN_LIST` 数量一一对应

## ⚙️ 环境变量配置

支持通过环境变量传参：

```bash
export TOKEN_LIST="access_token1,access_token2"
export SEND_KEY_LIST="send_key1,send_key2"
