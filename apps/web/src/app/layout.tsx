import type { Metadata } from "next";
import "./globals.css";
import { DemoProvider } from "@/components/kawteam";

export const metadata: Metadata = {
  title: "KawTeam — A little less searching",
  description: "Start a conversation. Find the right vendors, keep your projects together, and make the final call with your team.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body><DemoProvider>{children}</DemoProvider></body>
    </html>
  );
}
