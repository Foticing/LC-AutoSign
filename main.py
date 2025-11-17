# -*- coding: UTF-8 -*-

import requests
import os
import json
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

# 从 GitHub Secrets 获取配置
TOKEN_LIST = os.getenv('TOKEN_LIST', '')
SEND_KEY_LIST = os.getenv('SEND_KEY_LIST', '')

# 接口配置
url = 'https://m.jlc.com/api/activity/sign/signIn?source=3'
gold_bean_url = "https://m.jlc.com/api/appPlatform/center/assets/selectPersonalAssetsInfo"
seventh_day_url = "https://m.jlc.com/api/activity/sign/receiveVoucher"


# ======== 工具函数 ========

def mask_account(account):
    """用于打印时隐藏部分账号信息"""
    if len(account) >= 4:
        return account[:2] + '****' + account[-2:]
    return '****'


def mask_json_customer_code(data):
    """递归地脱敏 JSON 中的 customerCode 字段"""
    if isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            if k == "customerCode" and isinstance(v, str):
                new_data[k] = v[:1] + "xxxxx" + v[-2:]  # 例: 1xxxxx8A
            else:
                new_data[k] = mask_json_customer_code(v)
        return new_data
    elif isinstance(data, list):
        return [mask_json_customer_code(i) for i in data]
    else:
        return data


# ======== 推送通知 ========

def send_msg_by_server(send_key, title, content):
    push_url = f'https://sctapi.ftqq.com/{send_key}.send'
    data = {
        'text': title,
        'desp': content
    }
    try:
        response = requests.post(push_url, data=data)
        return response.json()
    except RequestException:
        return None


# ======== 单个账号签到逻辑 ========

def sign_in(access_token):
    headers = {
        'X-JLC-AccessToken': access_token,
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) '
                      'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) JlcMobileApp',
    }

    try:
        # 1. 执行签到请求
        sign_response = requests.get(url, headers=headers)
        sign_response.raise_for_status()
        sign_result = sign_response.json()

        # 2. 获取金豆信息
        bean_response = requests.get(gold_bean_url, headers=headers)
        bean_response.raise_for_status()
        bean_result = bean_response.json()

        # 获取 customerCode
        customer_code = bean_result['data']['customerCode']

        # 打印签到响应 JSON（已脱敏）
        print(f"🔍 [账号{mask_account(customer_code)}] 签到响应JSON:")
        #print(json.dumps(mask_json_customer_code(sign_result), indent=2, ensure_ascii=False))

        # 打印金豆响应 JSON（已脱敏）
        #print(f"🔍 [账号{mask_account(customer_code)}] 金豆响应JSON:")
        #print(json.dumps(mask_json_customer_code(bean_result), indent=2, ensure_ascii=False))

        # 解析数据
        data = sign_result.get('data', {})
        gain_num = data.get('gainNum')
        status = data.get('status')
        integral_voucher = bean_result['data']['integralVoucher']

        # 处理签到结果
        if status > 0:
            if gain_num is not None and gain_num != 0:
                # print(f"🎯 [账号{mask_account(customer_code)}] 今日签到完成，当前金豆：{integral_voucher}")
                return f"✅ 账号({mask_account(customer_code)})：获取{gain_num}个金豆，当前总数：{integral_voucher}"
            else:
                # 第七天特殊处理
                seventh_response = requests.get(seventh_day_url, headers=headers)
                seventh_response.raise_for_status()
                seventh_result = seventh_response.json()

                # 打印第七天响应 JSON（已脱敏）
                print(f"🔍 [账号{mask_account(customer_code)}] 第七天签到响应JSON:")
                # print(json.dumps(mask_json_customer_code(seventh_result), indent=2, ensure_ascii=False))

                if seventh_result.get("success"):
                    print(f"🎉 [账号{mask_account(customer_code)}] 第七天签到成功，领取8个金豆")
                    return f"🎉 账号({mask_account(customer_code)})：第七天签到成功，领取8个金豆，当前总数：{integral_voucher + 8}"
                else:
                    print(f"ℹ️ [账号{mask_account(customer_code)}] 第七天签到失败，无金豆获取")
                    return None
        else:
            print(f"ℹ️ [账号{mask_account(customer_code)}] 今日已签到或签到失败")
            return None

    except RequestException as e:
        print(f"❌ [账号{mask_account(customer_code)}] 网络请求失败: {str(e)}")
        return None
    except KeyError as e:
        print(f"❌ [账号{mask_account(customer_code)}] 数据解析失败: 缺少键 {str(e)}")
        return None
    except Exception as e:
        print(f"❌ [账号{mask_account(customer_code)}] 未知错误: {str(e)}")
        return None


# ======== 主函数 ========

def main():
    if not TOKEN_LIST or not SEND_KEY_LIST:
        print("❌ TOKEN_LIST 或 SEND_KEY_LIST 环境变量未设置")
        return

    AccessTokenList = TOKEN_LIST.split(',')
    SendKeyList = SEND_KEY_LIST.split(',')

    # 确保长度一致
    min_length = min(len(AccessTokenList), len(SendKeyList))
    AccessTokenList = AccessTokenList[:min_length]
    SendKeyList = SendKeyList[:min_length]

    print(f"🔧 共发现 {min_length} 个账号需要签到")

    # 按 SendKey 分组
    task_groups = defaultdict(list)
    for access_token, send_key in zip(AccessTokenList, SendKeyList):
        task_groups[send_key].append(access_token)

    print(f"📊 共分为 {len(task_groups)} 个通知组")

    # 多线程处理签到任务
    with ThreadPoolExecutor(max_workers=min_length) as executor:
        group_results = {}

        for send_key, tokens in task_groups.items():
            print(f"\n🚀 开始处理 SendKey: {send_key[:5]}... 的 {len(tokens)} 个账号")
            futures = [executor.submit(sign_in, token) for token in tokens]
            results = [f.result() for f in futures]

            valid_results = [r for r in results if r is not None]
            group_results[send_key] = valid_results

        # 推送通知
        print("\n📬 开始发送通知...")
        for send_key, results in group_results.items():
            if not results:
                print(f"⏭️ SendKey: {send_key[:5]}... 组内无金豆获取，跳过通知")
                continue

            content = "\n\n".join(results)
            print(f"📤 准备发送通知给 SendKey: {send_key[:5]}...")
            # print(f"📝 通知内容预览:\n{content[:100]}...")

            response = send_msg_by_server(send_key, "嘉立创签到汇总", content)

            if response and response.get('code') == 0:
                print(f"✅ 通知发送成功！消息ID: {response.get('data', {}).get('pushid', '')}")
            else:
                error_msg = response.get('message') if response else '未知错误'
                print(f"❌ 通知发送失败！错误: {error_msg}")


# ======== 程序入口 ========

if __name__ == '__main__':
    print("🏁 嘉立创自动签到任务开始")
    main()
    print("🏁 任务执行完毕")
