import { cookies } from "next/headers";

export const DEVICE_ID_COOKIE = "device_id";

export async function getDeviceId(): Promise<string | null> {
  const store = await cookies();
  return store.get(DEVICE_ID_COOKIE)?.value ?? null;
}
