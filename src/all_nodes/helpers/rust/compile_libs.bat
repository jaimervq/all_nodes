@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
cls

echo ======================================
echo        PYTHON RUST BUILD (WIN)
echo ======================================
echo.

:: Build mode (default release)
set BUILD_MODE=release
if /I "%1"=="debug" set BUILD_MODE=debug

echo Build mode: %BUILD_MODE%
echo.

:: Detect Python for PyO3
for /f %%i in ('py -3.10 -c "import sys; print(sys.executable)"') do set PYO3_PYTHON=%%i
echo Using Python: %PYO3_PYTHON%
echo.

:: Collect crates first
set CRATES=

for /d %%D in (rust_*) do (
    if exist "%%D\Cargo.toml" (
        set CRATES=!CRATES! %%D
    )
)

if "%CRATES%"=="" (
    echo No rust_* crates found
    goto docker
)

echo Found crates:
chcp 65001 >nul
for %%D in (%CRATES%) do (
    echo     🦀 %%D
)
echo.

:: Build crates in parallel
for %%D in (%CRATES%) do (
    call :buildcrate %%D
)

echo --------------------------------------
echo.
echo.

::goto docker

:: ------------------------------
:: Build crate function
:: ------------------------------
:buildcrate
set CRATE=%1
echo Building !CRATE!

:: Read crate name from Cargo.toml
for /f "tokens=1,2 delims==" %%A in ('findstr /r "^name *= *" "!CRATE!\Cargo.toml"') do (
    set RAW=%%B
)
set CRATE_NAME=!RAW:"=!
set CRATE_NAME=!CRATE_NAME: =!

:: Delete old artifacts
del /q "!CRATE_NAME!.pyd" 2>nul
del /q "!CRATE_NAME!.so" 2>nul

:: Format
cargo fmt -q --manifest-path="!CRATE!\Cargo.toml"

:: Build
if "%BUILD_MODE%"=="release" (
    cargo build -q --manifest-path="!CRATE!\Cargo.toml" --release
) else (
    cargo build -q --manifest-path="!CRATE!\Cargo.toml"
)

if errorlevel 1 (
    echo ERROR building !CRATE!
    exit /b
)

:: Rename DLL -> PYD
if "%BUILD_MODE%"=="release" (
    set TARGET=!CRATE!\target\release\!CRATE_NAME!.dll
) else (
    set TARGET=!CRATE!\target\debug\!CRATE_NAME!.dll
)

if exist "!TARGET!" (
    move "!TARGET!" "!CRATE_NAME!.pyd" >nul
    echo     Built !CRATE_NAME!.pyd
) else (
    echo WARNING: DLL not found for !CRATE_NAME!
)

exit /b

:: ------------------------------
:: Docker build
:: ------------------------------
:docker

echo =================================
echo        CONTAINER FOR LINUX
echo =================================
docker build -t python-rust-lib .
docker run --rm -v "%cd%":/usr/src/out python-rust-lib

echo.
echo Done.
pause