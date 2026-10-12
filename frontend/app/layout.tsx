import type { Metadata, Viewport } from "next";
import "./globals.css";

/**
 * The tab is the first thing anyone sees and the last thing anyone fixes.
 *
 * Five tables will have this open side by side on a projector, so the title has
 * to say what the product is rather than what framework built it, and the icon
 * has to survive 16px on browser chrome that may be light or dark. The mark
 * itself lives in icon.svg, with the reasoning for its shape.
 *
 * `template` is the part that keeps paying: give a route `title: "Corpus"` in
 * its own metadata export and the tab reads "Corpus · Policy Assistant" without
 * anyone repeating the product name. F7 and F8 get it for free.
 */
export const metadata: Metadata = {
  title: {
    default: "Policy Assistant · Aldermere Bank",
    template: "%s · Policy Assistant",
  },
  description:
    "Ask a question about Aldermere Bank policy in plain language. Every answer " +
    "cites the sections it came from, and when the policy corpus cannot support " +
    "an answer it says so rather than guessing.",
  applicationName: "Policy Assistant",
  // Nothing here is public, and a half-built teaching corpus about a bank that
  // does not exist is the last thing that should turn up in a search result.
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  // Matches --bg, so mobile browser chrome continues the page instead of
  // drawing a line across the top of it.
  themeColor: "#fafafc",
  colorScheme: "light",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
