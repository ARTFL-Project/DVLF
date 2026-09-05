#!/bin/sh
# Start the database, run gunicorn in the foreground, and stop the database cleanly on
# SIGTERM so that a restart is not a crash recovery every time.
set -e

# The socket lives on the tmpfs and listen_addresses is empty, so the database speaks only
# inside this container — unreachable from outside by construction.
#
# These go in postgresql.conf rather than on pg_ctl's -o line, and that is not a style
# choice: pg_ctl reads the socket directory from the config file to decide where to poll
# while -w waits. Passed via -o, the server puts its socket in /tmp and pg_ctl waits for
# one in /var/run/postgresql, forever. Writing them to the config makes the two agree.
# Idempotent, and self-healing for a data directory initialised somewhere that forgot.
if ! grep -q '^# managed by the dvlf entrypoint' "$PGDATA/postgresql.conf"; then
  {
    echo "# managed by the dvlf entrypoint"
    echo "unix_socket_directories = '/tmp'"
    echo "listen_addresses = ''"
  } >> "$PGDATA/postgresql.conf"
fi

pg_ctl -D "$PGDATA" -w start

shutdown() {
  kill -TERM "$child" 2>/dev/null || true
  wait "$child" 2>/dev/null || true
  pg_ctl -D "$PGDATA" -m fast -w stop || true
  exit 0
}
trap shutdown TERM INT

gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 -w 4 \
  --worker-tmp-dir /tmp \
  --access-logfile - --error-logfile - web_app:app &
child=$!

# Nothing else supervises Postgres in a one-container service. If it goes away, exit and
# let `restart: unless-stopped` rebuild the container rather than serve errors behind a
# healthy-looking port. Set PG_WATCHDOG=0 to observe the unsupervised behaviour instead.
while kill -0 "$child" 2>/dev/null; do
  sleep 15
  [ "${PG_WATCHDOG:-1}" = "1" ] || continue
  pg_isready -q && continue
  sleep 5
  pg_isready -q && continue
  echo "entrypoint: postgres is not answering; shutting down so the container restarts" >&2
  shutdown
done
wait "$child"
