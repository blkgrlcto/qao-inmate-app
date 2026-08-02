import { NextRequest, NextResponse } from "next/server";

const TOKEN_KEY = "auth_token";

export async function POST(request: NextRequest) {
  // Must match how the cookie was set in api/login/route.ts, or the browser
  // won't accept this as a valid overwrite of a Secure cookie.
  const isHttps =
    request.nextUrl.protocol === "https:" || request.headers.get("x-forwarded-proto") === "https";

  const response = NextResponse.json({ ok: true });
  response.cookies.set(TOKEN_KEY, "", {
    httpOnly: true,
    secure: isHttps,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  return response;
}
