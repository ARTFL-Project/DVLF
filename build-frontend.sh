#!/bin/sh
# Build the Vue frontend, and cope with vue-cli-service not exiting.
#
# Measured 2026-09-05: the compile takes about ten seconds, prints "Build complete", and
# then the node process sits in epoll_wait indefinitely on a handle nothing closes — it
# was still alive 22 minutes later. This is not a BuildKit artefact; a plain `docker run`
# of the same command behaves identically. So: run it in the background, wait for the
# completion marker, then stop it — and verify the artefacts afterwards, so that a build
# which genuinely failed can never be mistaken for one that merely refused to exit.
set -e

LOG=/tmp/vue-build.log
MAX_WAIT=900

npx vue-cli-service build > "$LOG" 2>&1 &
pid=$!

waited=0
while [ "$waited" -lt "$MAX_WAIT" ]; do
  grep -q "Build complete" "$LOG" 2>/dev/null && break
  kill -0 "$pid" 2>/dev/null || break        # it exited on its own; the checks below judge
  sleep 2
  waited=$((waited + 2))
done

kill "$pid" 2>/dev/null || true
wait "$pid" 2>/dev/null || true
pkill -f vue-cli-service 2>/dev/null || true

cat "$LOG"

# The gate. Any of these failing fails the image build.
grep -q "Build complete" "$LOG"
test -s dist/index.html
test -d dist/js && test -d dist/css && test -d dist/img
ls dist/js/app.*.js dist/js/chunk-vendors.*.js >/dev/null

echo "frontend build verified after ${waited}s"
