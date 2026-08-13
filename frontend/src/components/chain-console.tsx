"use client";

import { useEffect, useState } from "react";
import { CONTRACT_ADDRESS, generatedWallet, injectedWallet, readClient } from "@/lib/genlayer";

type Mode = "read-only" | "browser" | "injected";
const short = (value?: string) => value ? `${value.slice(0, 6)}…${value.slice(-4)}` : "NOT CONNECTED";

export function ChainConsole() {
  const [mode, setMode] = useState<Mode>("read-only"); const [address, setAddress] = useState<string>();
  const [programs, setPrograms] = useState<string>("—"); const [reports, setReports] = useState<string>("—");
  const [message, setMessage] = useState("Reading ScopeLock on StudioNet…"); const [busy, setBusy] = useState(false);
  async function refresh() { try { const client = readClient(); const [p, r] = await Promise.all([client.readContract({ address: CONTRACT_ADDRESS, functionName: "program_count", args: [] }), client.readContract({ address: CONTRACT_ADDRESS, functionName: "report_count", args: [] })]); setPrograms(String(p)); setReports(String(r)); setMessage("Live on-chain read complete."); } catch { setMessage("Contract read unavailable. Check StudioNet RPC and the deployed address."); } }
  useEffect(() => { const timer = window.setTimeout(() => { void refresh(); }, 0); return () => window.clearTimeout(timer); }, []);
  async function connectBrowser() { const wallet = generatedWallet(); setMode("browser"); setAddress(wallet.account.address); setMessage("Browser wallet active. Its key is stored only in this browser; export it before clearing site data."); }
  async function connectInjected() { try { const accounts = await window.ethereum?.request({ method: "eth_requestAccounts" }) as `0x${string}`[]; if (!accounts?.[0]) throw new Error("Wallet returned no account."); await injectedWallet(accounts[0]); setMode("injected"); setAddress(accounts[0]); setMessage("Injected wallet connected for ScopeLock writes."); } catch (error) { setMessage(error instanceof Error ? error.message : "Wallet connection failed."); } }
  async function exerciseRead() { setBusy(true); await refresh(); setBusy(false); }
  return <section className="chain-console" aria-label="ScopeLock chain connection">
    <div><span>NETWORK</span><strong>GENLAYER STUDIO NET</strong></div><div><span>CONTRACT</span><a href={`https://genlayer-explorer.vercel.app/address/${CONTRACT_ADDRESS}`} target="_blank" rel="noreferrer">{short(CONTRACT_ADDRESS)}</a></div><div><span>PROGRAMS</span><strong>{programs}</strong></div><div><span>REPORTS</span><strong>{reports}</strong></div>
    <div className="chain-actions"><button onClick={connectInjected}>CONNECT INJECTED</button><button onClick={connectBrowser}>CREATE BROWSER WALLET</button><button onClick={exerciseRead} disabled={busy}>{busy ? "READING…" : "REFRESH CHAIN"}</button></div>
    <p aria-live="polite"><b>{mode.toUpperCase()} / {short(address)}</b> — {message}</p>
  </section>;
}
