"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { gen, program, reports, type Program, type Report } from "@/lib/scope-data";

const state = (value: unknown) => Number(value) === 1 ? "OPEN" : Number(value) === 2 ? "PAUSED" : "CLOSED";
export default function ProgramDossier({ params }: { params: Promise<{ id: string }> }) {
  const [id, setId] = useState(""); const [item, setItem] = useState<Program>(); const [items, setItems] = useState<Report[]>([]); const [error, setError] = useState("");
  useEffect(()=>{params.then(async ({id})=>{setId(id); try { const p=await program(id); setItem(p); setItems((await reports()).filter(r=>String(r.program_id)===id)); } catch(e){setError(e instanceof Error?e.message:"Unable to read program.");}})},[params]);
  if(error) return <main className="ledger-section"><p className="eyebrow">PROGRAM DOSSIER</p><h1>RPC unavailable.</h1><p>{error}</p></main>;
  if(!item) return <main className="ledger-section"><p className="eyebrow">PROGRAM / {id||"…"}</p><h1>Reading chain record…</h1></main>;
  return <main className="ledger-section"><p className="eyebrow">PROGRAM / SL-P{item.id}</p><h1>{String(item.name)}</h1><p><a href={String(item.repository_url)} target="_blank">{String(item.repository_url)}</a> @ {String(item.repository_ref)} · {state(item.status)}</p><div className="rows"><section className="row"><b>01 / TARGET</b><span>Sponsor {String(item.sponsor)}<br/>Pinned ref {String(item.repository_ref)}</span></section><section className="row"><b>02 / SCOPE</b><span>{String(item.scope)}</span></section><section className="row"><b>03 / PAYOUT MATRIX</b><span>LOW {gen(item.low_payout)} · MEDIUM {gen(item.medium_payout)} · HIGH {gen(item.high_payout)} · CRITICAL {gen(item.critical_payout)}</span></section><section className="row"><b>04 / PROGRAM BALANCE</b><span>Funded {gen(item.funded_total)} · Remaining {gen(item.remaining_pool)} · Min bond {gen(item.min_bond)} · Slash {String(item.invalid_slash_bps)} bps</span></section><section className="row"><b>05 / DISCLOSURES</b><span>{items.length} loaded / {String(item.report_count)} total<br/>{items.map(r=><Link key={String(r.id)} href={`/disclosures/${r.id}`}>SL-{String(r.id)} {String(r.title)}<br/></Link>)}</span></section><section className="row"><b>06 / CONTRACT PROOF</b><span>Window {String(item.starts_at)} → {String(item.ends_at)} · {String(item.open_report_count)} unresolved</span></section></div><Link className="connect" href={`/programs/${item.id}/submit`}>SUBMIT DISCLOSURE</Link></main>;
}
