export function TeamCrest({ url, name, size = 18 }: { url: string | null; name: string; size?: number }) {
  if (!url) return null;

  return (
    // eslint-disable-next-line @next/next/no-img-element -- external, per-team crest URLs; not worth next/image's remote-pattern config for a small static set
    <img
      src={url}
      alt={name}
      width={size}
      height={size}
      style={{ objectFit: "contain", verticalAlign: "middle", marginRight: 6 }}
    />
  );
}
