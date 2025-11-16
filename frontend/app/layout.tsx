import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Arandu Repro - Paper Hosting",
  description: "Host and view scientific papers",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
