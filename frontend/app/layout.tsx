import type { Metadata } from "next";
import { SidebarNav } from "@/components/SidebarNav";
import { LanguageToggle } from "@/components/LanguageToggle";
import { PushOptIn } from "@/components/PushOptIn";
import { LiveMatchBanner } from "@/components/LiveMatchBanner";
import { getHealthz, getUpcomingMatches } from "@/lib/api";
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

// YYYY-MM-DD for `date` as seen in Europe/Rome, for same-day comparisons that
// don't fall prey to UTC-vs-Rome day-boundary drift.
function formatDateKeyInRome(date: Date): string {
  return date.toLocaleDateString("en-CA", { timeZone: "Europe/Rome" });
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const { locale, dict } = await getDictionary();
  const [nextMatch, healthz] = await Promise.all([
    getUpcomingMatches(1).catch(() => []),
    getHealthz().catch(() => null),
  ]);
  const upcoming = nextMatch[0];
  const ingestDate = healthz?.last_successful_ingest_at ? new Date(healthz.last_successful_ingest_at) : null;
  const lastUpdatedTime = ingestDate
    ? ingestDate.toLocaleTimeString(locale === "en" ? "en-GB" : "it-IT", {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Europe/Rome",
      })
    : null;
  const lastUpdatedDate =
    ingestDate && formatDateKeyInRome(ingestDate) !== formatDateKeyInRome(new Date())
      ? ingestDate.toLocaleDateString(locale === "en" ? "en-GB" : "it-IT", {
          day: "2-digit",
          month: "short",
          timeZone: "Europe/Rome",
        })
      : null;
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
              <PushOptIn />

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
          <footer className="site-footer">
            <div>{dict.footer}</div>
            {lastUpdatedTime && (
              <div style={{ marginTop: 4 }}>
                {lastUpdatedDate
                  ? dict.footerUpdatedAtOn(lastUpdatedDate, lastUpdatedTime)
                  : dict.footerUpdatedAt(lastUpdatedTime)}
              </div>
            )}
          </footer>
        </LocaleProvider>
      </body>
    </html>
  );
}
