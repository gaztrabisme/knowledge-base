#!/bin/bash
# Goal row 4: the 20 phase A chunk and markdown files are byte-identical to the pre-run baseline.
set -e
here="$(dirname "$0")/../.."
cd "$here"
shasum -a 256 -c data/philosophy/phase-b/phase-a-baseline.sha256
