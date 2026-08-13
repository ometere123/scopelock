"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { gen, reports, type Report } from "@/lib/scope-data";
const final=(r:Report)=>Number(r.status)>=3;
export default function Settlements(){const [items,setItems]=useState<Report[]>([]);const [error,setError]=useState("");useEffect(()=>{reports().then(r=>setItems(r.filter(final))).catch(e=>setError(e instanceof Error?e.message:"RPC unavailable."))},[]);return <main className="ledger-section"><p className="eyebrow">SETTLEMENT LEDGER</p><h1>Final on-chain outcomes.</h1>{error?<p>{error}</p>:<div className="rows">{items.length?items.map(r=><Link className="row" key={String(r.id)} href={`/disclosures/${r.id}`}><b>SL-{String(r.id)} · {String(r.verdict||"EXPIRED")}</b><span>{String(r.severity||"N/A")} · payout {gen(r.payout)} · refund {gen(r.refund)} · slash {gen(r.slash)}</span></Link>):<p>No final reports are available.</p>}</div>}</main>}
