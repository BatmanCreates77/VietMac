import { Inter } from "next/font/google";
import "./globals.css";

import { Analytics } from "@vercel/analytics/next";
import { PostHogProvider } from "./providers/posthog-provider";

const inter = Inter({
  subsets: ["latin"],
});

export const metadata = {
  title: "VietMac Compare - Best MacBook Prices in Vietnam",
  description:
    "Compare live MacBook Pro prices from Vietnam's top retailers with VAT refunds for Indian tourists",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <PostHogProvider>{children}</PostHogProvider>
        <Analytics />
      </body>
    </html>
  );
}
