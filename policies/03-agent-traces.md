# Policy: Work produced by an autonomous agent carries a signed trace

This repository is built with the assistance of AI agents. The Flight Recorder exists so
that the reasoning behind a change is recoverable, not just its diff.

## The rule

An agent that modifies this repository records its actions with `filegit trace record`
and seals them with `filegit trace seal --bundle-id <id>` before the pull request is
opened. The sealed trace is committed under `.filegit/traces/`.

`filegit verify --require-trace` fails when no valid trace matches the active bundle, or
when a sealed trace has been altered after signing.

## What this policy does not claim

Nothing here distinguishes a human commit from an agent commit. The trace is an
attestation the agent chooses to make; its absence proves nothing on its own. What the
signature does prove is that a trace which *is* present has not been edited since it was
sealed.
