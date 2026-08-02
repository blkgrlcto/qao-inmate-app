import { NextRequest } from "next/server";

export const AUTH_TOKEN_KEY = "auth_token";
export const REFRESH_TOKEN_KEY = "refresh_token";
export const ACCESS_TOKEN_MAX_AGE = 60 * 30; // 30 min — matches backend JWT_EXPIRE_MINUTES
export const REFRESH_TOKEN_MAX_AGE = 60 * 60 * 24 * 7; // 7 days — matches backend JWT_REFRESH_EXPIRE_MINUTES

// See apiProxy/[...path]/route.ts for why this differs from NEXT_PUBLIC_API_URL.
export const API_URL =
  process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const API_BASE = `${API_URL}/api/v1`;

// Secure must reflect whether THIS request actually arrived over HTTPS, not
// just NODE_ENV — a production build served over plain HTTP (e.g. this
// docker-compose dev stack) would otherwise get a cookie no real browser ever
// sends back. Falls back to X-Forwarded-Proto behind a TLS-terminating proxy.
export function isHttpsRequest(request: NextRequest): boolean {
  return request.nextUrl.protocol === "https:" || request.headers.get("x-forwarded-proto") === "https";
}

export function cookieOptions(request: NextRequest, maxAge: number) {
  return {
    httpOnly: true as const,
    secure: isHttpsRequest(request),
    sameSite: "lax" as const,
    path: "/",
    maxAge,
  };
}
