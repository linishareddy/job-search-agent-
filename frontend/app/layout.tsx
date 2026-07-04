import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Providers } from "./providers";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Job Radar — AI Job Search Agent",
  description:
    "Describe your ideal role in plain English. Job Radar parses intent with AI, fetches from 6 job sources, and ranks matches with relevance scores, reasons, and gaps.",
  applicationName: "Job Radar",
  keywords: [
    "job search",
    "AI jobs",
    "remote jobs",
    "job alerts",
    "Adzuna",
    "Greenhouse",
  ],
  openGraph: {
    title: "Job Radar — AI Job Search Agent",
    description:
      "Personal AI job radar: natural-language searches, multi-source fetching, and explained match scores.",
    type: "website",
  },
  manifest: "/manifest.json",
  icons: {
    icon: [{ url: "/icon.svg", type: "image/svg+xml" }],
    apple: [{ url: "/icon.svg", type: "image/svg+xml" }],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} font-sans`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
