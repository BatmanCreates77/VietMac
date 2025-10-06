import "./globals.css";

import { Analytics } from "@vercel/analytics/next";

export const metadata = {
  title: "VietMac Compare - Best MacBook Prices in Vietnam",
  description:
    "Compare live MacBook Pro prices from Vietnam's top retailers with VAT refunds for Indian tourists",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
