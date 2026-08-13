"use client";

import { createAccount, createClient, generatePrivateKey } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";

export const CONTRACT_ADDRESS = (process.env.NEXT_PUBLIC_SCOPELOCK_CONTRACT ?? "0x00f0ba00fB0a6C12f9b6eFEc2CBEEDC78920BfCf") as `0x${string}`;
export const ENDPOINT = process.env.NEXT_PUBLIC_GENLAYER_ENDPOINT ?? "https://studio.genlayer.com/api";
export const CHAIN_NAME = process.env.NEXT_PUBLIC_GENLAYER_CHAIN ?? "studionet";
const KEY = "scopelock.browser-key";

export function readClient() { return createClient({ chain: studionet, endpoint: ENDPOINT, account: createAccount() }); }
export function generatedWallet() {
  const existing = localStorage.getItem(KEY) as `0x${string}` | null;
  const privateKey = existing ?? generatePrivateKey();
  if (!existing) localStorage.setItem(KEY, privateKey);
  return { privateKey, account: createAccount(privateKey), client: createClient({ chain: studionet, endpoint: ENDPOINT, account: createAccount(privateKey) }) };
}
export async function injectedWallet(address: `0x${string}`) {
  const provider = window.ethereum;
  if (!provider) throw new Error("No injected EIP-1193 wallet found. Create a browser wallet instead.");
  const client = createClient({ chain: studionet, endpoint: ENDPOINT, account: address, provider });
  await client.connect(CHAIN_NAME as never);
  return client;
}
export async function waitFinalized(client: ReturnType<typeof readClient>, hash: `0x${string}`) { return client.waitForTransactionReceipt({ hash: hash as never, status: TransactionStatus.FINALIZED, interval: 5000, retries: 90 }); }
declare global { interface Window { ethereum?: { request(args: { method: string }): Promise<unknown> } } }
