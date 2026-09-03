import { TrasferteExplorer } from "@/components/travel/TrasferteExplorer";

export default function TrasfertePage() {
  return (
    <>
      <h1>Trasferte</h1>
      <p className="subtitle">
        Trova le prossime trasferte della Juve più facili da raggiungere dalla tua città.
      </p>
      <TrasferteExplorer />
    </>
  );
}
