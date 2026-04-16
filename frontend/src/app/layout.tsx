import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/components/providers";

export const metadata: Metadata = {
  title: "FinEngine — Personal Financial Intelligence Engine",
  description:
    "AI-powered financial strategy orchestrator. Get quantified, simulation-backed, explainable recommendations for complex multi-variable financial decisions.",
  keywords: [
    "financial planning",
    "AI finance",
    "portfolio management",
    "loan analysis",
    "insurance gap",
    "Monte Carlo simulation",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
      </head>
      <body className="min-h-screen bg-surface-950">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
