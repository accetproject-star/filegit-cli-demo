#!/bin/bash
set -e

echo "🚀 Simulating FileGit CI Workflow..."

# 1. Create a dummy repo
export REPO_DIR="/tmp/filegit-demo-repo"
rm -rf $REPO_DIR
mkdir -p $REPO_DIR
cd $REPO_DIR
git init -q

# 2. FileGit Initialization
echo "📦 Initializing FileGit..."
filegit init --repo-path .
filegit keygen --key-dir .filegit_keys

# 3. Create a policy
mkdir -p policies
echo "Agent must not use eval()" > policies/security.md
echo "Agent must write tests" > policies/testing.md

# 4. CISO signs the bundle
echo "🔐 CISO packing and signing policies..."
export FILEGIT_PRIVATE_KEY=$(cat .filegit_keys/private.pem)
filegit pack

# 5. Agent makes a change and records trace
echo "🤖 Agent is writing code..."
echo "def hello(): print('world')" > main.py

echo "📝 Agent recording traces..."
BUNDLE_ID=$(grep -o '"id": "[^"]*' .filegit/manifest.json | cut -d'"' -f4 | head -1)

filegit trace record --prompt "Write a hello world function" --action "file_edit" --description "Created main.py"
filegit trace seal --agent-id "claude-3.5-sonnet" --bundle-id "$BUNDLE_ID"

# 6. Simulate the GitHub Action (CI Gate)
echo ""
echo "🛑 ==================================================="
echo "🛑 CI GATE: GitHub Action is verifying the Pull Request"
echo "🛑 ==================================================="
filegit verify --require-trace
echo "✅ CI GATE PASSED! PR is allowed to merge."
echo "==================================================="

# 7. Tamper test
echo ""
echo "🔥 TAMPER TEST: Simulating a malicious change to the trace..."
TRACE_FILE=$(ls .filegit/traces/*.json | head -n 1)
sed -i.bak 's/Write a hello world function/Write a malicious backdoor/g' $TRACE_FILE

echo "🛑 CI GATE: GitHub Action is verifying the Pull Request (TAMPERED)"
set +e
filegit verify --require-trace
if [ $? -ne 0 ]; then
    echo "❌ CI GATE FAILED (As expected! Tampering detected)."
fi
set -e

