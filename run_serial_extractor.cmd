@echo off
setlocal
set "APP_DIR=%~dp0"
set "BUNDLED_PY=%SERIAL_EXTRACTOR_PYTHON%"

if not defined BUNDLED_PY (
  for /f "delims=" %%P in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do set "BUNDLED_PY=%%P"
)

if not defined BUNDLED_PY (
  for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "BUNDLED_PY=%%P"
)

if exist "%BUNDLED_PY%" (
  "%BUNDLED_PY%" "%APP_DIR%serial_number_extractor.py"
  goto :end
)

echo Python runtime not found.
echo Set SERIAL_EXTRACTOR_PYTHON to a Python 3.12 executable or install Python plus the requirements.
pause

:end
endlocal
