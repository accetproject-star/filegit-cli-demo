# Policy: No claim in this repository may overstate what the code does

Documentation in this repository must describe behaviour that can be reproduced by
running the code. This applies to `README.md`, `action.yml` descriptions, and any file
under `docs/`.

## The specific claim this policy exists to prevent

> "If the signature is invalid or the trace is missing, the CI fails and blocks the PR."

That sentence lived in `README.md` and was **false**. A failing check does not block a
merge. A required status check is *granted* in the repository's branch protection
settings; until an administrator grants it, the job goes red and the merge button stays
available.

## The rule

A statement about enforcement must name the mechanism that enforces it. "The CI fails"
is verifiable. "The PR is blocked" is only true when branch protection names that check
as required — and saying so requires having checked.

Where a capability is configured but not demonstrated, the documentation says so.
