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
  // In development the page talks to its own origin and next.config.ts
  // forwards /api to the API -- see the comment there.
  const apiUrl =
    process.env.NODE_ENV === "development"
      ? "/api"
      : (process.env.API_URL ?? "http://localhost:8000");
  return <Chat apiUrl={apiUrl} />;
}
