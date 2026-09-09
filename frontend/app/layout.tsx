import type { Metadata } from "next";
import { SidebarNav } from "@/components/SidebarNav";
import { LanguageToggle } from "@/components/LanguageToggle";
import { LiveMatchBanner } from "@/components/LiveMatchBanner";
import { getUpcomingMatches } from "@/lib/api";
import { TEAM_NAME } from "@/lib/constants";
import { getDictionary } from "@/lib/i18n/server";
import { LocaleProvider } from "@/lib/i18n/LocaleProvider";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const { locale } = await getDictionary();
  return {
    title: "Juve Momentum Index",
    description:
      locale === "en"
        ? "Momentum Index and Match Brief for Juventus, based on Elo and recent form."
        : "Momentum Index e Match Brief per la Juventus, basati su Elo e forma recente.",
  };
}

function formatNextMatchDate(iso: string, locale: string): string {
  return new Date(iso).toLocaleDateString(locale === "en" ? "en-GB" : "it-IT", {
    weekday: "short",
    day: "2-digit",
    month: "short",
  });
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const { locale, dict } = await getDictionary();
  const nextMatch = await getUpcomingMatches(1).catch(() => []);
  const upcoming = nextMatch[0];
  const opponent = upcoming ? (upcoming.home_team === TEAM_NAME ? upcoming.away_team : upcoming.home_team) : null;

  return (
    <html lang={dict.htmlLang}>
      <body>
        <LocaleProvider locale={locale}>
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

              <LanguageToggle />

              <div className="sidebar__widget">
                <span className="sidebar__widget-label">{dict.sidebar.nextMatch}</span>
                {upcoming ? (
                  <>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Juventus – {opponent}</span>
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      {formatNextMatchDate(upcoming.match_date, locale)} · {upcoming.competition}
                    </span>
                  </>
                ) : (
                  <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{dict.sidebar.noUpcoming}</span>
                )}
              </div>
            </aside>

            <main className="app-main">
              <LiveMatchBanner />
              {children}
            </main>
          </div>
          <footer className="site-footer">{dict.footer}</footer>
        </LocaleProvider>
      </body>
    </html>
  );
}
