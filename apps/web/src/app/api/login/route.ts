import { NextRequest, NextResponse } from "next/server";

// See apiProxy/[...path]/route.ts for why this differs from NEXT_PUBLIC_API_URL.
const API_URL =
  process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_BASE = `${API_URL}/api/v1`;
const TOKEN_KEY = "auth_token";
const MAX_AGE_SECONDS = 60 * 60 * 24 * 7; // 7 days, matches backend JWT_EXPIRE_MINUTES

export async function POST(request: NextRequest) {
  const { email, password } = (await request.json()) as {
    email?: string;
    password?: string;
  };
  if (!email || !password) {
    return NextResponse.json({ detail: "Email and password required" }, { status: 400 });
  }

  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);

  const loginRes = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
  if (!loginRes.ok) {
    const err = await loginRes.json().catch(() => ({}));
    return NextResponse.json(
      { detail: (err as { detail?: string }).detail || "Login failed" },
      { status: loginRes.status }
    );
  }
  const { access_token } = (await loginRes.json()) as { access_token: string };

  const meRes = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${access_token}` },
  });
  if (!meRes.ok) {
    return NextResponse.json({ detail: "Login failed" }, { status: 502 });
  }
  const user = await meRes.json();

  // Secure must reflect whether THIS request actually arrived over HTTPS, not
  // just NODE_ENV — a production build served over plain HTTP (e.g. this
  // docker-compose dev stack) would otherwise get a cookie no real browser
  // ever sends back. Falls back to X-Forwarded-Proto behind a TLS-terminating proxy.
  const isHttps =
    request.nextUrl.protocol === "https:" || request.headers.get("x-forwarded-proto") === "https";

  const response = NextResponse.json({ user });
  response.cookies.set(TOKEN_KEY, access_token, {
    httpOnly: true,
    secure: isHttps,
    sameSite: "lax",
    path: "/",
    maxAge: MAX_AGE_SECONDS,
  });
  return response;
}
