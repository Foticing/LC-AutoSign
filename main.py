# -*- coding: UTF-8 -*-
import requests
import os
import json
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== 通用脱敏函数 ==========
def mask_account(account):
    """账号脱敏显示，如 1083978A -> 1xxxxx8A"""
    if not account or len(account) < 3:
        return account
    return account[:1] + "xxxxx" + account[-2:]

def mask_json_sensitive(data):
    """递归地脱敏 JSON 中的敏感字段，如 customerCode、integralVoucher"""
    if isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            if k == "customerCode" and isinstance(v, str):
                new_data[k] = v[:1] + "xxxxx" + v[-2:]
            elif k == "integralVoucher":
                new_data[k] = "****"  # 金豆数量隐藏
            else:
                new_data[k] = mask_json_sensitive(v)
        return new_data
    elif isinstance(data, list):
        return [mask_json_sensitive(i) for i in data]
    else:
        return data

# ========== 主签到逻辑 ==========
def sign_and_get_beans(customer_code, send_key):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

    # 签到
    sign_url = "https://jlcapi.jlc.com/signin/v1/userSign"
    data = {"customerCode": customer_code}
    try:
        response = requests.post(sign_url, headers=headers, json=data, timeout=10)
        sign_result = response.json()
    except RequestException as e:
        print(f"❌ [账号{mask_account(customer_code)}] 签到失败: {e}")
        return
    except Exception:
        print(f"❌ [账号{mask_account(customer_code)}] 签到响应解析失败")
        return

    # 打印脱敏后的 JSON 日志
    print(f"🔍 [账号{mask_account(customer_code)}] 签到响应JSON:")
    print(json.dumps(mask_json_sensitive(sign_result), indent=2, ensure_ascii=False))

    # 获取金豆信息
    beans_url = "https://jlcapi.jlc.com/signin/v1/userIntegral"
    try:
        bean_resp = requests.post(beans_url, headers=headers, json=data, timeout=10)
        bean_result = bean_resp.json()
    except RequestException as e:
        print(f"❌ [账号{mask_account(customer_code)}] 金豆查询失败: {e}")
        return

    print(f"🔍 [账号{mask_account(customer_code)}] 金豆响应JSON:")
    print(json.dumps(mask_json_sensitive(bean_result), indent=2, ensure_ascii=False))

    # ========== 微信通知（这里保留真实值） ==========
    integral = bean_result.get("data", {}).get("integralVoucher", "未知")
    msg = f"账号 {customer_code} 签到成功 🎉 当前金豆：{integral}"

    if send_key:
        wx_push(send_key, "嘉立创签到通知", msg)
    else:
        print("⚠️ 未配置 Server酱 SendKey，跳过推送")

# ========== 微信通知 ==========
def wx_push(send_key, title, content):
    url = f"https://sctapi.ftqq.com/{send_key}.send"
    try:
        requests.post(url, data={"title": title, "desp": content}, timeout=10)
        print(f"📢 微信推送成功：{title}")
    except Exception as e:
        print(f"❌ 微信推送失败: {e}")

# ========== 并发执行 ==========
def main():
    token_list = os.getenv("TOKEN_LIST", "").replace(",", "\n").splitlines()
    send_key_list = os.getenv("SEND_KEY_LIST", "").replace(",", "\n").splitlines()

    token_list = [x.strip() for x in token_list if x.strip()]
    send_key_list = [x.strip() for x in send_key_list if x.strip()]

    if not token_list:
        print("❌ 未检测到 TOKEN_LIST")
        return

    with ThreadPoolExecutor(max_workers=len(token_list)) as executor:
        futures = []
        for i, token in enumerate(token_list):
            send_key = send_key_list[i % len(send_key_list)] if send_key_list else None
            futures.append(executor.submit(sign_and_get_beans, token, send_key))

        for future in as_completed(futures):
            future.result()

if __name__ == "__main__":
    main()
