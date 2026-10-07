// Club crests are trademarks of the clubs, and football-data.org does not license them: whoever
// deploys the app must obtain the rights. They are therefore off unless explicitly enabled.
const SHOW_CRESTS = process.env.NEXT_PUBLIC_SHOW_CRESTS === "true";

export function TeamCrest({ url, name, size = 18 }: { url: string | null; name: string; size?: number }) {
  if (!url || !SHOW_CRESTS) return null;

  return (
    // eslint-disable-next-line @next/next/no-img-element -- external, per-team crest URLs; not worth next/image's remote-pattern config for a small static set
    <img
      src={url}
      alt=""
      width={size}
      height={size}
      style={{ objectFit: "contain", verticalAlign: "middle", marginRight: 6 }}
    />
  );
}
