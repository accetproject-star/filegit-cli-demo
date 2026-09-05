<div align="center">
  
# 🛡️ FileGit

**Enterprise Governance & Cryptographic Attestation for Autonomous AI Agents**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-93%25-success.svg)](#)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

</div>

FileGit is a modern CLI tool and governance engine designed to bring **cryptographic accountability** to codebases edited by Autonomous AI Agents (like Claude, GPT-4, or custom Copilots). 

As AI agents gain autonomy, organizations need a way to ensure that agents strictly follow security guidelines, architectural rules, and compliance policies. FileGit bridges this gap by introducing cryptographically signed **Context Bundles**, an **Agent Flight Recorder**, and a **CI/CD Gatekeeper**.

---

## 🌟 Why FileGit?

- **For Security Teams (CISOs):** Write security policies in plain Markdown and cryptographically sign them via a beautiful local UI (FileGit Studio). 
- **For AI Agents:** Read the verified policies via MCP (Model Context Protocol), and leave a tamper-proof "Execution Trace" explaining exactly why decisions were made.
- **For DevOps Engineers:** Block any Pull Request in CI/CD where the AI agent ignored the rules or failed to provide a valid, signed execution trace.

---

## 🚀 Quickstart (Beginner Friendly)

### 1. Installation
Install the FileGit CLI via pip. We recommend using a virtual environment.
```bash
pip install filegit-cli
```

### 2. Initialize a Repository
Navigate to your project folder and initialize FileGit. This creates a hidden `.filegit` directory to store your signed manifests and traces.
```bash
cd my-project
filegit init
```

### 3. Generate Cryptographic Keys
Generate the Ed25519 keypair used to sign your policies. Keep your private key secure!
```bash
filegit keygen --key-dir .filegit_keys
```
*(Tip: In production, store `private.pem` in a secrets manager like GitHub Secrets or AWS Secrets Manager).*

### 4. Write Your Policies
Create a `policies/` folder in your project and write your rules in standard Markdown. These are the rules the AI Agent must follow.
```bash
mkdir policies
echo "# Security Rules\n1. Do not use eval().\n2. Always sanitize SQL inputs." > policies/security.md
```

### 5. CISO Dashboard: Sign the Bundle!
Launch the built-in **FileGit Studio** to visually review and cryptographically sign your policies.
```bash
export FILEGIT_PRIVATE_KEY=$(cat .filegit_keys/private.pem)
filegit studio
```
Navigate to `http://127.0.0.1:3000` in your browser. Review the policies on the left and click **Sign & Authorize Context** to pack the `.filegit/manifest.json`.

---

## 🤖 The "Flight Recorder" (For AI Agents)

Once policies are signed, AI Agents working on the repository must record their actions to prove compliance. FileGit provides a CLI for agents to interact with the **Flight Recorder**.

```bash
# 1. The agent records an action it just took
filegit trace record --prompt "Refactor the database layer" --action "file_edit" --description "Updated db.py to use parameterized queries"

# 2. The agent seals the trace when finished
filegit trace seal --agent-id "claude-3.5-sonnet" --bundle-id "filegit-bundle-2026..."
```
This generates a cryptographically signed JSON trace in `.filegit/traces/` that proves exactly what the agent did.

---

## 🛑 CI/CD Gatekeeper

In your GitHub Actions (or GitLab CI), you can run FileGit to strictly verify that:
1. The rules (Context Bundle) haven't been tampered with.
2. The AI Agent provided a valid, cryptographically signed trace matching the active rules.

```bash
# Exits non-zero if the signature is invalid or the trace is missing.
filegit verify --require-trace
```

### Example GitHub Action (`.github/workflows/filegit-gate.yml`)
```yaml
name: FileGit Gatekeeper
on: [pull_request]

jobs:
  verify-ai-code:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: accetproject-star/filegit-cli-demo@main
        # require-trace defaults to true: a PR whose agent did not attach a
        # signed execution trace fails this step.
        with:
          require-trace: 'true'
```

### Three steps to adopt it — and only two can be packaged

**A required status check is not deployed. It is granted.** This is the single most
important thing to understand before adopting FileGit, and no amount of tooling can
change it.

| | Step | Can it be packaged? |
|---|---|---|
| 1 | Add the workflow above to your repository (12 lines) | **Yes** — copy and paste |
| 2 | Let it run once, so GitHub learns the check's name | **Yes** — automatic |
| 3 | **Grant branch protection naming that check** | **No. Ever.** |

Step 3 must be done by someone with admin rights, on their own repository, by hand.
Either through *Settings → Branches → Add branch protection rule*, or in one command:

```bash
gh api -X PUT repos/OWNER/REPO/branches/main/protection --input - <<'JSON'
{"required_status_checks":{"strict":false,"contexts":["build-and-test (3.12)"]},
 "enforce_admins":true,"required_pull_request_reviews":null,"restrictions":null}
JSON
```

**Order matters.** GitHub will not let you require a check it has never seen run. Step 2 is
not a formality: it is a precondition of step 3, and skipping it is the usual mistake.

`enforce_admins: true` includes *you*. Without it, the person who owns the repository can
merge past a red check, which is the failure mode the tool exists to prevent.

#### Proof, not a claim

Both of these are real pull requests in this repository:

- **[#1](https://github.com/accetproject-star/filegit-cli-demo/pull/1)** — three checks
  green, merged normally.
- **[#2](https://github.com/accetproject-star/filegit-cli-demo/pull/2)** — one deliberate
  lint error. `gh pr view 2 --json mergeStateStatus` returns **`BLOCKED`**, and an actual
  merge attempt is refused:

  ```
  X Pull request #2 is not mergeable: the base branch policy prohibits the merge.
  ```

  This repository also sets `enforce_admins: true`, which GitHub documents as applying the
  same rules to administrators. That part is configured but not demonstrated here — proving
  it would require merging a knowingly broken commit into `main`.

And the pair that shows what the permission actually buys — the **same change, byte for
byte**, submitted twice:

| | [#5](https://github.com/accetproject-star/filegit-cli-demo/pull/5) | [#6](https://github.com/accetproject-star/filegit-cli-demo/pull/6) |
|---|---|---|
| The change | a policy edited without re-signing | *identical* |
| FileGit Gatekeeper | ❌ FAILURE | ❌ FAILURE |
| `build-and-test` ×3 | ✅ SUCCESS | ✅ SUCCESS |
| Merge state | `UNSTABLE` — **mergeable** | **`BLOCKED`** |

In #5 the Gatekeeper was running but was not a required check. **The only check that caught
the violation was the only one that could not stop it**; the three that could stop it had
nothing to object to, because the code was fine — what changed was a signed markdown file.

Between #5 and #6, not one line of code or workflow changed. A check was named as required.
**Having the check is not having the gate.**

#### The limit, stated plainly

Whoever grants the permission can revoke it. `enforce_admins: true` prevents merging on
red; it does not prevent turning the protection off entirely. Branch protection is
self-attested one level up — the audited party still holds the switch. Closing that gap
needs a third party holding it instead, which is what transparency logs such as
[Rekor](https://github.com/sigstore/rekor) exist for. FileGit does not do this today.

---

## 🏗️ Architecture (Robust Design)

FileGit is built with a Clean Architecture approach in Python, ensuring modularity, scalability, and high test coverage.

- **`src/filegit/cli/`**: Typer-based CLI, MCP Server (`mcp_server.py`), and FastAPI Studio (`studio_server.py`).
- **`src/filegit/core/`**: The brain of FileGit. Contains `use_cases.py` (business logic) and `flight_recorder.py` (traceability engine).
- **`src/filegit/domain/`**: Pydantic models (`models.py`) and interface ports (`ports.py`).
- **`src/filegit/infrastructure/`**: Adapters for cryptography (`PyNaClCrypto`), hashing (`SHA256Hasher`), and file system (`OSFileSystem`).
- **`dashboard/`**: A Vite + React frontend serving as the local CISO dashboard.

### Cryptography Details
- **Algorithm**: `Ed25519` via PyNaCl.
- **Hashing**: `SHA-256` for deterministic JSON hashing.
- **Keys**: Base58/Base64 encoding for public/private key portability.

---

## 🤝 Contributing

We welcome contributions! 
1. Clone the repository.
2. Install dependencies: `pip install -e ".[dev]"`
3. Run tests: `pytest` (We enforce >90% coverage).
4. Run linters: `ruff check .` and `mypy .`

## 📄 License
MIT License. See `LICENSE` for details.
