"use client";
import { useEffect, useMemo, useState } from "react";
import { ensureContract, waitFinalizedSuccessful } from "@/lib/genlayer";
import { useWallet } from "@/components/wallet-provider";
import type { Report } from "@/lib/scope-data";

const SUBMITTED=1, NEEDS_EVIDENCE=2;
const TERMINAL=new Set([3,4,5,6,7,8]);

export function ReportActions({item,onRefresh}:{item:Report;onRefresh:()=>Promise<void>}){
 const wallet=useWallet();
 const [url,setUrl]=useState("");
 const [busy,setBusy]=useState(false);
 const [message,setMessage]=useState("");
 const [currentTime,setCurrentTime]=useState(Date.now);
 const status=Number(item.status), reportId=BigInt(String(item.id));
 const researcher=String(item.researcher||"");
 const isResearcher=Boolean(wallet.address)&&wallet.address!.toLowerCase()===researcher.toLowerCase();
 const deadline=useMemo(()=>Date.parse(String(item.evidence_deadline||"")),[item.evidence_deadline]);
 const expired=Number.isFinite(deadline)&&currentTime>=deadline;

 useEffect(()=>{
  if(status!==NEEDS_EVIDENCE||!Number.isFinite(deadline))return;
  const remaining=deadline-Date.now();
  const timer=window.setTimeout(()=>setCurrentTime(Date.now()),Math.max(0,remaining)+50);
  return()=>window.clearTimeout(timer);
 },[deadline,status]);

 async function write(functionName:string,args:unknown[]){
  setBusy(true);setMessage("Wallet signature requested…");
  try{
   const client=await wallet.getWriteClient();
   const hash=await client.writeContract({address:ensureContract(),functionName,args:args as never[],value:0n,consensusMaxRotations:3});
   setMessage(`Transaction submitted: ${hash}. Waiting for finalization and GenVM execution…`);
   await waitFinalizedSuccessful(client as never,hash as never);
   setMessage("Finalized with successful GenVM execution. Refreshing the on-chain report…");
   await onRefresh();
   setMessage("Chain state refreshed.");
  }catch(error){
   setMessage(error instanceof Error?error.message:"Protocol action failed.");
   await onRefresh().catch(()=>undefined);
  }finally{setBusy(false)}
 }

 if(TERMINAL.has(status)) return <section className="protocol-actions"><p className="eyebrow">07 / PROTOCOL ACTIONS</p><h2>LIFECYCLE COMPLETE</h2><p>This report is terminal. No further lifecycle write is available.</p></section>;
 if(status===SUBMITTED) return <section className="protocol-actions"><p className="eyebrow">07 / PROTOCOL ACTIONS</p><h2>READY FOR CONSENSUS</h2><p>Any connected account may ask GenLayer validators to adjudicate this submitted report.</p><button className="connect" disabled={busy||!wallet.address} onClick={()=>write("adjudicate",[reportId])}>{busy?"ADJUDICATING…":wallet.address?"RUN ADJUDICATION":"CONNECT WALLET TO ADJUDICATE"}</button><p className="tx-message" aria-live="polite">{message}</p></section>;
 if(status===NEEDS_EVIDENCE) return <section className="protocol-actions"><p className="eyebrow">07 / PROTOCOL ACTIONS</p><h2>MORE EVIDENCE REQUESTED</h2><dl><div><dt>Reasoning</dt><dd>{String(item.reasoning||"No reasoning recorded.")}</dd></div><div><dt>Evidence digest</dt><dd>{String(item.evidence_digest||"No digest recorded.")}</dd></div><div><dt>Deadline</dt><dd>{String(item.evidence_deadline||"Unavailable")}</dd></div><div><dt>Researcher</dt><dd>{researcher}</dd></div><div><dt>Connected wallet</dt><dd>{wallet.address||"Not connected"}</dd></div><div><dt>Supplementary evidence</dt><dd>{String(item.supplementary_url||"None submitted")}</dd></div></dl>{expired?<><p>The evidence window has closed. The contract permits any connected account to expire this request and return the full researcher bond.</p><button className="connect" disabled={busy||!wallet.address} onClick={()=>write("expire_needs_evidence",[reportId])}>{busy?"EXPIRING…":wallet.address?"EXPIRE REQUEST / RETURN BOND":"CONNECT WALLET TO EXPIRE"}</button></>:isResearcher?<form onSubmit={e=>{e.preventDefault();if(!url.startsWith("https://")){setMessage("Supplementary evidence must use a public HTTPS URL.");return}void write("add_supplementary_evidence",[reportId,url])}}><label>Supplementary public evidence URL<input required type="url" pattern="https://.*" value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://…"/></label><button className="connect" disabled={busy}>{busy?"SUBMITTING…":"ADD SUPPLEMENTARY EVIDENCE"}</button></form>:<p>Only the researcher address above may add evidence before the deadline. Connect that wallet to continue.</p>}<p className="tx-message" aria-live="polite">{message}</p></section>;
 return <section className="protocol-actions"><p className="eyebrow">07 / PROTOCOL ACTIONS</p><h2>ACTION UNAVAILABLE</h2><p>The current on-chain status does not expose a lifecycle write.</p></section>;
}
