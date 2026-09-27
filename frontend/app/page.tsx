import Chat from "@/components/Chat";

// The browser talks to this app's own /api routes, which forward to API_URL
// server-side -- see app/api/[...path]/route.ts. So nothing about the backend's
// location reaches the client bundle, and changing API_URL needs only a restart.
export default function Home() {
  return <Chat apiUrl="/api" />;
}
