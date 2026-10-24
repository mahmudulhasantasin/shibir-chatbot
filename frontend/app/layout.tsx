import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Shibir PDF Assistant - AI Chatbot",
  description: "AI-powered document knowledge base assistant powered by Qdrant and Gemini RAG.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
