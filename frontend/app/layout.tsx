import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Juve Momentum Index",
  description: "Momentum Index e Match Brief per la Juventus, basati su Elo e forma recente.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body>
        <header className="site-header">
          <div className="site-header__inner">
            <span className="brand">Juve Momentum Index</span>
            <nav className="nav">
              <Link href="/">Overview</Link>
              <Link href="/momentum">Momentum Details</Link>
              <Link href="/matches">Matches</Link>
              <Link href="/brief/next">Match Brief</Link>
              <Link href="/trasferte">Trasferte</Link>
            </nav>
          </div>
        </header>
        <main className="page">{children}</main>
        <footer className="site-footer">
          Dati indicativi da football-data.org (fallback Wikipedia). Progetto personale, non affiliato alla Juventus FC.
        </footer>
      </body>
    </html>
  );
}
