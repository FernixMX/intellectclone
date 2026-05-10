"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

const NAV = [
  { label: "Directorio", href: "/directorio" },
  { label: "Red de colaboración", href: "/red" },
  { label: "Acerca", href: "/acerca" },
];

function LoginModal({ onClose }: { onClose: () => void }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const setToken = useAuthStore((s) => s.setToken);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) {
      setError("Ingresa la contraseña");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await api.login(password.trim());
      setToken(res.access_token);
      onClose();
    } catch {
      setError("Contraseña incorrecta");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.55)",
        zIndex: 200,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
      onClick={onClose}
    >
      <div
        className="card"
        style={{ padding: "var(--sp-8)", width: 340, textAlign: "center" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ fontSize: 32, marginBottom: "var(--sp-4)" }}>🔒</div>
        <div
          style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}
        >
          Panel de administración
        </div>
        <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: "var(--sp-5)" }}>
          Ingresa la contraseña de acceso
        </div>
        <form
          onSubmit={(e) => void handleSubmit(e)}
          style={{ display: "flex", flexDirection: "column", gap: 12 }}
        >
          <input
            type="password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              setError(null);
            }}
            placeholder="Contraseña"
            autoFocus
            style={{
              padding: "9px 12px",
              fontSize: 14,
              border: `1px solid ${error ? "var(--red)" : "var(--border-color)"}`,
              borderRadius: "var(--radius-md)",
              background: "var(--bg-surface)",
              color: "var(--text-primary)",
              outline: "none",
            }}
          />
          {error && (
            <div style={{ fontSize: 12, color: "var(--red)", textAlign: "left" }}>{error}</div>
          )}
          <button type="submit" className="btn btn-primary btn-sm" disabled={busy}>
            {busy ? "Accediendo…" : "Acceder"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function Header() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [mounted, setMounted] = useState(false);

  const { isAuthenticated, clearToken } = useAuthStore();

  useEffect(() => {
    setMounted(true);
  }, []);

  const authed = mounted && isAuthenticated();

  return (
    <>
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
          {authed ? (
            <>
              <Link
                href="/admin"
                className="btn btn-outline btn-sm"
                style={{ borderColor: "#2a4060", color: "#8da2b5" }}
              >
                Panel admin
              </Link>
              <button
                className="btn btn-ghost btn-sm"
                style={{ color: "#8da2b5" }}
                onClick={clearToken}
              >
                Salir
              </button>
            </>
          ) : (
            <button
              className="btn btn-outline btn-sm"
              style={{ borderColor: "#2a4060", color: "#8da2b5" }}
              onClick={() => setShowLogin(true)}
            >
              Iniciar sesión
            </button>
          )}
        </div>
      </header>

      {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
    </>
  );
}
