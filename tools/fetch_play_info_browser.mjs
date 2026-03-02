#!/usr/bin/env node
/**
 * Auto fetch latest relayStream/playKey from 360 with browser login.
 *
 * Usage:
 *   node tools/fetch_play_info_browser.mjs --sn YOUR_DEVICE_SN --play
 *   node tools/fetch_play_info_browser.mjs --sn YOUR_DEVICE_SN --account xxx --password yyy --play
 *
 * Notes:
 * - Session is persisted under tools/.cache/360-browser-session.
 * - If captcha is required, complete it in the opened browser window.
 */

import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";
import { chromium } from "playwright";

const __filename = fileURLToPath(import.meta.url);
const toolsDir = path.dirname(__filename);
const repoRoot = path.resolve(toolsDir, "..");

function getArg(name) {
  const idx = process.argv.indexOf(name);
  if (idx >= 0 && process.argv[idx + 1]) return process.argv[idx + 1];
  return null;
}

function hasFlag(flag) {
  return process.argv.includes(flag);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const deviceSn = getArg("--sn") || process.env.DEVICE_SN || "";
const waitSeconds = Number(getArg("--wait") || process.env.LOGIN_WAIT_SECONDS || 180);
const shouldPlay = hasFlag("--play");
const loginAccount = getArg("--account") || process.env.LOGIN_ACCOUNT || "";
const loginPassword = getArg("--password") || process.env.LOGIN_PASSWORD || "";

if (!deviceSn) {
  console.error("Missing device SN.");
  console.error("Usage: node tools/fetch_play_info_browser.mjs --sn YOUR_DEVICE_SN [--play]");
  process.exit(1);
}

if (!Number.isFinite(waitSeconds) || waitSeconds <= 0) {
  console.error("Invalid wait seconds.");
  process.exit(1);
}

const sessionDir = path.join(toolsDir, ".cache", "360-browser-session");

function mask(v, left = 8, right = 8) {
  if (!v || v.length <= left + right) return "***";
  return `${v.slice(0, left)}****${v.slice(-right)}`;
}

function buildCookieHeader(cookies) {
  return cookies.map((c) => `${c.name}=${c.value}`).join("; ");
}

function pickCookieMap(cookies) {
  const map = new Map();
  for (const c of cookies) map.set(c.name, c.value);
  return map;
}

function hasLoginCookies(cookies) {
  const map = pickCookieMap(cookies);
  return (map.has("Q") || map.has("__NS_Q")) && (map.has("T") || map.has("__NS_T"));
}

async function waitForLoginCookies(context, timeoutMs) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const cookies = await context.cookies();
    if (hasLoginCookies(cookies)) return cookies;
    await sleep(1000);
  }
  return null;
}

async function getVisibleLocator(frame, selectors) {
  for (const sel of selectors) {
    const loc = frame.locator(sel).first();
    try {
      const count = await loc.count();
      if (count === 0) continue;
      if (await loc.isVisible()) return loc;
    } catch (_) {
      continue;
    }
  }
  return null;
}

async function tryFillLoginOnce(page, account, password) {
  const userSelectors = [
    'input[name="account"]',
    'input[name="userName"]',
    'input[name="username"]',
    'input[type="text"]',
  ];
  const passSelectors = [
    'input[name="password"]',
    'input[type="password"]',
  ];
  const submitSelectors = [
    'button[type="submit"]',
    'input[type="submit"]',
    ".quc-submit",
    ".btn-login",
    'button:has-text("登录")',
    'a:has-text("登录")',
  ];

  const frames = page.frames();
  for (const frame of frames) {
    const userInput = await getVisibleLocator(frame, userSelectors);
    const passInput = await getVisibleLocator(frame, passSelectors);
    if (!userInput || !passInput) continue;

    await userInput.fill(account);
    await passInput.fill(password);

    const submit = await getVisibleLocator(frame, submitSelectors);
    if (submit) {
      await submit.click();
    } else {
      await passInput.press("Enter");
    }
    return true;
  }
  return false;
}

async function autoLoginWithCredentials(page, account, password) {
  await page.goto("https://my.jia.360.cn/web/index", { waitUntil: "domcontentloaded" });

  for (let i = 0; i < 20; i++) {
    const submitted = await tryFillLoginOnce(page, account, password);
    if (submitted) return true;
    await sleep(1000);
  }
  return false;
}

async function main() {
  const context = await chromium.launchPersistentContext(sessionDir, {
    headless: false,
    viewport: { width: 1366, height: 900 },
  });

  try {
    const page = context.pages()[0] || (await context.newPage());
    await page.goto("https://my.jia.360.cn/web/index", { waitUntil: "domcontentloaded" });

    let cookies = await context.cookies();
    if (!hasLoginCookies(cookies) && loginAccount && loginPassword) {
      console.error("[Browser] Attempting auto login with provided account/password...");
      const submitted = await autoLoginWithCredentials(page, loginAccount, loginPassword);
      if (!submitted) {
        console.error("[Browser] Could not find login form automatically.");
      }
    }

    cookies = await context.cookies();
    if (!hasLoginCookies(cookies)) {
      console.error(`[Browser] Please complete login in the opened browser within ${waitSeconds}s (captcha may be required)...`);
      cookies = await waitForLoginCookies(context, waitSeconds * 1000);
      if (!cookies) {
        console.error("[Browser] Login timeout: Q/T cookies not found.");
        process.exit(2);
      }
    }

    const cookieHeader = buildCookieHeader(cookies);
    const apiUrl = `https://my.jia.360.cn/app/play?sn=${encodeURIComponent(deviceSn)}&mode=0`;

    const resp = await context.request.get(apiUrl, {
      headers: {
        accept: "application/json, text/javascript, */*; q=0.01",
        "x-requested-with": "XMLHttpRequest",
        referer: "https://my.jia.360.cn/web/index",
        cookie: cookieHeader,
      },
    });

    const bodyText = await resp.text();
    let json;
    try {
      json = JSON.parse(bodyText);
    } catch (e) {
      console.error("[API] Failed to parse /app/play response as JSON.");
      console.error(bodyText.slice(0, 500));
      process.exit(3);
    }

    if (!resp.ok() || json.errorCode !== 0 || !json.relayStream || !json.playKey) {
      console.error(`[API] HTTP=${resp.status()} errorCode=${json.errorCode ?? "unknown"} msg=${json.errorMsg || json.errmsg || "unknown"}`);
      console.error(bodyText.slice(0, 500));
      process.exit(4);
    }

    const streamUrl = `https://flv-live.jia.360.cn/live_jia_personal/${json.relayStream}.flv`;

    console.log(`[OK] relayStream: ${json.relayStream}`);
    console.log(`[OK] playKey: ${mask(json.playKey)}`);
    console.log(`[OK] streamUrl: ${streamUrl}`);
    console.log("");
    console.log("Export and play manually:");
    console.log(`STREAM_URL='${streamUrl}' PLAY_KEY='${json.playKey}' bash tools/play_live.sh`);

    if (shouldPlay) {
      console.log("");
      console.log("[Play] Starting tools/play_live.sh ...");
      await context.close();
      const child = spawn("bash", ["tools/play_live.sh"], {
        cwd: repoRoot,
        stdio: "inherit",
        env: {
          ...process.env,
          STREAM_URL: streamUrl,
          PLAY_KEY: json.playKey,
        },
      });
      child.on("exit", (code) => process.exit(code ?? 0));
      return;
    }

    await context.close();
  } catch (err) {
    console.error("[Fatal]", err);
    process.exit(10);
  }
}

main();
