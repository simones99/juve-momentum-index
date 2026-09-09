"use client";

import { useEffect, useState } from "react";
import { subscribeToPush, unsubscribeFromPush } from "@/lib/api";
import { useLocale } from "@/lib/i18n/LocaleProvider";

const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY;

// Web Push wants the VAPID key as a Uint8Array; browsers hand it back base64url-encoded.
function urlBase64ToUint8Array(base64Url: string): Uint8Array {
  const padding = "=".repeat((4 - (base64Url.length % 4)) % 4);
  const base64 = (base64Url + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  return Uint8Array.from([...raw].map((char) => char.charCodeAt(0)));
}

type Status = "unsupported" | "loading" | "off" | "on" | "denied";

export function PushOptIn() {
  const { locale, dict } = useLocale();
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    let cancelled = false;

    async function checkSupport() {
      if (!VAPID_PUBLIC_KEY || !("serviceWorker" in navigator) || !("PushManager" in window)) {
        if (!cancelled) setStatus("unsupported");
        return;
      }
      try {
        const registration = await navigator.serviceWorker.register("/sw.js");
        const subscription = await registration.pushManager.getSubscription();
        if (!cancelled) setStatus(subscription ? "on" : "off");
      } catch {
        if (!cancelled) setStatus("unsupported");
      }
    }

    checkSupport();
    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "unsupported" || status === "loading") return null;

  async function handleClick() {
    const registration = await navigator.serviceWorker.ready;

    if (status === "on") {
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        await unsubscribeFromPush(subscription.endpoint).catch(() => {});
        await subscription.unsubscribe();
      }
      setStatus("off");
      return;
    }

    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      setStatus("denied");
      return;
    }

    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY!),
    });
    await subscribeToPush(subscription, locale);
    setStatus("on");
  }

  return (
    <div className="lang-toggle" role="group" aria-label={dict.push.label}>
      <button
        type="button"
        className={`lang-toggle__btn${status === "on" ? " lang-toggle__btn--active" : ""}`}
        onClick={handleClick}
        title={status === "denied" ? dict.push.permissionDenied : undefined}
      >
        {status === "on" ? dict.push.enabled : dict.push.enable}
      </button>
    </div>
  );
}
