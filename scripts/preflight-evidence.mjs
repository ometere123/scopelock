#!/usr/bin/env node
// Usage: node scripts/preflight-evidence.mjs <repo> <commit> <component> <disclosure-url>
const [repo, commit, component, disclosure] = process.argv.slice(2);
if (!repo || !/^[0-9a-f]{40}$/i.test(commit) || !component || !disclosure) throw new Error("usage: <repo> <40-char-commit> <component> <disclosure-url>");
const advisory = disclosure.match(/github\.com\/advisories\/(GHSA-[\w-]+)/i);
const legs = [
  ["DISCLOSURE", advisory ? `https://api.github.com/advisories/${advisory[1]}` : disclosure],
  ["TARGET", `https://raw.githubusercontent.com/${repo.replace(/^https:\/\/github\.com\//, "").replace(/\/$/, "")}/${commit}/${component.replace(/^\//, "")}`],
];
let total = 0;
for (const [name, url] of legs) { const response = await fetch(url, {headers:{Accept:"application/vnd.github+json"}}); const body = await response.text(); const normalized = body.replace(/\s+/g," ").trim(); total += normalized.length; console.log(`${name}\nadapter: ${url.includes("api.github.com")?"github-advisory-api":"static-http"}\nresolved URL: ${url}\nHTTP status: ${response.status}\nnormalized size: ${normalized.length}\n`); if (!response.ok || normalized.length < 20) process.exitCode = 1; }
console.log(`SUPPLEMENTARY\npresent: no\n\nPRECEDENTS\ncount: 0\n\nestimated normalized evidence/prompt size: ${total}`);
