import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import {Noto_Sans_JP} from "next/font/google";
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
  title: "問題自動生成アプリ",
  description: "高校数学の演習プリントを乱数を用いて自動で生成し、PDFとしてダウンロードできるアプリです。",
};

const notoSansJP = Noto_Sans_JP({
  weight: ["400", "700"],
  subsets: ["latin"],
  display: "swap",
  variable: "--font-noto-sans-jp",
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ja"
      className={`${notoSansJP.variable} ${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-gray-200 text-gray-800 font-sans">
        <header className="bg-slate-700 text-white p-6 shadow-md">
          <h1 className="text-2xl font-bold text-center tracking-wider">
            高校数学演習問題自動生成アプリケーション
          </h1>
        </header>
        {children}
      </body>
    </html>
  );
}
