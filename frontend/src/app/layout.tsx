import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: "ScopeLock — public security disclosure settlement", description: "Public findings. Bound scope. Consensus settlement." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
