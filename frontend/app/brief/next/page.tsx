import { ApiError, getNextMatchBrief } from "@/lib/api";
import { MatchBriefCard } from "@/components/MatchBriefCard";
import { getDictionary } from "@/lib/i18n/server";

export default async function NextMatchBriefPage() {
  const { locale, dict } = await getDictionary();

  let brief;
  try {
    brief = await getNextMatchBrief(locale);
  } catch (err) {
    if (err instanceof ApiError) {
      return (
        <>
          <h1>{dict.brief.title}</h1>
          <div className="card empty-state">{dict.brief.noBriefFound}</div>
        </>
      );
    }
    throw err;
  }

  return (
    <>
      <h1>{dict.brief.title}</h1>
      <p className="subtitle">{dict.brief.subtitle}</p>
      <MatchBriefCard brief={brief} />
    </>
  );
}
