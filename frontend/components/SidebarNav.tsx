"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  {
    href: "/",
    label: "Overview",
    icon: (
      <path d="M4 18V13M10 18V9M16 18V5M22 18V11" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    ),
  },
  {
    href: "/momentum",
    label: "Momentum Details",
    icon: (
      <>
        <circle cx="12" cy="12" r="8.5" stroke="currentColor" strokeWidth="1.7" />
        <path d="M12 7.5v5l3.2 2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
      </>
    ),
  },
  {
    href: "/matches",
    label: "Matches",
    icon: (
      <>
        <rect x="3.5" y="5" width="17" height="14" rx="3" stroke="currentColor" strokeWidth="1.7" />
        <path d="M3.5 9.5h17M8 5v14" stroke="currentColor" strokeWidth="1.7" />
      </>
    ),
  },
  {
    href: "/brief/next",
    label: "Match Brief",
    icon: (
      <path
        d="M12 3l1.8 4.6L18.5 9l-4.4 2.3.4 5-2.5-2.8-2.5 2.8.4-5L5.5 9l4.7-1.4L12 3z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    ),
  },
  {
    href: "/trasferte",
    label: "Trasferte",
    icon: (
      <>
        <path
          d="M12 21s7-6.1 7-11.5A7 7 0 0 0 5 9.5C5 14.9 12 21 12 21z"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinejoin="round"
        />
        <circle cx="12" cy="9.5" r="2.4" stroke="currentColor" strokeWidth="1.7" />
      </>
    ),
  },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <nav className="sidebar__nav">
      {ITEMS.map((item) => {
        const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`sidebar__nav-item${active ? " sidebar__nav-item--active" : ""}`}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              {item.icon}
            </svg>
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
