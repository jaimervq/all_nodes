#!/bin/bash

# Build libs
echo Building...

cargo build -q --manifest-path=./rust_noise/Cargo.toml  --release
cp "/usr/src/rust_noise/target/release/librust_noise.so" "/usr/src/out/rust_noise.so"

cargo build -q --manifest-path=./rust_regex/Cargo.toml  --release
cp "/usr/src/rust_regex/target/release/librust_regex.so" "/usr/src/out/rust_regex.so"

cargo build -q --manifest-path=./rust_requests/Cargo.toml  --release
cp "/usr/src/rust_requests/target/release/librust_requests.so" "/usr/src/out/rust_requests.so"

# END
printf "Built and renamed rust libs (Linux)\n"