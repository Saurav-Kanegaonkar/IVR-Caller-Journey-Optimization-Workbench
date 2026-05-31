import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("/Users/sauravkanegaonkar/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const url = process.argv[2] || "http://127.0.0.1:4173/";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, deviceScaleFactor: 1 });

await page.goto(url, { waitUntil: "networkidle" });
await page.screenshot({ path: path.join(root, "docs/images/command-center.png"), fullPage: true });

await page.click('[data-view="queue"]');
await page.waitForTimeout(250);
await page.screenshot({ path: path.join(root, "docs/images/friction-queue.png"), fullPage: true });

await page.click('[data-view="flow"]');
await page.waitForTimeout(250);
await page.screenshot({ path: path.join(root, "docs/images/flow-diagnostics.png"), fullPage: true });

await page.click('[data-view="handoff"]');
await page.waitForTimeout(250);
await page.screenshot({ path: path.join(root, "docs/images/stakeholder-handoff.png"), fullPage: true });

const metricCount = await page.locator("#metricStrip article").count();
const activeHeading = await page.locator("h1").textContent();
await browser.close();

console.log(JSON.stringify({ activeHeading, metricCount }, null, 2));
