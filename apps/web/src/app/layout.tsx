import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { DemoProvider } from "@/components/kawteam";
import { Aurora } from "@/components/aurora";

const heros=localFont({src:[
 {path:"./fonts/texgyreheros-regular.otf",weight:"400",style:"normal"},
 {path:"./fonts/texgyreheros-italic.otf",weight:"400",style:"italic"},
 {path:"./fonts/texgyreheros-bold.otf",weight:"700",style:"normal"},
 {path:"./fonts/texgyreheros-bolditalic.otf",weight:"700",style:"italic"},
],variable:"--font-heros",display:"swap"});

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
    <html lang="en" className={heros.variable}>
      <body><Aurora/><DemoProvider>{children}</DemoProvider></body>
    </html>
  );
}
