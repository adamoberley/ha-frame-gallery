#!/usr/bin/env bash
# Entry point (no s6/bashio - init: false). Looks up the MQTT broker that the
# Supervisor provides for `services: mqtt:need` and hands it to the daemon via
# environment variables, mirroring the ledfx app's pattern.
set -euo pipefail

eval "$(python3 - <<'PY'
import json, os, urllib.request

host, port, user, pw = "", 1883, "", ""
token = os.environ.get("SUPERVISOR_TOKEN", "")
if token:
    try:
        req = urllib.request.Request(
            "http://supervisor/services/mqtt",
            headers={"Authorization": "Bearer " + token},
        )
        d = json.load(urllib.request.urlopen(req, timeout=10))
        d = d.get("data", d) if isinstance(d, dict) else {}
        host = d.get("host") or ""
        user = d.get("username") or ""
        pw = d.get("password") or ""
        try:
            port = int(d.get("port") or 1883)
        except (TypeError, ValueError):
            port = 1883
        if d.get("ssl"):
            port = 1883  # use the plaintext listener; the daemon doesn't do TLS
    except Exception as exc:
        print(f"echo '[hue_ent] MQTT service lookup failed: {exc}' >&2")

def q(value):
    return "'" + str(value).replace("'", "'\\''") + "'"

print(f"export MQTT_HOST={q(host or '127.0.0.1')}")
print(f"export MQTT_PORT={q(port)}")
print(f"export MQTT_USER={q(user)}")
print(f"export MQTT_PASS={q(pw)}")
PY
)"

echo "[hue_ent] starting bridge (broker: ${MQTT_HOST}:${MQTT_PORT})"
exec python3 -m app.main
