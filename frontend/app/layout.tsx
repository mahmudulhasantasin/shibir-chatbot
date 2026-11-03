import type { Metadata } from "next";
import { Hind_Siliguri } from "next/font/google";
import "./globals.css";

const hindSiliguri = Hind_Siliguri({
  weight: ["400", "500", "600", "700"],
  subsets: ["bengali"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "সদস্য সহায়িকা",
  description: "বাংলাদেশ ইসলামী ছাত্রশিবিরের সদস্য সহায়িকা ও নোট সংক্রান্ত AI সহকারী।",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="bn" className="h-full">
      <body className={`${hindSiliguri.className} h-full antialiased`}>
        {children}
      </body>
    </html>
  );
}
