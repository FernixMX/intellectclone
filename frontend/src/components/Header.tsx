"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { label: "Directorio", href: "/directorio" },
  { label: "Red de colaboración", href: "/red" },
  { label: "Acerca", href: "/acerca" },
];

export default function Header() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="pub-header">
      <Link href="/" style={{ display: "flex", flexDirection: "column", gap: 1 }}>
        <span className="sidebar-logo-uat">UAT</span>
        <span className="sidebar-logo-sub">IntellectClone</span>
      </Link>

      <nav className={menuOpen ? "pub-nav open" : "pub-nav"}>
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={pathname.startsWith(item.href) ? "pub-nav-item active" : "pub-nav-item"}
            onClick={() => setMenuOpen(false)}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <button
        className="pub-hamburger"
        onClick={() => setMenuOpen((o) => !o)}
        aria-label="Menú de navegación"
      >
        <span />
        <span />
        <span />
      </button>

      <div className="pub-header-login" style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
        <button
          className="btn btn-outline btn-sm"
          style={{ borderColor: "#2a4060", color: "#8da2b5" }}
        >
          Iniciar sesión
        </button>
      </div>
    </header>
  );
}
