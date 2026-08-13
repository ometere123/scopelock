#!/usr/bin/env node
import { createHash } from "node:crypto";
import { mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(new URL("../frontend/package.json", import.meta.url));
const { createClient } = require("genlayer-js");
const { studionet } = require("genlayer-js/chains");

const address = process.argv[2];
if (!address) throw new Error("usage: node scripts/verify-deployed-source.mjs <contract-address>");
const endpoint = studionet.rpcUrls.default.http[0];
const rpc = await fetch(endpoint, { method:"POST", headers:{"content-type":"application/json"}, body:JSON.stringify({jsonrpc:"2.0",id:1,method:"gen_getContractCode",params:[address]}) }).then(r=>r.json());
if (rpc.error) throw new Error(JSON.stringify(rpc.error));
const base64 = rpc.result;
const decoded = Buffer.from(base64, "base64");
mkdirSync(".tmp", {recursive:true});
writeFileSync(".tmp/deployed-scopelock.py", decoded);
const client = createClient({chain:studionet});
const source = await client.getContractCode(address);
writeFileSync(".tmp/genlayerjs-scopelock.py", source, "utf8");
const local = readFileSync("contracts/scopelock.py");
const hash = b => createHash("sha256").update(b).digest("hex");
let offset = -1; for(let i=0;i<Math.max(local.length,decoded.length);i++){if(local[i]!==decoded[i]){offset=i;break;}}
console.log(JSON.stringify({localRawByteSha256:hash(local),rpcBase64StringSha256:hash(Buffer.from(base64,"utf8")),rpcDecodedSourceSha256:hash(decoded),genlayerJsSourceSha256:hash(Buffer.from(source,"utf8")),localBytes:local.length,deployedBytes:decoded.length,firstDifference:offset,localAround:offset<0?null:local.subarray(Math.max(0,offset-24),offset+48).toString("hex"),deployedAround:offset<0?null:decoded.subarray(Math.max(0,offset-24),offset+48).toString("hex")},null,2));
