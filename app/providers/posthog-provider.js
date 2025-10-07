"use client";

import posthog from "posthog-js";
import { PostHogProvider as PHProvider } from "posthog-js/react";
import { useEffect } from "react";

export function PostHogProvider({ children }) {
  useEffect(() => {
    // Initialize PostHog only on client side
    if (typeof window !== "undefined") {
      console.log("PostHog Init - Key:", process.env.NEXT_PUBLIC_POSTHOG_KEY);
      console.log("PostHog Init - Host:", process.env.NEXT_PUBLIC_POSTHOG_HOST);

      posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY, {
        api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
        debug: true, // Enable debug mode
        loaded: (posthog) => {
          console.log("PostHog loaded successfully!");
          posthog.debug();
        },
        capture_pageview: true, // Automatic pageview tracking
        capture_pageleave: true, // Track when users leave
      });
    }
  }, []);

  return <PHProvider client={posthog}>{children}</PHProvider>;
}
