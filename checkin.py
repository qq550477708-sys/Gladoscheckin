import requests
import json
import os

# -------------------------------------------------------------------------------------------
# github workflows
# -------------------------------------------------------------------------------------------
if __name__ == '__main__':
    # PushPlus token 申请地址 https://www.pushplus.plus/
    # 替换原 SENDKEY 为 PUSHPLUS_TOKEN（保持兼容也可继续使用 SENDKEY）
    pushplus_token = os.environ.get("PUSHPLUS_TOKEN", os.environ.get("SENDKEY", ""))

    # 推送内容
    title = ""
    success, fail, repeats = 0, 0, 0        # 成功账号数量 失败账号数量 重复签到账号数量
    context = ""

    # glados账号cookie 直接使用数组 如果使用环境变量需要字符串分割一下
    cookies_str = os.environ.get("COOKIES", "")
    cookies = cookies_str.split("&") if cookies_str else []  # 修复空字符串分割的潜在问题

    if cookies and cookies[0] != "":
        check_in_url = "https://glados.space/api/user/checkin"        # 签到地址
        status_url = "https://glados.space/api/user/status"          # 查看账户状态

        referer = 'https://glados.space/console/checkin'
        origin = "https://glados.space"
        useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
        payload = {
            'token': 'glados.one'
        }
        
        for cookie in cookies:
            if not cookie:  # 跳过空cookie
                continue
            try:
                checkin = requests.post(
                    check_in_url, 
                    headers={
                        'cookie': cookie, 
                        'referer': referer, 
                        'origin': origin,
                        'user-agent': useragent, 
                        'content-type': 'application/json;charset=UTF-8'
                    }, 
                    data=json.dumps(payload),
                    timeout=10  # 添加请求超时
                )
                state = requests.get(
                    status_url, 
                    headers={
                        'cookie': cookie, 
                        'referer': referer, 
                        'origin': origin, 
                        'user-agent': useragent
                    },
                    timeout=10  # 添加请求超时
                )
            except requests.exceptions.RequestException as e:
                email = ""
                message_status = f"请求异常: {str(e)}"
                message_days = "error"
                fail += 1
                context += "账号: " + email + ", P: 0, 剩余: " + message_days + " | " + message_status + "\n"
                continue

            message_status = ""
            points = 0
            message_days = ""
            
            if checkin.status_code == 200:
                # 解析返回的json数据
                try:
                    result = checkin.json()
                except json.JSONDecodeError:
                    result = {}
                # 获取签到结果
                check_result = result.get('message', '解析失败')
                points = result.get('points', 0)

                # 获取账号当前状态
                try:
                    state_result = state.json()
                except json.JSONDecodeError:
                    state_result = {'data': {}}
                # 获取剩余时间
                try:
                    leftdays = int(float(state_result.get('data', {}).get('leftDays', 0)))
                except (ValueError, TypeError):
                    leftdays = None
                # 获取账号email
                email = state_result.get('data', {}).get('email', '未知账号')
                
                print(check_result)
                if "Checkin! Got" in check_result:
                    success += 1
                    message_status = "签到成功，会员点数 + " + str(points)
                elif "Checkin Repeats!" in check_result:
                    repeats += 1
                    message_status = "重复签到，明天再来"
                else:
                    fail += 1
                    message_status = "签到失败，请检查..."

                message_days = f"{leftdays} 天" if leftdays is not None else "error"
            else:
                email = "未知账号"
                message_status = f"签到请求失败，状态码: {checkin.status_code}"
                message_days = "error"
                fail += 1

            context += f"账号: {email}, P: {str(points)}, 剩余: {message_days} | {message_status}\n"

        # 推送内容 
        title = f'Glados 签到结果: 成功{success},失败{fail},重复{repeats}'
        print("Send Content:" + "\n", context)
        
    else:
        # 推送内容 
        title = f'# 未找到有效 cookies!'
        context = "请检查 COOKIES 环境变量配置是否正确"

    print("pushplus_token:", pushplus_token)
    print("cookies:", cookies)
    
    # 推送消息：PushPlus 实现
    # 未设置 pushplus_token 则不进行推送
    if not pushplus_token:
        print("Not push (未配置 PushPlus Token)")
    else:
        # PushPlus 接口地址
        pushplus_url = "http://www.pushplus.plus/send"
        # 构造推送参数
        push_data = {
            "token": pushplus_token,
            "title": title,
            "content": context,
            "template": "txt"  # 文本格式，可选：html、markdown、txt
        }
        try:
            # 发送推送请求
            response = requests.post(
                pushplus_url,
                json=push_data,  # 直接使用 json 参数，自动序列化并设置 Content-Type
                timeout=15
            )
            response.raise_for_status()  # 抛出 HTTP 错误状态码异常
            push_result = response.json()
            if push_result.get("code") == 200:
                print("PushPlus 推送成功")
            else:
                print(f"PushPlus 推送失败: {push_result.get('msg', '未知错误')}")
        except requests.exceptions.RequestException as e:
            print(f"PushPlus 推送请求异常: {str(e)}")
