"use client";
import { createAccount, createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";
export const CONTRACT_ADDRESS = process.env.NEXT_PUBLIC_SCOPELOCK_CONTRACT as `0x${string}` | undefined;
export const ENDPOINT = process.env.NEXT_PUBLIC_GENLAYER_ENDPOINT ?? "https://studio.genlayer.com/api";
export function ensureContract() { if (!CONTRACT_ADDRESS) throw new Error("ScopeLock contract is not configured. Set NEXT_PUBLIC_SCOPELOCK_CONTRACT."); return CONTRACT_ADDRESS; }
export function readClient() { return createClient({ chain: studionet, endpoint: ENDPOINT, account: createAccount() }); }
export async function injectedClient(address: `0x${string}`) { if (!window.ethereum) throw new Error("No injected wallet found."); const client = createClient({ chain: studionet, endpoint: ENDPOINT, account: address, provider: window.ethereum }); await client.connect("studionet" as never); return client; }
export async function waitFinalized(client: ReturnType<typeof readClient>, hash: `0x${string}`) { return client.waitForTransactionReceipt({ hash: hash as never, status: TransactionStatus.FINALIZED, interval: 5000, retries: 90 }); }
declare global { interface Window { ethereum?: { request(args: { method: string; params?: unknown[] }): Promise<unknown>; on?(name: string, listener: (...args: unknown[]) => void): void; removeListener?(name: string, listener: (...args: unknown[]) => void): void } } }
