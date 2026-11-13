#!/usr/bin/env bash
# owh-testbed.sh: throwaway Open WebUI v0.13.3 for OWH rehearsals (ADR-0007, ADR-0011).
#
#   owh-testbed.sh up       create container + volume, wait for health, create the admin
#   owh-testbed.sh status   print container state, URL, health and admin e-mail
#   owh-testbed.sh down     remove container AND volume and the local state dir
#   owh-testbed.sh reset    down, then up
#   owh-testbed.sh token    print a fresh admin session token (for scripts; do not log it)
#
# Never touches the live `open-webui` container or its volume. Host networking is used
# because Ollama listens on 127.0.0.1 only (a bridge container cannot reach it); the server
# is bound to 127.0.0.1:18080 so nothing listens on other interfaces.
set -euo pipefail

IMAGE="ghcr.io/open-webui/open-webui:v0.13.3"
NAME="owh-test-owu"
VOLUME="owh-test-owu-data"
PORT="${OWH_TESTBED_PORT:-18080}"
URL="http://127.0.0.1:${PORT}"
ADMIN_EMAIL="owh-test@localhost"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/owh/testbed"
PASS_FILE="$STATE_DIR/admin-password"
# Extra `docker run` arguments (e.g. OPENAI_API_BASE_URLS for the env-vs-DB test).
read -r -a EXTRA_ARGS <<<"${OWH_TESTBED_EXTRA_ARGS:-}"

die() {
	echo "owh-testbed: $*" >&2
	exit 1
}

guard_names() {
	# Belt and braces: refuse to run if someone edits the names to the live ones.
	[[ "$NAME" != "open-webui" && "$VOLUME" != "open-webui" ]] || die "refusing to touch the live instance"
}

exists_container() { docker container inspect "$NAME" >/dev/null 2>&1; }
exists_volume() { docker volume inspect "$VOLUME" >/dev/null 2>&1; }

# A cold first start downloads about 1.1 GB of embedding model before /health answers.
wait_healthy() {
	local _
	for _ in $(seq 1 300); do
		if curl -fsS -m 2 "$URL/health" >/dev/null 2>&1; then
			return 0
		fi
		sleep 1
	done
	die "no /health from $URL after 300 s (docker logs $NAME)"
}

# POST JSON read from stdin, so passwords never appear in argv.
post_json() {
	curl -fsS -m 20 -H 'Content-Type: application/json' --data-binary @- "$URL$1"
}

admin_token() {
	[[ -r "$PASS_FILE" ]] || die "no admin password file ($PASS_FILE); run 'up' first"
	python3 -c '
import json, sys
print(json.dumps({"email": sys.argv[1], "password": open(sys.argv[2]).read().strip()}))
' "$ADMIN_EMAIL" "$PASS_FILE" | post_json /api/v1/auths/signin |
		python3 -c 'import json, sys; print(json.load(sys.stdin)["token"])'
}

cmd_up() {
	guard_names
	docker image inspect "$IMAGE" >/dev/null 2>&1 || die "image $IMAGE not on disk (this script never pulls)"
	if exists_container; then
		if [[ "$(docker inspect -f '{{.State.Running}}' "$NAME")" != "true" ]]; then
			docker start "$NAME" >/dev/null
		fi
		wait_healthy
		ensure_admin
		echo "owh-testbed: already up at $URL"
		return 0
	fi
	mkdir -p "$STATE_DIR"
	chmod 700 "$STATE_DIR"
	local secret
	secret="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
	# The secret goes in through an env file so it is not in this script's argv.
	local envfile
	envfile="$(mktemp "$STATE_DIR/env.XXXXXX")"
	chmod 600 "$envfile"
	printf 'WEBUI_SECRET_KEY=%s\n' "$secret" >"$envfile"
	docker run -d --name "$NAME" \
		--network host \
		-v "$VOLUME:/app/backend/data" \
		--env-file "$envfile" \
		-e HOST=127.0.0.1 \
		-e PORT="$PORT" \
		-e OLLAMA_BASE_URL=http://127.0.0.1:11434 \
		-e SCARF_NO_ANALYTICS=true \
		-e DO_NOT_TRACK=true \
		-e ANONYMIZED_TELEMETRY=false \
		-e ENABLE_VERSION_UPDATE_CHECK=false \
		"${EXTRA_ARGS[@]}" \
		"$IMAGE" >/dev/null
	rm -f "$envfile"
	wait_healthy
	ensure_admin
	echo "owh-testbed: up at $URL (admin $ADMIN_EMAIL, password in $PASS_FILE)"
}

# Also run on an existing container, so an earlier `up` that timed out still gets its admin.
ensure_admin() {
	mkdir -p "$STATE_DIR"
	chmod 700 "$STATE_DIR"
	if [[ ! -s "$PASS_FILE" ]]; then
		(
			umask 077
			python3 -c 'import secrets; print(secrets.token_urlsafe(24))' >"$PASS_FILE"
		)
	fi
	# First signup on an empty DB becomes the admin. On a reused volume it already exists.
	if ! python3 -c '
import json, sys
print(json.dumps({"name": "OWH Test", "email": sys.argv[1], "password": open(sys.argv[2]).read().strip()}))
' "$ADMIN_EMAIL" "$PASS_FILE" | post_json /api/v1/auths/signup >/dev/null 2>&1; then
		admin_token >/dev/null || die "admin signup and signin both failed"
	fi
}

cmd_down() {
	guard_names
	if exists_container; then
		docker rm -f "$NAME" >/dev/null
	fi
	if exists_volume; then
		docker volume rm "$VOLUME" >/dev/null
	fi
	rm -rf "$STATE_DIR"
	echo "owh-testbed: down (container, volume and $STATE_DIR removed)"
}

cmd_status() {
	if exists_container; then
		echo "container: $NAME $(docker inspect -f '{{.State.Status}} (started {{.State.StartedAt}})' "$NAME")"
	else
		echo "container: $NAME absent"
	fi
	if exists_volume; then echo "volume:    $VOLUME present"; else echo "volume:    $VOLUME absent"; fi
	if curl -fsS -m 2 "$URL/health" >/dev/null 2>&1; then echo "health:    ok ($URL)"; else echo "health:    unreachable ($URL)"; fi
	echo "admin:     $ADMIN_EMAIL"
}

case "${1:-}" in
up) cmd_up ;;
down) cmd_down ;;
reset)
	cmd_down
	cmd_up
	;;
status) cmd_status ;;
token) admin_token ;;
*)
	echo "usage: $0 up|down|status|reset|token" >&2
	exit 2
	;;
esac
