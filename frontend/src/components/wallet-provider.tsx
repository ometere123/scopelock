"use client";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { studionet } from "genlayer-js/chains";
import { injectedClient } from "@/lib/genlayer";

type NetworkStatus = "unknown" | "ready" | "error";
type Wallet = {
 address?: `0x${string}`;
 status: "disconnected" | "connecting" | "connected";
 networkStatus: NetworkStatus;
 error?: string;
 connect(): Promise<void>;
 disconnect(): void;
 getWriteClient(): Promise<Awaited<ReturnType<typeof injectedClient>>>;
 refresh(): Promise<void>;
};

const Context=createContext<Wallet|null>(null);
const studioChainId=`0x${studionet.id.toString(16)}`.toLowerCase();
const accountError="Wallet account connected, but StudioNet setup did not complete. Switch to GenLayer StudioNet in your wallet, then try again.";
const manualDisconnectKey="scopelock:wallet-manually-disconnected";

function readManualDisconnect(){
 try{return typeof window!=="undefined"&&window.localStorage.getItem(manualDisconnectKey)==="true"}catch{return false}
}

function firstAccount(value: unknown): `0x${string}` | undefined {
 return Array.isArray(value) && typeof value[0]==="string" ? value[0] as `0x${string}` : undefined;
}

export function WalletProvider({children}:{children:React.ReactNode}) {
 const [address,setAddress]=useState<`0x${string}`>();
 const [status,setStatus]=useState<Wallet["status"]>("disconnected");
 const [networkStatus,setNetworkStatus]=useState<NetworkStatus>("unknown");
 const [error,setError]=useState<string>();
 const [manuallyDisconnected,setManuallyDisconnected]=useState(readManualDisconnect);

 const clearSession=useCallback(()=>{setAddress(undefined);setStatus("disconnected");setNetworkStatus("unknown");setError(undefined)},[]);
 const setManualDisconnect=useCallback((value:boolean)=>{
  setManuallyDisconnected(value);
  try{if(value)window.localStorage.setItem(manualDisconnectKey,"true");else window.localStorage.removeItem(manualDisconnectKey)}catch{}
 },[]);
 const inspectNetwork=useCallback(async()=>{
  if(!window.ethereum)return;
  try{
   const chainId=await window.ethereum.request({method:"eth_chainId"});
   if(typeof chainId==="string"&&chainId.toLowerCase()===studioChainId){setNetworkStatus("ready");setError(undefined)}
   else {setNetworkStatus("error");setError("Wallet account connected. Switch to GenLayer StudioNet to sign ScopeLock writes.")}
  }catch{setNetworkStatus("error");setError("Wallet account connected, but ScopeLock could not confirm StudioNet. Switch to GenLayer StudioNet, then try again.")}
 },[]);
 const syncWallet=useCallback(async()=>{
  if(manuallyDisconnected){clearSession();return}
  if(!window.ethereum){clearSession();return}
  try{
   const account=firstAccount(await window.ethereum.request({method:"eth_accounts"}));
   if(!account){clearSession();return}
   setAddress(account);setStatus("connected");setError(undefined);
   await inspectNetwork();
  }catch(error){clearSession();setError(error instanceof Error?error.message:"Unable to read the injected wallet session.")}
 },[clearSession,inspectNetwork,manuallyDisconnected]);
 const prepareStudioNet=useCallback(async(account:`0x${string}`)=>{
  try{const client=await injectedClient(account);setNetworkStatus("ready");setError(undefined);return client}
  catch(error){setNetworkStatus("error");setError(accountError);throw error}
 },[]);
 const connect=useCallback(async()=>{
  setManualDisconnect(false);
  setStatus("connecting");setError(undefined);
  try{
   if(!window.ethereum)throw new Error("No injected wallet was found. Open ScopeLock inside your wallet browser or install and unlock a StudioNet-compatible wallet.");
   const account=firstAccount(await window.ethereum.request({method:"eth_requestAccounts"}));
   if(!account)throw new Error("Wallet returned no account. Unlock the wallet and approve the ScopeLock connection.");
   setAddress(account);setStatus("connected");setNetworkStatus("unknown");
   try{await prepareStudioNet(account)}catch{ /* rendered as a network error while address remains connected */ }
  }catch(error){clearSession();setError(error instanceof Error?error.message:"Wallet connection failed.");throw error}
 },[clearSession,prepareStudioNet,setManualDisconnect]);
 const getWriteClient=useCallback(async()=>{
  if(!address)throw new Error("Connect the wallet shown in the header before signing.");
  return prepareStudioNet(address);
 },[address,prepareStudioNet]);
 const refresh=useCallback(async()=>{await syncWallet()},[syncWallet]);

 useEffect(()=>{
  const initialSync=window.setTimeout(()=>{void syncWallet()},0);
  const provider=window.ethereum;
  if(!provider)return()=>window.clearTimeout(initialSync);
  const accountsChanged=(accounts:unknown)=>{
   const account=firstAccount(accounts);
   if(!account){setManualDisconnect(false);clearSession();return}
   setManualDisconnect(false);
   setAddress(account);setStatus("connected");setError(undefined);void inspectNetwork();
  };
  const disconnected=()=>{setManualDisconnect(false);clearSession()};
  const chainChanged=()=>{void syncWallet()};
  const onVisible=()=>{if(document.visibilityState==="visible")void syncWallet()};
  const onReturn=()=>{void syncWallet()};
  provider.on?.("accountsChanged",accountsChanged);
  provider.on?.("disconnect",disconnected);
  provider.on?.("chainChanged",chainChanged);
  document.addEventListener("visibilitychange",onVisible);
  window.addEventListener("focus",onReturn);
  window.addEventListener("pageshow",onReturn);
  return()=>{
   window.clearTimeout(initialSync);
   provider.removeListener?.("accountsChanged",accountsChanged);
   provider.removeListener?.("disconnect",disconnected);
   provider.removeListener?.("chainChanged",chainChanged);
   document.removeEventListener("visibilitychange",onVisible);
   window.removeEventListener("focus",onReturn);
   window.removeEventListener("pageshow",onReturn);
  };
 },[clearSession,inspectNetwork,setManualDisconnect,syncWallet]);

 const disconnect=useCallback(()=>{setManualDisconnect(true);clearSession()},[clearSession,setManualDisconnect]);
 const value=useMemo(()=>({address,status,networkStatus,error,connect,disconnect,getWriteClient,refresh}),[address,status,networkStatus,error,connect,disconnect,getWriteClient,refresh]);
 return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useWallet(){const value=useContext(Context);if(!value)throw new Error("WalletProvider missing");return value}
