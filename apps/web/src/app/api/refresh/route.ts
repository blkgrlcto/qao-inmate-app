import { NextRequest, NextResponse } from "next/server";
import { ACCESS_TOKEN_MAX_AGE, API_BASE, AUTH_TOKEN_KEY, REFRESH_TOKEN_KEY, cookieOptions } from "@/lib/authCookies";

export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get(REFRESH_TOKEN_KEY)?.value;
  if (!refreshToken) {
    return NextResponse.json({ detail: "No refresh token" }, { status: 401 });
  }

  const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!refreshRes.ok) {
    return NextResponse.json({ detail: "Refresh failed" }, { status: refreshRes.status });
  }
  const { access_token } = (await refreshRes.json()) as { access_token: string };

  const response = NextResponse.json({ ok: true });
  response.cookies.set(AUTH_TOKEN_KEY, access_token, cookieOptions(request, ACCESS_TOKEN_MAX_AGE));
  return response;
}
