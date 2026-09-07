# syntax=docker/dockerfile:1
#
# dvlf: the application and the database it owns, in one image, run by an unprivileged
# uid on a read-only root filesystem. See docker_containers_update/dvlf/MIGRATION.md.

# ---- frontend build; this stage never ships ----
# Vue CLI 3 / webpack 4 will not build under Node 17+ without --openssl-legacy-provider,
# so the builder is pinned to Node 16. An EOL Node here is bounded: it runs at build time,
# on our own source, and nothing from this stage reaches the runtime image except dist/.
FROM node:16-bullseye AS web
WORKDIR /src
COPY public/package.json public/package-lock.json ./
# --legacy-peer-deps because the lockfile predates npm 7's automatic peer installation:
# without it npm tries to add peers the lock never recorded (jquery for bootstrap 4,
# @babel/core@7.0.0-beta.47 for babel-preset-stage-2) and refuses the install. With it,
# the tree installed is exactly the one the lockfile records — which is the tree that
# built the bundle now in production.
RUN npm ci --no-audit --no-fund --legacy-peer-deps
COPY public/ ./

# The API origin is compiled into the bundle by main.js, so it cannot be changed at
# runtime. The default reproduces the production bundle; the staging build overrides it,
# otherwise a browser pointed at staging silently exercises production (MIGRATION.md 5.7).
ARG API_SERVER=https://dvlf.uchicago.edu

# The reCAPTCHA *site* key is public and is likewise compiled in. Staging needs its own
# key pair, because a reCAPTCHA key is tied to its allowed domains and its secret cannot
# be duplicated: rotating production's secret to share it would break production until
# cutover. A separate staging key decouples the two entirely.
ARG RECAPTCHA_KEY=6LfhfycTAAAAAId87HWFIW-N8cShdp6O8fpAMK8h

# vue-cli-service does not exit when it has finished; build-frontend.sh handles that and
# verifies the artefacts. See the comments in that script.
COPY build-frontend.sh /usr/local/bin/build-frontend.sh
RUN sed -i "s|\"apiServer\": \".*\"|\"apiServer\": \"${API_SERVER}\"|" appConfig.json \
 && sed -i "s|\"recaptchaKey\": \".*\"|\"recaptchaKey\": \"${RECAPTCHA_KEY}\"|" appConfig.json \
 && cat appConfig.json \
 && sh /usr/local/bin/build-frontend.sh

# ---- runtime: app + database, one image ----
FROM ubuntu:26.04
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8

# Busted weekly by the build arg so that `docker compose build --pull` actually applies
# security updates instead of reusing a cached layer (CONTAINER_UPDATE_PLAN.md 5.1).
ARG REBUILD_DATE=unset
RUN echo "rebuild: $REBUILD_DATE" \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      postgresql postgresql-contrib ca-certificates \
 && rm -rf /var/lib/apt/lists/* /var/lib/postgresql/*/main \
 # Canonical's base image ships /usr/bin/pebble, their service manager for OCI images.
 # Nothing here uses it - the entrypoint starts postgres and gunicorn directly - and it
 # is a 10 MB Go binary that carried 8 HIGH CVEs on the first weekly scan, 2026-09-07.
 && rm -f /usr/bin/pebble \
 # The ssl-cert package (a postgresql dependency) drops a self-signed "snakeoil" key here.
 # This cluster never speaks TLS - listen_addresses is empty - so the key is unused, and
 # leaving it makes every scan report a secret that is not one. A report people learn to
 # ignore is worse than no report.
 && rm -f /etc/ssl/private/ssl-cert-snakeoil.key /etc/ssl/certs/ssl-cert-snakeoil.pem

# initdb calls getpwuid(), so the runtime uid has to exist in /etc/passwd. Nothing in
# this image runs as root, so there is no gosu and no privilege drop at runtime.
#
# 480 is deliberate and matches a real `dvlf` system account on the host, so that the
# bind-mounted database directory and the container's processes read as `dvlf` on both
# sides. The same pattern as artfl-platform-services, which runs as 358 with a `philo-web`
# host account behind it. The obvious choice, 999, is systemd-coredump on the host, which
# makes `ls -l` and `ps` actively misleading.
RUN groupadd -g 480 dvlf && useradd -u 480 -g 480 -M -s /usr/sbin/nologin dvlf

# The interpreter comes from uv rather than the distro, so it is pinned here and bumped
# as a deliberate decision instead of moving with the base image.
ENV UV_PYTHON_INSTALL_DIR=/opt/python UV_LINK_MODE=copy
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY requirements.txt /tmp/requirements.txt
RUN uv venv /opt/venv --python 3.13 --managed-python \
 && VIRTUAL_ENV=/opt/venv uv pip install --no-cache -r /tmp/requirements.txt \
 && rm -rf /root/.cache

ENV PATH=/opt/venv/bin:/usr/lib/postgresql/18/bin:$PATH \
    PGDATA=/data/psql/18 \
    PGHOST=/tmp \
    PYTHONUNBUFFERED=1

# WORKDIR is /DVLF because the app opens config.json, words_of_the_day.json and
# public/dist/ by relative path.
WORKDIR /DVLF
COPY web_app.py datamodels.py words_of_the_day.json ./
COPY --from=web /src/dist ./public/dist
COPY entrypoint.sh /entrypoint.sh

USER 480:480
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
