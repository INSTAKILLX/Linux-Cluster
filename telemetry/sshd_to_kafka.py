#!/usr/bin/env python3
"""Publish real sshd success/failure events from systemd-journald to SentinelFlow Kafka."""
import json
import os
import re
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone


BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "security-events")
DEVICE = socket.getfqdn()

FAILED = re.compile(r"Failed (?:password|publickey|keyboard-interactive/pam) for (?:invalid user )?(?P<user>[^ ]+) from (?P<ip>[^ ]+)")
ACCEPTED = re.compile(r"Accepted (?P<method>[^ ]+) for (?P<user>[^ ]+) from (?P<ip>[^ ]+)")
INVALID = re.compile(r"Invalid user (?P<user>[^ ]+) from (?P<ip>[^ ]+)")


def producer_forever():
    from kafka import KafkaProducer
    while True:
        try:
            return KafkaProducer(
                bootstrap_servers=BOOTSTRAP,
                acks="all",
                value_serializer=lambda v: json.dumps(v, separators=(",", ":")).encode(),
                key_serializer=lambda v: v.encode(),
            )
        except Exception as exc:
            print(f"Kafka unavailable: {exc}; retrying", file=sys.stderr, flush=True)
            time.sleep(3)


def normalize(message):
    m = FAILED.search(message)
    if m:
        return "LOGIN_FAILED", m.group("user"), m.group("ip"), None
    m = ACCEPTED.search(message)
    if m:
        return "LOGIN_SUCCESS", m.group("user"), m.group("ip"), m.group("method")
    m = INVALID.search(message)
    if m:
        return "LOGIN_FAILED", m.group("user"), m.group("ip"), "invalid-user"
    return None


def event(event_type, user, ip, method, raw):
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user,
        "device_id": DEVICE,
        "event_type": event_type,
        "ip": ip,
        "country": None,
        "bytes": 0,
        "metadata": {
            "source": "sshd/journald",
            "auth_method": method or "unknown",
            "raw": raw[:1000],
        },
    }


def main():
    prod = producer_forever()
    proc = subprocess.Popen(
        ["journalctl", "-f", "-n", "0", "-o", "json", "-u", "sshd.service"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        try:
            record = json.loads(line)
            msg = record.get("MESSAGE", "")
            parsed = normalize(msg)
            if not parsed:
                continue
            typ, user, ip, method = parsed
            payload = event(typ, user, ip, method, msg)
            prod.send(TOPIC, key=user, value=payload).get(timeout=10)
            print(json.dumps(payload), flush=True)
        except Exception as exc:
            print(f"telemetry error: {exc}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
