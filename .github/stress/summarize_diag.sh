#!/usr/bin/env bash
# Print the per-worker diagnostic logs and Xvfb's audit log for one stress run.
set -uo pipefail

dir="$1"
for f in "$dir"/*.log; do
	[ -e "$f" ] || continue
	name="$(basename "$f")"
	echo "::group::$name ($(wc -l <"$f") lines, $(grep -c ANOMALY "$f") anomalies, $(grep -c 'VTK OUTPUT' "$f") VTK outputs)"
	grep -E 'session|ANOMALY|VTK OUTPUT|^[0-9:.]+ pid=[0-9]+     ' "$f" | head -n 200
	echo "::endgroup::"
done

err="$dir/xvfb.err"
if [ -e "$err" ]; then
	echo "::group::xvfb.err ($(wc -l <"$err") lines): connected=$(grep -c ' connected' "$err") disconnected=$(grep -c ' disconnected' "$err") rejected=$(grep -c ' rejected' "$err")"
	grep -v -E ' connected| disconnected' "$err" | head -n 60
	echo "::endgroup::"
fi
