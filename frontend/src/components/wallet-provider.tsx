"use client";
import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { injectedClient } from "@/lib/genlayer";
type Wallet = { address?: `0x${string}`; status: "disconnected"|"connecting"|"connected"; connect(): Promise<void>; disconnect(): void; getWriteClient(): Promise<Awaited<ReturnType<typeof injectedClient>>>; refresh(): Promise<void> };
const Context=createContext<Wallet|null>(null);
export function WalletProvider({children}:{children:React.ReactNode}) { const [address,setAddress]=useState<`0x${string}`>(); const [status,setStatus]=useState<Wallet["status"]>("disconnected");
 const connect=useCallback(async()=>{setStatus("connecting");try{if(!window.ethereum)throw new Error("Install or unlock an injected EIP-1193 wallet for StudioNet.");const accounts=await window.ethereum.request({method:"eth_requestAccounts"}) as `0x${string}`[];if(!accounts?.[0])throw new Error("Wallet returned no account.");await injectedClient(accounts[0]);setAddress(accounts[0]);setStatus("connected");}catch(e){setStatus("disconnected");throw e;}},[]);
 const getWriteClient=useCallback(async()=>{if(!address)throw new Error("Connect the wallet shown in the header before signing.");return injectedClient(address)},[address]); const refresh=useCallback(async()=>{},[]); const value=useMemo(()=>({address,status,connect,disconnect:()=>{setAddress(undefined);setStatus("disconnected")},getWriteClient,refresh}),[address,status,connect,getWriteClient,refresh]);return <Context.Provider value={value}>{children}</Context.Provider> }
export function useWallet(){const value=useContext(Context);if(!value)throw new Error("WalletProvider missing");return value}
