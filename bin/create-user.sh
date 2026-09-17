#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -lt 1 ]; then
  echo "Usage: sudo $0 USERNAME [SSH_PUBLIC_KEY_FILE]"
  exit 2
fi
USER_NAME=$1
KEY_FILE=${2:-}

if ! klist -s; then
  echo "Acquire an IPA admin ticket first: kinit admin"
  exit 1
fi

ipa user-show "$USER_NAME" >/dev/null 2>&1 || ipa user-add "$USER_NAME" --first="$USER_NAME" --last="Operator" --password
ipa group-add-member cluster-operators --users="$USER_NAME"

if [ -n "$KEY_FILE" ]; then
  ipa user-mod "$USER_NAME" --sshpubkey="$(cat "$KEY_FILE")"
fi

echo "Created/updated $USER_NAME. Test: id $USER_NAME"
echo "For Kerberos SSO: kinit $USER_NAME && ssh -K node1.lab.example"
