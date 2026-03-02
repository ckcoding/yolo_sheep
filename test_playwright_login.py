import asyncio
from playwright.async_api import async_playwright
import time

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # intercept responses
        sid_cookie = None
        play_key = None
        stream_url = None
        
        print("Goto login page...")
        await page.goto("https://my.jia.360.cn/")
        await page.wait_for_selector("input.quc-input-account", timeout=10000)
        
        print("Typing credentials...")
        await page.fill("input.quc-input-account", "18219951345")
        await page.fill("input.quc-input-password", "Chai962464")
        
        # Check agreement
        await page.click("input.quc-checkbox")
        
        print("Clicking submit...")
        await page.click("input.quc-button-submit")
        
        print("Waiting for network idle to see if captcha appears...")
        try:
            await page.wait_for_selector(".quc-captcha-canvas", timeout=5000)
            print("CAPTCHA DETECTED. WE CANNOT PROCEED FULLY HEADLESS WITHOUT SOLVING IT.")
            await page.screenshot(path="captcha.png")
        except:
            print("No Captcha detected, waiting for redirect to myList...")
            await page.wait_for_url("**/web/myList**", timeout=10000)
            print("Redirected to myList! Getting cookies...")
            
            cookies = await context.cookies()
            for c in cookies:
                if c["name"] == "jia_web_sid":
                    sid_cookie = c["value"]
            
            # extract playkey
            content = await page.content()
            import re
            m = re.search(r'playKey":"([^"]+)"', content)
            if m:
                play_key = m.group(1)
            
            m2 = re.search(r'stream.*?(http[^"]+\.flv)', content)
            if m2:
                stream_url = m2.group(1)
            
            print(f"PLAY_KEY: {play_key}")
            print(f"STREAM_URL: {stream_url}")
            print(f"SID_COOKIE: {sid_cookie}")

        await browser.close()

asyncio.run(main())
