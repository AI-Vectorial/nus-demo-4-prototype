import type { Metadata } from "next";
import { Space_Grotesk } from "next/font/google";

import "./globals.css";

/**
 * Module 3's typeface, loaded the way Next loads fonts: self-hosted at build
 * time, so there is no request to a third party on first paint and no layout
 * shift when the font lands. A raw <link> to Google would give up both.
 *
 * The variable is what app/globals.css reads; the class on <body> is what
 * applies it, with system-ui behind it for the moment before it is ready.
 */
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
  variable: "--font-sans",
  fallback: ["system-ui", "sans-serif"],
});

export const metadata: Metadata = {
  title: "Policy Assistant",
  description:
    "Ask questions about internal policy. Answers cite the sections they came from.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={spaceGrotesk.variable}>
      <body className={spaceGrotesk.className}>{children}</body>
    </html>
  );
}
