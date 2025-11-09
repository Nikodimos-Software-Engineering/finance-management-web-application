"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname() || "/";
  const [open, setOpen] = useState(false);

  if (pathname === "/" || pathname === "/dashboard" || pathname === "/login" || pathname === "/register") return null;

  const links = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/transactions", label: "Transaction" },
    { href: "/budget", label: "Budget" },
    { href: "/savings-goals", label: "Savings Goals" },
  ];

  const findActive = () => {
    const exact = links.find((l) => l.href === pathname);
    if (exact) return exact;
    const starts = links.find((l) => pathname.startsWith(l.href + "/"));
    if (starts) return starts;
    if (pathname === "/") return links.find((l) => l.href === "/dashboard") || links[0];
    const parts = pathname.split("/").filter(Boolean);
    const label = parts.length ? parts[0].replace(/-/g, " ") : "App";
    return { href: pathname, label: label.charAt(0).toUpperCase() + label.slice(1) };
  };

  const active = findActive();

  const isActive = (href) => {
    return active && href === active.href;
  };

  return (
    <header className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center">
            <Link href="/" className="text-lg font-semibold text-gray-900">
              Finance Tracker
            </Link>
          </div>

          {/* Desktop links */}
          <nav className="hidden md:flex items-center space-x-4">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={`text-sm px-3 py-1 rounded ${isActive(l.href) ? "text-gray-900 font-semibold" : "text-gray-600 hover:text-gray-900"}`}
              >
                {l.label}
              </Link>
            ))}
          </nav>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setOpen((v) => !v)}
              aria-label="Toggle menu"
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-gray-900 focus:outline-none"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {open ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile panel */}
      {open && (
        <div className="md:hidden border-t bg-white">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className={`block px-3 py-2 rounded ${isActive(l.href) ? "text-gray-900 font-semibold" : "text-gray-600 hover:text-gray-900"}`}
              >
                {l.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
