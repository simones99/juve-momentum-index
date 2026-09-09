import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { DEVICE_ID_COOKIE } from "@/lib/deviceId";

// Anonymous device id, used to attribute predictions to a browser without
// accounts/login. Set once, read by server components via getDeviceId().
export function proxy(request: NextRequest) {
  if (request.cookies.has(DEVICE_ID_COOKIE)) return NextResponse.next();

  const deviceId = crypto.randomUUID();

  // Also forward it on the request so THIS render (not just the next one)
  // can already see it via cookies() — otherwise getDeviceId() returns null
  // for the very first page a visitor hits.
  const requestHeaders = new Headers(request.headers);
  const existingCookie = request.headers.get("cookie");
  requestHeaders.set(
    "cookie",
    existingCookie ? `${existingCookie}; ${DEVICE_ID_COOKIE}=${deviceId}` : `${DEVICE_ID_COOKIE}=${deviceId}`
  );

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.cookies.set(DEVICE_ID_COOKIE, deviceId, {
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
    sameSite: "lax",
  });
  return response;
}
