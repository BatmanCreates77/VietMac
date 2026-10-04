"use client";

import { useMemo } from "react";
import { usePostHog } from "posthog-js/react";
import { sendGAEvent } from "@next/third-parties/google";
import { ANALYTICS_ENABLED } from "@/lib/analytics-config";

// One call records an event in both PostHog and Google Analytics, so the two
// never drift apart. Event names are PostHog's existing ones (snake_case,
// which GA4 also expects).
export function useAnalytics() {
  const posthog = usePostHog();
  return useMemo(
    () => ({
      capture(event, properties = {}) {
        posthog?.capture(event, properties);
        if (ANALYTICS_ENABLED) sendGAEvent("event", event, properties);
      },
    }),
    [posthog],
  );
}
