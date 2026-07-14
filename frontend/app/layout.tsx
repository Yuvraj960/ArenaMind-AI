import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ArenaMind AI — FIFA WC 2026 Stadium OS",
  description:
    "Generative AI Operating System for FIFA World Cup 2026 Venues — serving Fans, Operations, Emergency, and Volunteers in real-time.",
  icons: {
    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='14' fill='%232a4bdb'/><text y='22' x='6' font-size='18'>⚡</text></svg>",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-slate-50">
        {children}
      </body>
    </html>
  );
}