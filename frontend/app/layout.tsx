import type { Metadata } from "next";
import { SidebarNav } from "@/components/SidebarNav";
import { getUpcomingMatches } from "@/lib/api";
import { TEAM_NAME } from "@/lib/constants";
import "./globals.css";

export const metadata: Metadata = {
  title: "Juve Momentum Index",
  description: "Momentum Index e Match Brief per la Juventus, basati su Elo e forma recente.",
};

function formatNextMatchDate(iso: string): string {
  return new Date(iso).toLocaleDateString("it-IT", { weekday: "short", day: "2-digit", month: "short" });
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const nextMatch = await getUpcomingMatches(1).catch(() => []);
  const upcoming = nextMatch[0];
  const opponent = upcoming ? (upcoming.home_team === TEAM_NAME ? upcoming.away_team : upcoming.home_team) : null;

  return (
    <html lang="it">
      <body>
        <div className="app-shell">
          <aside className="sidebar">
            <div className="sidebar__brand">
              <div className="sidebar__brand-mark">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M6 20V9.5L12 4l6 5.5V20"
                    stroke="#f5f5f7"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M10 20v-6h4v6"
                    stroke="var(--accent)"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <div className="sidebar__brand-text">
                <span className="sidebar__brand-name">Momentum</span>
                <span className="sidebar__brand-sub">JUVENTUS · JMI</span>
              </div>
            </div>

            <SidebarNav />

            <div className="sidebar__widget">
              <span className="sidebar__widget-label">Prossima partita</span>
              {upcoming ? (
                <>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>Juventus – {opponent}</span>
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                    {formatNextMatchDate(upcoming.match_date)} · {upcoming.competition}
                  </span>
                </>
              ) : (
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Nessuna partita in programma</span>
              )}
            </div>
          </aside>

          <main className="app-main">{children}</main>
        </div>
        <footer className="site-footer">
          Dati indicativi da football-data.org (fallback Wikipedia). Progetto personale, non affiliato alla Juventus FC.
        </footer>
      </body>
    </html>
  );
}
