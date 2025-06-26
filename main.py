# -*- coding: UTF-8 -*-

import requests
import os
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

# 从 GitHub Secrets 获取配置
TOKEN_LIST = os.getenv('TOKEN_LIST', '')
SEND_KEY_LIST = os.getenv('SEND_KEY_LIST', '')

# 接口配置
url = 'https://m.jlc.com/api/activity/sign/signIn?source=3'
gold_bean_url = "https://m.jlc.com/api/appPlatform/center/assets/selectPersonalAssetsInfo"

# 推送通知函数
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

# 单个账号签到逻辑
def sign_in(access_token):
    headers = {
        'X-JLC-AccessToken': access_token,
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) JlcMobileApp',
    }
    try:
        # 执行签到请求
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
        
        # 处理签到结果
        if status > 0:
            if gain_num is not None:
                return f"✅ 账号(尾号{access_token[-4:]})：签到成功，获得{gain_num}个金豆，当前金豆总数：{integral_voucher}"
            else:
                # 第七天特殊处理
                response_receive = requests.get("https://m.jlc.com/api/activity/sign/receiveVoucher", headers=headers)
                if response_receive.json().get("success"):
                    return f"🎉 账号(尾号{access_token[-4:]})：第七天签到成功，领取8个金豆，当前金豆总数：{integral_voucher + 8}"
                else:
                    return f"⚠️ 账号(尾号{access_token[-4:]})：第七天签到失败"
        else:
            return f"❌ 账号(尾号{access_token[-4:]})：签到失败，状态码：{status}"

    except RequestException:
        return f"❌ 账号(尾号{access_token[-4:]})：网络请求失败"
    except KeyError:
        return f"❌ 账号(尾号{access_token[-4:]})：数据解析失败"
    except Exception:
        return f"❌ 账号(尾号{access_token[-4:]})：未知错误"

# 主函数
def main():
    # 解析环境变量
    if not TOKEN_LIST or not SEND_KEY_LIST:
        print("❌ TOKEN_LIST 或 SEND_KEY_LIST 环境变量未设置")
        return
        
    AccessTokenList = TOKEN_LIST.split(',')
    SendKeyList = SEND_KEY_LIST.split(',')
    
    # 确保两个列表长度一致
    min_length = min(len(AccessTokenList), len(SendKeyList))
    AccessTokenList = AccessTokenList[:min_length]
    SendKeyList = SendKeyList[:min_length]
    
    # 按 SendKey 分组
    task_groups = defaultdict(list)
    for access_token, send_key in zip(AccessTokenList, SendKeyList):
        task_groups[send_key].append(access_token)
    
    # 为每个分组创建线程池
    with ThreadPoolExecutor(max_workers=min_length) as executor:
        # 存储每个分组的结果
        group_results = {}
        
        # 提交并处理所有任务
        for send_key, tokens in task_groups.items():
            futures = [executor.submit(sign_in, token) for token in tokens]
            results = [future.result() for future in futures]
            group_results[send_key] = results
        
        # 发送组合通知
        for send_key, results in group_results.items():
            content = "\n\n".join(results)
            print(f"📤 准备发送通知给 SendKey: {send_key[:5]}...")
            response = send_msg_by_server(send_key, "嘉立创签到汇总", content)
            
            if response and response.get('code') == 0:
                print(f"✅ 通知发送成功！消息ID: {response.get('data', {}).get('pushid', '')}")
            else:
                print(f"❌ 通知发送失败！错误: {response.get('message') if response else '未知错误'}")

if __name__ == '__main__':
    main()
