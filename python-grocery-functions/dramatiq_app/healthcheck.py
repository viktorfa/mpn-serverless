#!/usr/bin/env python3
import os
import sys
import time

import redis


def log(msg):  # lines here will show in Docker health logs
    print(msg, flush=True)


STAGE = os.getenv("STAGE", "")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# 1) Ready file check - just verify it exists (service has started)
ready_file = "/tmp/dramatiq.ready"
try:
    st = os.stat(ready_file)
    age = time.time() - st.st_mtime
    log(f"ready_file={ready_file} age_seconds={age:.1f}")
    # Don't check staleness - service should run indefinitely
except FileNotFoundError:
    log("ready file missing - service not started yet")
    sys.exit(1)

# 2) Redis ping (fast timeouts)
try:
    r = redis.Redis(
        host=REDIS_HOST, port=6379, password=REDIS_PASSWORD, socket_connect_timeout=1, socket_timeout=1, decode_responses=True
    )
    pong = r.ping()
    log(f"redis_ping={pong}")
except Exception as e:
    log(f"redis_ping_error={e}")
    sys.exit(1)

log("health=ok")
sys.exit(0)
