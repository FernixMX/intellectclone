import type { Metadata } from "next";
import "./globals.css";

const FONTS_URL =
  "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap";

export const metadata: Metadata = {
  title: "IntellectClone — UAT",
  description:
    "Gemelos digitales de la comunidad académica de la Universidad Autónoma de Tamaulipas",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href={FONTS_URL} rel="stylesheet" />
      </head>
      <body>{children}</body>
    </html>
  );
}
