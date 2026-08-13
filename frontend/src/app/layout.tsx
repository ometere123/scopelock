import type { Metadata } from "next";
import "./globals.css";
import { WalletProvider } from "@/components/wallet-provider";
import { AppShell } from "@/components/app-shell";

export const metadata: Metadata = { title: "ScopeLock: public security disclosure settlement", description: "Public findings. Bound scope. Consensus settlement." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body><WalletProvider><AppShell>{children}</AppShell></WalletProvider></body></html>; }
