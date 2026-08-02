import { NextRequest, NextResponse } from "next/server";
import {
  ACCESS_TOKEN_MAX_AGE,
  API_BASE,
  AUTH_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  REFRESH_TOKEN_MAX_AGE,
  cookieOptions,
} from "@/lib/authCookies";

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
  const { access_token, refresh_token } = (await loginRes.json()) as {
    access_token: string;
    refresh_token: string;
  };

  const meRes = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${access_token}` },
  });
  if (!meRes.ok) {
    return NextResponse.json({ detail: "Login failed" }, { status: 502 });
  }
  const user = await meRes.json();

  const response = NextResponse.json({ user });
  response.cookies.set(AUTH_TOKEN_KEY, access_token, cookieOptions(request, ACCESS_TOKEN_MAX_AGE));
  response.cookies.set(REFRESH_TOKEN_KEY, refresh_token, cookieOptions(request, REFRESH_TOKEN_MAX_AGE));
  return response;
}
