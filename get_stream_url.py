import urllib.request
import urllib.parse
import json

# Cookie from the user's request
# In practice we could try to simulate login to get it, but let's test if we can just use the provided cookie segment to access the inner api list
cookie = "test_cookie_enable=null; __guid=6974633.3210292762249625600.1772445125551.4946; monitor_count=1; __quc_silent__=1; Q=u%3D%25O2%25S1%25Q7%25QN%25P5%25S4%26n%3D%25OS%25O5%25Q7%25NS%25O4%25S3%25O5%25P0PX%26le%3D%26m%3DZGtlWGWOWGWOWGWOWGWOWGWOZmD1%26qid%3D211164673%26im%3D1_t016d7ec49acf3a8452%26src%3Dpcw_ipcam_live%26t%3D1; __NS_Q=u%3D%25O2%25S1%25Q7%25QN%25P5%25S4%26n%3D%25OS%25O5%25Q7%25NS%25O4%25S3%25O5%25P0PX%26le%3D%26m%3DZGtlWGWOWGWOWGWOWGWOWGWOZmD1%26qid%3D211164673%26im%3D1_t016d7ec49acf3a8452%26src%3Dpcw_ipcam_live%26t%3D1; T=s%3Dc9c5d2bb9b8e1c72174ed29a495a4390%26t%3D1772445161%26lm%3D%26lf%3D2%26sk%3D584e3b13b9fc58ac98fb5a1a9504eb37%26mt%3D1772445161%26rc%3D%26v%3D2.0%26a%3D1; __NS_T=s%3Dc9c5d2bb9b8e1c72174ed29a495a4390%26t%3D1772445161%26lm%3D%26lf%3D2%26sk%3D584e3b13b9fc58ac98fb5a1a9504eb37%26mt%3D1772445161%26rc%3D%26v%3D2.0%26a%3D1; jia_web_sid=054fcb6d5c308baed793114d5b7a8895igFPhAQESo3QFvXf2Y7msjyry1smk1nZ2AxqGhNGEck%3D"

url = "https://my.jia.360.cn/web/myList"

req = urllib.request.Request(url)
req.add_header("Cookie", cookie)
req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7")
req.add_header("Sec-Fetch-Site", "same-origin")

try:
    with urllib.request.urlopen(req) as res:
        print(f"Status: {res.status}")
        content = res.read().decode('utf-8')
        print(content[:500])
        with open("mylist.html", "w") as f:
            f.write(content)
except Exception as e:
    print(e)

