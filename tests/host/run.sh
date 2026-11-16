#!/bin/sh
# Timmy Time Adventure for GFOS: host tests.
#   tests/host/run.sh [GFOPENALLEGRO/allegro4]
# The data files (amiga/tools/timmydat.py) read back through gfopenallegro's
# allegro4 core on its fake acgame.library, and the big-endian maps.
# Copyright (c) 2026 AmiCradle Team. GPL-3 or later, as Timmy Time Adventure.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
A4=${1:-"$ROOT/../gfopenallegro/allegro4"}
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT HUP INT TERM
python3 "$ROOT/tests/host/test_maps.py"
python3 "$ROOT/amiga/tools/timmydat.py" --all "$ROOT/res" "$ROOT/src/data" "$T/data" >/dev/null
${HOSTCC:-cc} -std=gnu99 -D_DEFAULT_SOURCE -w -I"$A4/include" -I"$A4/src" -I"$A4/tests" -I"$ROOT/src" \
    "$A4"/src/a4_*.c "$A4"/tests/fake_acgame.c "$ROOT/tests/host/test_data.c" -lm -o "$T/test_data"
"$T/test_data" "$T/data" "$ROOT/src/data"
