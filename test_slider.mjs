import { chromium } from "playwright";

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  });
  const page = await context.newPage();
  
  await page.goto("https://my.jia.360.cn/");
  await page.waitForTimeout(2000);
  
  // Fill
  await page.fill("input.quc-input-account", "18219951345");
  await page.fill("input.quc-input-password", "Chai962464");
  await page.click("input.quc-checkbox");
  await page.click("input.quc-button-submit");
  
  await page.waitForTimeout(3000);
  
  // See if captcha iframe exists or slider natively
  const bg = await page.$(".quc-captcha-bg"); // or whatever class it is
  if (bg) {
      console.log("Slider captcha detected natively!");
  } else {
      console.log("No slider captcha directly on page.");
  }
  
  await page.screenshot({ path: "slider_check.png" });
  await browser.close();
})();
