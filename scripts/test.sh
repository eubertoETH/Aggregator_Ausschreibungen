#!/usr/bin/env sh
set -eu

python3 -m compileall -q Code
test -f requirements.txt
printf '%s\n' 'Application syntax checks passed.'
