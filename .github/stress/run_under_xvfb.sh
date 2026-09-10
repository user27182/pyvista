#!/usr/bin/env bash
# Run a command under xvfb-run with the script's own default server arguments,
# plus connection auditing and, for XVFB_VARIANT=noreset, -noreset.
set -euo pipefail

script="$(command -v xvfb-run)"
args="$(sed -n 's/^XVFBARGS="\(.*\)"$/\1/p' "$script")"
[ -n "$args" ] || {
	echo "could not read XVFBARGS from $script" >&2
	exit 1
}
args="$args -audit 2"

case "${XVFB_VARIANT:-default}" in
default) ;;
noreset) args="$args -noreset" ;;
*)
	echo "unknown XVFB_VARIANT=$XVFB_VARIANT" >&2
	exit 1
	;;
esac

errfile="${XVFB_ERROR_FILE:-/dev/null}"
echo "xvfb-run -a -e $errfile -s '$args' $*"
exec xvfb-run -a -e "$errfile" -s "$args" "$@"
