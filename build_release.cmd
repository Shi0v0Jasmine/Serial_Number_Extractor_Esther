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

if not exist "%BUNDLED_PY%" (
  echo Python runtime not found. Set SERIAL_EXTRACTOR_PYTHON to a Python 3.12 executable.
  exit /b 1
)

cd /d "%APP_DIR%"

set "APP_BUILD_PYTHONPATH=%APP_DIR%.build_deps;%APP_DIR%.test_deps;%APP_DIR%"
set "OCR_BUILD_PYTHONPATH=%APP_DIR%.build_deps;%APP_DIR%.ocr_deps;%APP_DIR%.test_deps;%APP_DIR%"
set "COMMON_ARGS=--onefile --clean --hidden-import pypdf --hidden-import pdfplumber --hidden-import openpyxl --hidden-import openpyxl.styles --hidden-import openpyxl.utils"

set "PYTHONPATH=%APP_BUILD_PYTHONPATH%"
"%BUNDLED_PY%" -m PyInstaller ^
  %COMMON_ARGS% ^
  --windowed ^
  --name SerialNumberExtractor ^
  serial_number_extractor.py
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

"%BUNDLED_PY%" -m PyInstaller ^
  %COMMON_ARGS% ^
  --console ^
  --name SerialNumberExtractorCLI ^
  serial_number_extractor.py
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

set "PYTHONPATH=%OCR_BUILD_PYTHONPATH%"
"%BUNDLED_PY%" -m PyInstaller ^
  --onefile --clean ^
  --paths "%APP_DIR%.ocr_deps" ^
  --collect-all paddle ^
  --collect-all paddleocr ^
  --collect-all paddlex ^
  --copy-metadata paddlepaddle ^
  --copy-metadata paddleocr ^
  --copy-metadata paddlex ^
  --copy-metadata imagesize ^
  --copy-metadata opencv-contrib-python ^
  --copy-metadata pyclipper ^
  --copy-metadata pypdfium2 ^
  --copy-metadata python-bidi ^
  --copy-metadata shapely ^
  --hidden-import paddle ^
  --hidden-import paddleocr ^
  --hidden-import pypdf ^
  --console ^
  --name ocr_worker ^
  serial_extractor\ocr_worker.py
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

"%BUNDLED_PY%" scripts\package_release.py
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

echo Release package created under "%APP_DIR%release\v2.0.1"
endlocal
