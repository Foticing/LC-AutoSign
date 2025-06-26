# 📬 嘉立创自动签到脚本

使用此 Python 脚本可以自动为多个嘉立创账号完成每日签到任务，并通过 [Server 酱](https://sct.ftqq.com/)推送签到结果至微信。

---

## ✨ 项目功能

* ✅ 支持 **多个账号并发签到**
* 🎁 自动判断是否为**第七天签到**并领取额外金豆
* 💰 获取并显示当前账号金豆余额
* 📊 将账号按通知 `SendKey` 分组，分组推送签到结果
* 📲 使用 **Server 酱** 实时推送签到通知到微信

---

## 🔧 使用前准备

### 1️⃣ 获取 AccessToken

1. 打开 [嘉立创官网](https://m.jlc.com)
2. 登录账号，按 `F12` 打开浏览器开发者工具
3. 在「Network」中找到任意请求
4. 查看请求头 Header 中的 `X-JLC-AccessToken`，复制其值
5. 多个账号用英文逗号 `,` 分隔

> 示例：

```bash
TOKEN_LIST="token1,token2,token3"
```

### 2️⃣ 获取 SendKey（Server 酱）

1. 打开 [Server 酱官网](https://sct.ftqq.com/)
2. 注册并登录后，进入「发送通道」页面
3. 创建通知通道并获取 `SendKey`
4. 多个账号用英文逗号 `,` 分隔，**数量需与 TOKEN\_LIST 一一对应**

> 示例：

```bash
SEND_KEY_LIST="key1,key2,key3"
```

---

## ⚙️ 环境变量配置

支持通过环境变量传参，适用于定时任务部署、云函数等场景：

```bash
export TOKEN_LIST="token1,token2"
export SEND_KEY_LIST="sendkey1,sendkey2"
```

也可通过 `.env` 文件或 CI/CD 系统配置界面进行设置：

```
TOKEN_LIST=token1,token2
SEND_KEY_LIST=sendkey1,sendkey2
```

---

## ⚙️ 配置说明

### GitHub Actions 配置

1. Fork 本仓库
2. 进入仓库 Settings → Secrets → Actions
3. 添加以下 Secrets：

| 变量名             | 示例值           | 说明               |
| --------------- | ------------- | ---------------- |
| TOKEN\_LIST     | token1,token2 | 多个 token 用英文逗号分隔 |
| SEND\_KEY\_LIST | key1,key2     | 与 token 一一对应     |

### 本地运行配置

创建 `.env` 文件：

```ini
TOKEN_LIST=your_token1,your_token2
SEND_KEY_LIST=your_key1,your_key2
```

---

## 📋 执行流程

1. 自动签到获取金豆
2. 检查是否为第七天签到
3. 查询当前金豆余额并推送

---

## ⏱️ GitHub Actions 定时运行

### 创建 `.github/workflows/jlc-signin.yml`

```yaml
name: JLC Auto Sign

on:
  schedule:
    - cron: '0 */6 * * *'  # 每 6 小时执行一次，UTC 时间

  workflow_dispatch:

jobs:
  sign:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout
      uses: actions/checkout@v3

    - name: Run Sign Script
      env:
        TOKEN_LIST: ${{ secrets.TOKEN_LIST }}
        SEND_KEY_LIST: ${{ secrets.SEND_KEY_LIST }}
      run: |
        python main.py
```

---

## 📄 License

本项目遵循 MIT License，欢迎自由使用和修改。
