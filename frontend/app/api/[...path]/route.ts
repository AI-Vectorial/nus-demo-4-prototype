/**
 * Same-origin proxy to the API.
 *
 * The browser cannot reach the API directly. `API_URL` is a server-side value
 * -- in a Codespace it is `http://localhost:8000`, which from a browser means
 * the laptop rather than the container, so a client-side fetch to it fails
 * while everything looks correct from the terminal.
 *
 * So the browser calls `/api/...` on the page's own origin, and this route --
 * running on the server, inside the container -- forwards to wherever the API
 * actually is. That holds in a Codespace, on Railway, and on a laptop without
 * any of them needing to know about the others.
 */

import { NextRequest } from "next/server";

import { apiUrl } from "@/lib/config";

export const dynamic = "force-dynamic";

// One definition of where the API is, shared with the server components --
// see lib/config.ts for why the default is 127.0.0.1 and not localhost.
const API = apiUrl();

async function forward(request: NextRequest, path: string[]) {
  const target = `${API}/${path.join("/")}${request.nextUrl.search}`;

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers: { "Content-Type": "application/json" },
      body: request.method === "GET" ? undefined : await request.text(),
      cache: "no-store",
    });
  } catch {
    // The API is down, not the page. Say which, because a 502 from the page
    // itself sends people looking at the wrong half of the system.
    return Response.json(
      { detail: `The API did not respond at ${API}.` },
      { status: 502 },
    );
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("Content-Type") ?? "application/json" },
  });
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return forward(request, (await context.params).path);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return forward(request, (await context.params).path);
}
