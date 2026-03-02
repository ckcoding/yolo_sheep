import requests
import json

# 1. 目标接口：就是您最早抓到的那个报警列表接口
# (请替换为您抓包里的那个长链接，如果不记得了，请抓取 "点击看家/消息" 时的链接)
url = "https://ipcmaster-bj-7days-v4.beijing.xstore.qihu.com/ipc_master/GetEventList..." 

# 2. 构造“伪造”的身份头
headers = {
    "User-Agent": "SmartHome/2.23.0 (iPhone; iOS 18.2; Scale/3.00)",
    "Content-Type": "application/x-www-form-urlencoded",
    # 关键尝试1：直接用 sid
    "Cookie": "sid=90F7CE2925BAE6C417578E7775993E22; u=211164673; k=4f284803bd0966cc24fa8683a34afc6e"
}

# 3. 发送请求
try:
    # 这里的 data 参数可能需要根据实际接口调整，通常 GET 请求不需要 data
    response = requests.get(url, headers=headers, verify=False)
    
    print(f"状态码: {response.status_code}")
    print("返回内容:")
    print(response.text)
    
    if "snapUrl" in response.text:
        print("\n✅ 成功！Token 有效，可以接入 Home Assistant 了！")
    else:
        print("\n❌ 失败，可能是 Cookie 格式不对，或者 URL 已过期。")

except Exception as e:
    print(e)