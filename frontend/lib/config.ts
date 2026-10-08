/**
 * Where the API is, read on the server at REQUEST time -- never baked into the
 * bundle -- so a deployment is repointed by changing API_URL and restarting.
 */
export function apiUrl(): string {
  return process.env.API_URL ?? "http://localhost:8000";
}
