import { TrasferteExplorer } from "@/components/travel/TrasferteExplorer";
import { getDictionary } from "@/lib/i18n/server";

export default async function TrasfertePage() {
  const { dict } = await getDictionary();
  return (
    <>
      <h1>{dict.nav.trasferte}</h1>
      <p className="subtitle">{dict.trasferte.subtitle}</p>
      <TrasferteExplorer />
    </>
  );
}
