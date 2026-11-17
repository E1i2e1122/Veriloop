#!/usr/bin/env bash
# Start x11vnc for the live browser view.
# When VNC_PASSWORD is set the VNC server requires it; otherwise it accepts
# unauthenticated connections, which is only acceptable for local development.
set -euo pipefail

display="${DISPLAY:-:99}"
args=(-display "${display}" -forever -shared -rfbport 5900)

if [ -n "${VNC_PASSWORD:-}" ]; then
  passfile="${VNC_PASSWD_FILE:-/tmp/x11vnc.passwd}"
  x11vnc -storepasswd "${VNC_PASSWORD}" "${passfile}" >/dev/null 2>&1
  chmod 600 "${passfile}"
  args+=(-rfbauth "${passfile}")
else
  echo "WARNING: VNC_PASSWORD is not set; the live browser view accepts unauthenticated connections." >&2
  args+=(-nopw)
fi

exec /usr/bin/x11vnc "${args[@]}"
