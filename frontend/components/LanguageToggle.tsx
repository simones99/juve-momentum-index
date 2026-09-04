"use client";

import { useTransition } from "react";
import { setLocaleAction } from "@/lib/i18n/actions";
import { useLocale } from "@/lib/i18n/LocaleProvider";
import type { Locale } from "@/lib/i18n/dictionaries";

const OPTIONS: { value: Locale; label: string }[] = [
  { value: "it", label: "IT" },
  { value: "en", label: "EN" },
];

export function LanguageToggle() {
  const { locale } = useLocale();
  const [isPending, startTransition] = useTransition();

  return (
    <div className="lang-toggle" role="group" aria-label="Language">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          disabled={isPending}
          className={`lang-toggle__btn${locale === opt.value ? " lang-toggle__btn--active" : ""}`}
          onClick={() => startTransition(() => setLocaleAction(opt.value))}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
