/**
 * The browser's way to the API: same origin, forwarded server-side.
 *
 * The browser never calls API_URL itself. In a Codespace "localhost:8000" is
 * the viewer's own machine and the forwarded port is private; on Railway the
 * backend would need every frontend origin allowed. Forwarding from here
 * sidesteps both, and API_URL is read per request, so repointing the frontend
 * needs a restart, not a rebuild.
 *
 * Only the routes the interface uses are forwarded -- this is not an open proxy.
 */

export const dynamic = "force-dynamic";

const FORWARDED = new Set(["ask", "healthz"]);

async function forward(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const path = (await params).path.join("/");
  if (!FORWARDED.has(path)) {
    return Response.json({ detail: "not found" }, { status: 404 });
  }

  const apiUrl = process.env.API_URL;
  if (!apiUrl) {
    return Response.json({ detail: "API_URL is not set" }, { status: 503 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${apiUrl}/${path}`, {
      method: request.method,
      headers: { "Content-Type": "application/json" },
      body: request.method === "GET" ? undefined : await request.text(),
      cache: "no-store",
    });
  } catch {
    return Response.json({ detail: `could not reach the API at ${apiUrl}` }, { status: 502 });
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("Content-Type") ?? "application/json" },
  });
}

export { forward as GET, forward as POST };
