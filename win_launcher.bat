:: ALL NODES LAUNCHER
:: 2022 Jaime Rivera


@echo off


set ALL_NODES_APP_NAME=ALL_NODES


:: ------------ Start!
echo [46m+++++++++++++++++++++++++++++++[0m
echo [46m+                             +[0m
echo [46m+          ALL_NODES          +[0m
echo [46m+                             +[0m
echo [46m+++++++++++++++++++++++++++++++[0m
echo Launched at %date% %time%
echo:

:: ------------ Root
set ALL_NODES_ROOT=%~dp0
echo [92m[%ALL_NODES_APP_NAME%][0m ALL_NODES_ROOT %ALL_NODES_ROOT%
echo:

:: ------------ Basic help
echo [92m[%ALL_NODES_APP_NAME%][0m Basic help:
type %ALL_NODES_ROOT%documentation\BASIC_HELP.txt
echo:

:: ------------ Env vars
echo [92m[%ALL_NODES_APP_NAME%][0m Setting environment variables:
set ALL_NODES_LIB_PATH=
set ALL_NODES_LIB_PATH=%ALL_NODES_ROOT%lib\;%ALL_NODES_LIB_PATH%
echo + ALL_NODES_LIB_PATH %ALL_NODES_LIB_PATH%

set PYTHONPATH=%ALL_NODES_ROOT%\..\;%PYTHONPATH%
echo:

:: ------ Start
echo [92m[%ALL_NODES_APP_NAME%][0m Starting all_nodes
echo:
%ALL_NODES_ROOT%.venv\Scripts\python.exe %ALL_NODES_ROOT%main.py %*

:: ------ Exit
echo:
echo [92m[%ALL_NODES_APP_NAME%][0m End of all_nodes
echo:

