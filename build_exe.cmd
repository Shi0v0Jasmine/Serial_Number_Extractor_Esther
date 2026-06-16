@echo off
setlocal
set "APP_DIR=%~dp0"
set "BUNDLED_PY=C:\Users\21136\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if not exist "%BUNDLED_PY%" (
  echo Bundled Python runtime not found:
  echo %BUNDLED_PY%
  pause
  exit /b 1
)

cd /d "%APP_DIR%"

if exist "%APP_DIR%.build_deps" (
  set "PYTHONPATH=%APP_DIR%.build_deps;%PYTHONPATH%"
)

set "COMMON_ARGS=--onefile --clean --hidden-import pypdf --hidden-import openpyxl --hidden-import openpyxl.styles --hidden-import openpyxl.utils"

"%BUNDLED_PY%" -m PyInstaller ^
  %COMMON_ARGS% ^
  --windowed ^
  --name SerialNumberExtractor ^
  serial_number_extractor.py
if %ERRORLEVEL% neq 0 (
  echo.
  echo GUI build failed. PyInstaller may not be installed in this Python runtime.
  echo Install it with: "%BUNDLED_PY%" -m pip install --target "%APP_DIR%.build_deps" pyinstaller
  pause
  exit /b 1
)

"%BUNDLED_PY%" -m PyInstaller ^
  %COMMON_ARGS% ^
  --console ^
  --name SerialNumberExtractorCLI ^
  serial_number_extractor.py
if %ERRORLEVEL% neq 0 (
  echo.
  echo CLI build failed. PyInstaller may not be installed in this Python runtime.
  echo Install it with: "%BUNDLED_PY%" -m pip install --target "%APP_DIR%.build_deps" pyinstaller
  pause
  exit /b 1
)

echo.
echo EXE files created at:
echo "%APP_DIR%dist\SerialNumberExtractor.exe"
echo "%APP_DIR%dist\SerialNumberExtractorCLI.exe"
pause
endlocal
