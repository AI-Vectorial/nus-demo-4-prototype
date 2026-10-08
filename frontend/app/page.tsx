import Chat from "@/components/Chat";

// Server component. It reads the API location at REQUEST time, not build time.
//
// NEXT_PUBLIC_* variables are baked into the client bundle when `next build`
// runs, so changing one means rebuilding. Reading it here instead means the
// deployment can be pointed at a different API by changing an environment
// variable and restarting -- which is what a table will expect when they change
// configuration, and what an operator expects when they roll something back.
export const dynamic = "force-dynamic";

export default function Home() {
  // The browser calls our own origin, and app/api/[...path] forwards to the
  // real API from the server. Handing a client component API_URL directly
  // would have it fetch localhost:8000 from the laptop, which is nothing.
  const apiUrl = "/api";
  return <Chat apiUrl={apiUrl} />;
}
