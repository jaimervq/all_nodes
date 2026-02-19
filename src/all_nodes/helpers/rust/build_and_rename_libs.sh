#!/bin/bash
set -e

OUT=/usr/src/out
mkdir -p "$OUT"

for d in rust_*; do
    if [ -f "$d/Cargo.toml" ]; then
        echo "Building $d"

        CRATE_NAME=$(grep '^name' "$d/Cargo.toml" | head -n1 | cut -d '"' -f2)

        cargo build -q --manifest-path="$d/Cargo.toml" --release

        TARGET=$(find $d/target/release -name "*${CRATE_NAME}*.so" | head -n1)

        if [ -f "$TARGET" ]; then
            cp "$TARGET" "$OUT/${CRATE_NAME}.so"
            echo "    Built ${CRATE_NAME}.so"
        else
            echo "WARNING: missing ${CRATE_NAME}.so"
        fi
    fi
done

echo
echo "Built and renamed rust libs (Linux)"