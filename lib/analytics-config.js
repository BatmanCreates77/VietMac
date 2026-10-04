// Google Analytics 4 property for viet-mac.vercel.app. Measurement IDs are
// public (every visitor's browser loads them), so it lives in code rather
// than an env var.
export const GA_MEASUREMENT_ID = "G-CKQER8WHRL";

// Only real (production) builds report, so local development doesn't add
// visits to the site's analytics.
export const ANALYTICS_ENABLED = process.env.NODE_ENV === "production";
