import urllib.request
import urllib.parse
import json
import re

login_url = "https://login.360.cn/"
headers = {
    "accept": "*/*",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "__guid=6974633.3210292762249625600.1772445125551.4946",
    "referer": "https://my.jia.360.cn/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
body = "src=pcw_ipcam_live&from=pcw_ipcam_live&charset=UTF-8&requestScema=https&quc_sdk_version=7.3.5&quc_sdk_name=jssdk&mid=&asc=&mname=&o=sso&m=login&lm=0&captFlag=1&rtype=data&validatelm=0&isKeepAlive=1&captchaApp=i360&userName=18219951345&smDeviceId=&captcha=&type=normal&loginType=0&captchaType=&appid=&account=18219951345&password=26o6wvgw301464438w7ie9kl835b217ecd3d3c8760f0087562lggfw&tk=&x=d373b8f34226ad42153285514b92dad6&token=b5aea89f6ec7c689&proxy=https%3A%2F%2Fmy.jia.360.cn%2Fpsp_jump.html&callback=&func=" # removed jsonp callback to get pure json if possible

req = urllib.request.Request(login_url, data=body.encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req) as res:
        text = res.read().decode('utf-8')
        print("LOGIN RESPONSE:")
        print(text[:1000])
except Exception as e:
    print(e)
