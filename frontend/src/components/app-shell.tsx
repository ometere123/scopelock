"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useWallet } from "@/components/wallet-provider";

const links=[['INDEX','/'],['DISCLOSURES','/disclosures'],['PROGRAMS','/programs'],['PRECEDENT','/precedent'],['SETTLEMENTS','/settlements']] as const;

export function AppShell({children}:{children:React.ReactNode}){
 const path=usePathname();
 const wallet=useWallet();
 const [connectError,setConnectError]=useState("");
 const short=wallet.address?`${wallet.address.slice(0,6)}…${wallet.address.slice(-4)}`:"CONNECT WALLET";
 const connect=async()=>{
  setConnectError("");
  try {await wallet.connect()}
  catch(error) {setConnectError(error instanceof Error?error.message:"Wallet connection failed. Try again after unlocking your wallet.")}
 };
 const network=wallet.address&&wallet.networkStatus==="ready"
  ?`STUDIONET · CONNECTED ${short}`
  :wallet.address
   ?"ACCOUNT CONNECTED · SWITCH TO STUDIONET FOR WRITES"
   :"STUDIONET · READ-ONLY · INJECTED WALLET REQUIRED FOR WRITES";
 return <><header className="masthead"><Link className="wordmark" href="/"><svg aria-hidden="true" viewBox="0 0 64 64"><path d="M32 7 52 15v15c0 13-8.2 22.8-20 27C20.2 52.8 12 43 12 30V15L32 7Z"/><path className="wordmark-check" d="M24 31.5 29.2 37 41 24.5"/></svg><span>SCOPELOCK</span></Link><nav aria-label="Primary navigation">{links.map(([name,href])=><Link key={href} className={path===href||path.startsWith(`${href}/`)&&href!=="/"?"active":""} href={href}>{name}</Link>)}</nav><div className="wallet-actions">{wallet.address?<><span className="connected-address" aria-label="Connected wallet">{short}</span><button className="disconnect" onClick={wallet.disconnect}>DISCONNECT</button></>:<button className="connect" disabled={wallet.status==="connecting"} aria-label="Connect wallet" onClick={()=>void connect()}>{wallet.status==="connecting"?"CONNECTING…":"CONNECT WALLET"}</button>}</div></header><div className="network-strip">{network}</div>{wallet.error||connectError?<p className="wallet-error" role="alert" aria-live="polite">{connectError||wallet.error}</p>:null}{children}</>;
}
