"use client";

import posthog from "posthog-js";
import { PostHogProvider as PHProvider } from "posthog-js/react";
import { useEffect } from "react";

export function PostHogProvider({ children }) {
  useEffect(() => {
    // Initialize PostHog only on client side
    if (typeof window !== "undefined") {
      posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY, {
        api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
        // Verbose console logging only while developing locally.
        debug: process.env.NODE_ENV === "development",
        loaded: (client) => {
          // An earlier build called posthog.debug(), which persists in each
          // visitor's localStorage ("ph_debug") and outlives `debug: false`.
          if (process.env.NODE_ENV !== "development") client.debug(false);
        },
        capture_pageview: true, // Automatic pageview tracking
        capture_pageleave: true, // Track when users leave
      });
    }
  }, []);

  return <PHProvider client={posthog}>{children}</PHProvider>;
}
