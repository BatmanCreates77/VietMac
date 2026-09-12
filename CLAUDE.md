# Model-switch suggestions

When work in this session shifts complexity tier, proactively suggest switching models — don't just silently keep going on the wrong one:

- Suggest **Opus 5** when about to do high-stakes, easy-to-get-subtly-wrong logic: anti-bot/scraper evasion, validation-gate edge cases, concurrency, security-sensitive code, or anything where a wrong assumption ships silently.
- Suggest **Haiku 4.5** when the remaining work is mechanical/repetitive and low-risk: bulk file deletions, boilerplate generation, straightforward renames, running/reading test output — to save cost without quality loss.
- Suggest **staying on Sonnet 5** as the default for normal multi-file feature work, refactors, and debugging — don't suggest switching just because a task is "big."
- When suggesting a switch, say so in one line at the point of transition (not preemptively for the whole task), name the specific reason, and let the user decide — don't switch yourself, you can't.
