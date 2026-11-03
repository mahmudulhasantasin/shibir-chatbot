import type { Metadata } from "next";
import { Hind_Siliguri } from "next/font/google";
import "./globals.css";

const hindSiliguri = Hind_Siliguri({
  weight: ["400", "500", "600", "700"],
  subsets: ["bengali"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "শিবির পিডিএফ সহায়ক",
  description: "ইসলামী ছাত্রশিবিরের দলিল-সংক্রান্ত AI সহায়ক।",
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
