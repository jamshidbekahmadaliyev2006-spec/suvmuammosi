import type { Metadata } from "next";
import { ThemeProvider } from "@/context/theme-context";
import { AuthProvider } from "@/context/auth-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "SuvNazorati — Suv Ta'minoti Muammolarini Monitoring Qilish",
  description:
    "Telegram manbalaridagi suv ta'minoti va kanalizatsiya bilan bog'liq xabarlarni avtomatik tahlil qilish va nazorat qilish platformasi.",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="uz" suppressHydrationWarning>
      <body className="bg-slate-50 text-slate-900 antialiased dark:bg-slate-950 dark:text-slate-100">
        <ThemeProvider>
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
