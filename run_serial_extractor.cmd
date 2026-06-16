@echo off
setlocal
set "APP_DIR=%~dp0"
set "BUNDLED_PY=C:\Users\21136\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if exist "%BUNDLED_PY%" (
  "%BUNDLED_PY%" "%APP_DIR%serial_number_extractor.py"
  goto :end
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py "%APP_DIR%serial_number_extractor.py"
  goto :end
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python "%APP_DIR%serial_number_extractor.py"
  goto :end
)

echo Python runtime not found.
echo Please run this on the Codex machine or install Python plus pypdf/openpyxl.
pause

:end
endlocal
