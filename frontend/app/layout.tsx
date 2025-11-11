import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Arandu Repro",
  description: "Minimal reproducibility pipeline for AI papers",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
