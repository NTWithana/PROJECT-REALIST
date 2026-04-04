"use client";

import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ReactNode } from "react";
import { CatalystOSProvider } from "@/lib/os/useCatalystOS";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html>
      <body>
        <CatalystOSProvider>
          {children}
        </CatalystOSProvider>
      </body>
    </html>
  );
}
