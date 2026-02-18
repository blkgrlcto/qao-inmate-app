import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxy(request, params, "GET");
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxy(request, params, "POST");
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxy(request, params, "PATCH");
}

async function proxy(
  request: NextRequest,
  params: Promise<{ path: string[] }>,
  method: string
) {
  const { path } = await params;
  const pathStr = path.join("/");
  const url = new URL(request.url);
  const target = `${API_URL}/api/v1/${pathStr}${url.search}`;
  const token = request.cookies.get("auth_token")?.value;

  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  request.headers.forEach((v, k) => {
    if (k.toLowerCase() !== "host" && k.toLowerCase() !== "cookie") {
      headers[k] = v;
    }
  });

  const init: RequestInit = {
    method,
    headers,
  };
  if (method !== "GET" && method !== "HEAD") {
    init.body = await request.text();
    if (request.headers.get("content-type")) {
      (init.headers as Record<string, string>)["Content-Type"] =
        request.headers.get("content-type")!;
    }
  }

  const res = await fetch(target, init);
  const contentType = res.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const body = isJson ? await res.json() : await res.arrayBuffer();

  const responseHeaders: Record<string, string> = {
    "Content-Type": contentType,
  };
  const contentDisposition = res.headers.get("content-disposition");
  if (contentDisposition) responseHeaders["Content-Disposition"] = contentDisposition;

  return new NextResponse(body, {
    status: res.status,
    headers: responseHeaders,
  });
}
