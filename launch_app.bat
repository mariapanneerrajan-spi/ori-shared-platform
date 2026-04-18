@echo off
REM
REM Launch App (dev mode)
REM
REM Sets up PYTHONPATH for source imports and RV_SUPPORT_PATH
REM for locally-installed rvpkgs, then starts OpenRV.
REM
REM Requires RV_HOME to be set to your OpenRV installation directory.
REM

setlocal

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

if "%RV_HOME%"=="" (
    echo ERROR: RV_HOME is not set.
    echo Set it to your OpenRV installation directory:
    echo   set RV_HOME=C:\path\to\OpenRV
    exit /b 1
)

if not exist "%SCRIPT_DIR%\local_install\lib\open_rv\Packages" (
    echo ERROR: local_install not found. Run 'python dev_setup.py build' first.
    exit /b 1
)

REM Python modules importable directly from source
set "PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%"

REM RV packages installed by dev_setup.py
set "RV_SUPPORT_PATH=%SCRIPT_DIR%\local_install\lib\open_rv"

REM Plugin config
set "RPA_APP_CORE_PLUGINS_CONFIG=%SCRIPT_DIR%\rpa\plugins\open_app_plugins.cfg"

REM Qt settings
set "QT_LOGGING_RULES=*=false;qt.core.critical=true;qt.core.fatal=true"
set "QTWEBENGINE_DISABLE_SANDBOX=1"

python -m rpa.app.launch_app %*
