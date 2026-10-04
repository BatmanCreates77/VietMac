import { Inter } from "next/font/google";
import "./globals.css";

import { Analytics } from "@vercel/analytics/next";
import { GoogleAnalytics } from "@next/third-parties/google";
import { ANALYTICS_ENABLED, GA_MEASUREMENT_ID } from "@/lib/analytics-config";
import { PostHogProvider } from "./providers/posthog-provider";

const inter = Inter({
  subsets: ["latin"],
});

export const metadata = {
  title: "VietMac Compare - Best MacBook & iPhone Prices in Vietnam",
  description:
    "Compare live MacBook, Mac and iPhone prices from Vietnam's top Apple retailers with VAT refunds for tourists",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <PostHogProvider>{children}</PostHogProvider>
        <Analytics />
      </body>
      {ANALYTICS_ENABLED && <GoogleAnalytics gaId={GA_MEASUREMENT_ID} />}
    </html>
  );
}
