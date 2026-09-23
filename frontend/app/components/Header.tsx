"use client"

import { useState } from "react";
import Link from "next/link";

const MENU_ITEMS =[
    {label: "トップページに戻る", href: "/",external: false},
    {label: "このアプリについて", href: "/about", external: false},
    {label: "開発者のX", href: "https://x.com/NormalSubGroup", external: true},
    {label: "お問い合わせ", href: "/contact", external: false},
];

export default function Header()
{
    const [isOpen,setIsOpen] = useState(false);
    return (
        <>
            <header className="bg-slate-700 text-white p-6 shadow-md relative">
                <h1 className="text-2xl font-bold text-center tracking-wider">
                    <a href="/" className="hover:opacity-80 transition-opacity">
                        高校数学演習問題自動生成アプリケーション
                    </a>
                </h1>

                <button
                onClick={() => setIsOpen(true)}
                aria-label="メニューを開く"
                className="absolute right-6 top-1/2 -translate-y-1/2 text-3xl leading-none" >
                ≡
                </button>
            </header>

            {/* 開いているときだけ黒幕を出す処理 */}
            {isOpen && (
            <div
                onClick={() => setIsOpen(false)}
                className="fixed inset-0 bg-black/40 z-40"
            />
            )}

            {/* スライドしてくるパネル*/}
            <nav
                className={`fixed top-0 right-0 h-full w-72 bg-black text-white z-50 shadow-xl transition-transform duration-300 ${isOpen ? "translate-x-0" : "translate-x-full"}`}
            >
                <button
                    onClick={() => setIsOpen(false)}
                    aria-label="メニューを閉じる"
                    className="absolute right-4 top-4 text-2xl"
                >
                    x
                </button>

                <ul className="mt-16">
                    {MENU_ITEMS.map((item) => (
                        <li key={item.href}>
                            {item.external ? (
                                
                                <a
                                href={item.href}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block px-6 py-4 hover:bg-slate-700 transition-colors"
                                >
                                {item.label} ↗
                                </a>
                            ) : (
                                <Link
                                href={item.href}
                                onClick={() => setIsOpen(false)}
                                className="block px-6 py-4 hover:bg-slate-700 transition-colors"
                                >
                                {item.label}
                                </Link>
                            )}
                        </li>
                    ))}
                </ul>
            </nav>
        </>
    )
}