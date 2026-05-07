"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { label: "Directorio", href: "/directorio" },
  { label: "Red de colaboración", href: "/red" },
  { label: "Acerca", href: "/acerca" },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="pub-header">
      <Link href="/" style={{ display: "flex", flexDirection: "column", gap: 1 }}>
        <span className="sidebar-logo-uat">UAT</span>
        <span className="sidebar-logo-sub">IntellectClone</span>
      </Link>

      <nav style={{ display: "flex", gap: 4, marginLeft: 24 }}>
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={pathname.startsWith(item.href) ? "pub-nav-item active" : "pub-nav-item"}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
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
