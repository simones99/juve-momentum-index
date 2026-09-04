"use client";

import { createContext, useContext } from "react";
import { dictionaries, type Dictionary, type Locale } from "./dictionaries";

const LocaleContext = createContext<Locale | null>(null);

export function LocaleProvider({ locale, children }: { locale: Locale; children: React.ReactNode }) {
  return <LocaleContext.Provider value={locale}>{children}</LocaleContext.Provider>;
}

export function useLocale(): { locale: Locale; dict: Dictionary } {
  const locale = useContext(LocaleContext);
  const resolved = locale ?? "it";
  return { locale: resolved, dict: dictionaries[resolved] };
}
