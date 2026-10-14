/**
 * Where the API is, for code running on the SERVER -- server components and
 * the /api proxy -- read at request time so a deployment is repointed by
 * changing API_URL and restarting. The browser never uses this: it calls /api
 * on its own origin (app/api/[...path]).
 *
 * 127.0.0.1, not localhost: Node resolves localhost to ::1 first, and uvicorn
 * binds IPv4 only, so a server-side fetch to localhost is refused.
 */
export function apiUrl(): string {
  return process.env.API_URL ?? "http://127.0.0.1:8000";
}
