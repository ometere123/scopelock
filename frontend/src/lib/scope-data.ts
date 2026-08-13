"use client";
import { ensureContract, readClient } from "@/lib/genlayer";
export type Program=Record<string, string|number>; export type Report=Record<string,string|number>;
export async function programs(){const client=readClient();const ids=await client.readContract({address:ensureContract(),functionName:"list_program_ids",args:[0,50]}) as number[];return Promise.all(ids.map(id=>client.readContract({address:ensureContract(),functionName:"get_program",args:[id]}) as Promise<Program>));}
export async function reports(){const client=readClient();const ids=await client.readContract({address:ensureContract(),functionName:"list_report_ids",args:[0,50]}) as number[];return Promise.all(ids.map(id=>client.readContract({address:ensureContract(),functionName:"get_report",args:[id]}) as Promise<Report>));}
export async function program(id:string){return readClient().readContract({address:ensureContract(),functionName:"get_program",args:[BigInt(id)]}) as Promise<Program>}
export async function report(id:string){return readClient().readContract({address:ensureContract(),functionName:"get_report",args:[BigInt(id)]}) as Promise<Report>}
export const gen=(value: unknown)=>{try{return `${(BigInt(String(value))/1000000000000000000n).toString()} GEN`}catch{return "N/A"}};
