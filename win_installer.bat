:: ALL NODES INSTALLER
:: 2022 Jaime Rivera


@echo off


set ALL_NODES_INSTALLER_NAME=ALL_NODES_INSTALLER


:: ------------ Start!
echo [46m+++++++++++++++++++++++++++++++++++++++++++++++++[0m
echo [46m+                                               +[0m
echo [46m+          LAUNCHING ALL_NODES INSTALL          +[0m
echo [46m+                                               +[0m
echo [46m+++++++++++++++++++++++++++++++++++++++++++++++++[0m
echo Launched at %date% %time%
echo:

:: ------------ Root
set ALL_NODES_ROOT=%~dp0
echo [92m[%ALL_NODES_INSTALLER_NAME%][0m ALL_NODES_ROOT %ALL_NODES_ROOT%
echo:

:: ------------ Venv
echo [92m[%ALL_NODES_INSTALLER_NAME%][0m Creating venv...
py -3.10 -m venv %ALL_NODES_ROOT%.venv

:: ------ Deps
echo [92m[%ALL_NODES_INSTALLER_NAME%][0m Installing dependencies...
%ALL_NODES_ROOT%.venv\Scripts\pip install --upgrade pip
%ALL_NODES_ROOT%.venv\Scripts\pip install -r "%ALL_NODES_ROOT%requirements.txt"

pause