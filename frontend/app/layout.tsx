import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Policy Assistant",
  description:
    "Ask questions about internal policy. Answers cite the sections they came from.",
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
