@echo off
:: If building these libs from Windows, just run this .bat

:: CD to this folder
cd /d "%~dp0"
cls

:: Compile for Windows (very important to set PYO3_PYTHON to correct version!)
echo [---WINDOWS---]
echo Building...
for /f %%i in ('py -3.10 -c "import sys; print(sys.executable)"') do set PYO3_PYTHON=%%i

del /q .\rust_noise.pyd 2>nul
del /q .\rust_noise.so 2>nul
cargo fmt -q --manifest-path=./rust_noise/Cargo.toml
cargo build -q --manifest-path=./rust_noise/Cargo.toml  --release
move .\rust_noise\target\release\rust_noise.dll .\rust_noise.pyd >nul

del /q .\rust_regex.pyd 2>nul
del /q .\rust_regex.so 2>nul
cargo fmt -q --manifest-path=./rust_regex/Cargo.toml
cargo build -q --manifest-path=./rust_regex/Cargo.toml  --release
move .\rust_regex\target\release\rust_regex.dll .\rust_regex.pyd >nul

del /q .\rust_requests.pyd 2>nul
del /q .\rust_requests.so 2>nul
cargo fmt -q --manifest-path=./rust_requests/Cargo.toml
cargo build -q --manifest-path=./rust_requests/Cargo.toml  --release
move .\rust_requests\target\release\rust_requests.dll .\rust_requests.pyd >nul

echo Built and renamed rust libs (Windows)
echo:

:: Docker for compiling in Linux
echo [---CONTAINER FOR LINUX---]
docker build -t python-rust-lib .
docker run --rm -v .:/usr/src/out python-rust-lib