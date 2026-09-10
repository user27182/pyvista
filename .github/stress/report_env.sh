#!/usr/bin/env bash
# Describe the pieces the Xvfb reset race depends on.
set -uo pipefail

script="$(command -v xvfb-run)"
echo "::group::xvfb-run defaults ($script)"
grep -n -E '^(XVFBARGS|SERVERNUM|LISTENTCP|ERRORFILE)=' "$script"
echo "SIGUSR1 readiness handshake lines: $(grep -c USR1 "$script")"
echo "::endgroup::"

echo "::group::Xvfb"
Xvfb -version 2>&1 | head -n 5
echo "::endgroup::"

echo "::group::GL and X libraries"
ldconfig -p | grep -E 'libEGL|libGLX|libGL\.so|libOSMesa|libGLdispatch|libX11\.so|libxcb\.so'
dpkg-query -W -f='${Package} ${Version}\n' 'libegl*' 'libglvnd*' 'libgl1*' 'libglx*' 'libosmesa*' 'mesa*' 'xvfb' 'libx11-6' 'libxcb1' 2>/dev/null
echo "::endgroup::"

echo "::group::Limits and machine"
echo "ulimit -n: $(ulimit -n)"
echo "nproc: $(nproc)"
free -m
echo "::endgroup::"
