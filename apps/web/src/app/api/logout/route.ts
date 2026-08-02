import { NextRequest, NextResponse } from "next/server";
import { AUTH_TOKEN_KEY, REFRESH_TOKEN_KEY, cookieOptions } from "@/lib/authCookies";

export async function POST(request: NextRequest) {
  const response = NextResponse.json({ ok: true });
  // maxAge: 0 clears the cookie; other attributes must still match how it was
  // set (see cookieOptions) or the browser won't accept this as a valid overwrite.
  response.cookies.set(AUTH_TOKEN_KEY, "", cookieOptions(request, 0));
  response.cookies.set(REFRESH_TOKEN_KEY, "", cookieOptions(request, 0));
  return response;
}
