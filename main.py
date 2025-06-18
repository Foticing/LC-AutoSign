# -*- coding: UTF-8 -*-
import os
import requests
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor, as_completed

# 接口配置
url = 'https://m.jlc.com/api/activity/sign/signIn?source=3'
gold_bean_url = "https://m.jlc.com/api/appPlatform/center/assets/selectPersonalAssetsInfo"

# 从环境变量中读取并解析多个 AccessToken 和 SendKey（以换行符或逗号分隔）
AccessTokenList = os.getenv("ACCESS_TOKEN_LIST", "").replace(',', '\n').splitlines()
SendKeyList = os.getenv("SEND_KEY_LIST", "").replace(',', '\n').splitlines()

# 过滤空值（防止尾部多行空白）
AccessTokenList = [t.strip() for t in AccessTokenList if t.strip()]
SendKeyList = [k.strip() for k in SendKeyList if k.strip()]

# 合并用户和通知Key，检查哪些用户共享相同的通知Key
user_send_key_map = {}
for i, send_key in enumerate(SendKeyList):
    if send_key not in user_send_key_map:
        user_send_key_map[send_key] = []
    user_send_key_map[send_key].append(AccessTokenList[i])

print(f"用户和通知Key的映射关系: {user_send_key_map}")

# 推送通知函数
def send_msg_by_server(send_key, title, content):
    push_url = f'https://sctapi.ftqq.com/{send_key}.send'
    data = {
        'text': title,
        'desp': content
    }
    try:
        response = requests.post(push_url, data=data).json()
        if response.get('code') == 0:
            print(f"推送成功！[{title}]")
        else:
            print(f"推送失败！[{title}] 原因：{response.get('message')}")
    except RequestException as e:
        print(f"推送失败，网络错误：[{title}] 错误：{e}")

# 单个账号签到逻辑
def sign_in(access_token):
    headers = {
        'X-JLC-AccessToken': access_token,
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) JlcMobileApp',
    }
    try:
        response = requests.get(url, headers=headers)
        response_bean = requests.get(gold_bean_url, headers=headers)

        response.raise_for_status()
        response_bean.raise_for_status()

        result = response.json()
        result_bean = response_bean.json()

        data = result.get('data', {})
        gain_num = data.get('gainNum')
        status = data.get('status')
        integral_voucher = result_bean['data']['integralVoucher']

        if status > 0:
            if gain_num is not None:
                return f"金豆数量: {gain_num}, 当前金豆总数: {integral_voucher}"
            else:
                extra = requests.get("https://m.jlc.com/api/activity/sign/receiveVoucher", headers=headers).json()
                if extra.get("success"):
                    return f"第七天签到，领取8个金豆, 当前金豆总数: {integral_voucher + 8}"
        return "未获取到金豆或状态异常"
    except RequestException as e:
        return f"请求失败：{e}"
    except KeyError as e:
        return f"响应解析失败，缺少键：{e}"
    except Exception as e:
        return f"未知错误：{e}"

# 主函数
def main():
    print("----- 自动化任务开始 -----")
    for send_key, token_list in user_send_key_map.items():
        result_list = []

        with ThreadPoolExecutor(max_workers=len(token_list)) as executor:
            future_to_token = {
                executor.submit(sign_in, token): token for token in token_list
            }

            for future in as_completed(future_to_token):
                token = future_to_token[future]
                try:
                    result = future.result()
                    result_list.append(f"账号 {token[:6]}...：{result}")
                except Exception as e:
                    result_list.append(f"账号 {token[:6]}... 发生异常：{e}")

        summary = "\n".join(result_list)
        print(f"\n[通知内容汇总]\n{summary}")
        send_msg_by_server(send_key, "嘉立创签到结果", summary)

    print("----- 自动化任务结束 -----")

if __name__ == '__main__':
    main()
