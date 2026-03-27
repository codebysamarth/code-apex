import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { SelectedReqProvider } from "@/context/SelectedReqContext";
import { cn } from "@/lib/utils";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ApexBRD | Production AI Requirement Extraction",
  description: "Next-generation BRD extraction engine for enterprise systems analysis.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className={cn(
        inter.className, 
        "bg-[#f7f7f5] text-[rgba(55,53,47,1)] antialiased overflow-hidden"
      )}>
        <SelectedReqProvider>
          {children}
        </SelectedReqProvider>
      </body>
    </html>
  );
}
