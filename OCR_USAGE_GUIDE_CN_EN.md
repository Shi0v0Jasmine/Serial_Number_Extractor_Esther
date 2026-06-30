# Serial Number Extractor v2.0.1 OCR 使用指南 / OCR Usage Guide

## 中文

### 需要下载的文件

请将以下两个文件下载到同一个文件夹：

1. `SerialNumberExtractor_v2.0.1_Windows.zip` - 主程序
2. `SerialNumberExtractor_OCRSupport_v2.0.1_Windows.zip` - OCR 离线支持包

无需安装 Docker、Python 或 PaddleOCR。OCR 在本机运行，PDF 和图片不会上传到云端。

### GUI 安装和使用

1. 解压 `SerialNumberExtractor_v2.0.1_Windows.zip`。
2. **不要解压** `SerialNumberExtractor_OCRSupport_v2.0.1_Windows.zip`。
3. 打开主程序解压目录，双击 `SerialNumberExtractor.exe`。
4. 点击 **Install OCR Support**。
5. 程序会显示三个选择：
   - **Yes**：从 GitHub 在线下载 OCR 支持包。
   - **No**：选择已经下载的离线 OCR ZIP。
   - **Cancel**：取消安装。
6. 使用下载好的 OCR 包时，请点击 **No**，然后选择
   `SerialNumberExtractor_OCRSupport_v2.0.1_Windows.zip`。
7. 等待出现 `OCR support 2.0.1 installed`。OCR 安装一次后即可持续使用。
8. 添加 PDF 文件或文件夹，并选择输出目录。
9. 选择 OCR 模式：
   - **auto（推荐）**：普通文本页使用原生解析，只对没有可用文字层的扫描页运行 OCR。
   - **off**：完全关闭 OCR。
   - **force**：所有页面都使用 OCR 结果，速度较慢，适合文字层错误或需要强制验证 OCR 的文件。
10. 点击 **Extract to Excel**。

OCR 会安装到：

```text
%LOCALAPPDATA%\Apeiro\SerialNumberExtractor\ocr
```

安装完成后，OCR ZIP 不必继续放在主程序旁边，但建议保留用于离线重装。

### CLI 安装和使用（可选）

将 OCR ZIP 放在主程序解压目录，在该目录打开 PowerShell：

```powershell
.\SerialNumberExtractorCLI.exe --ocr-package ".\SerialNumberExtractor_OCRSupport_v2.0.1_Windows.zip"
```

安装成功后运行：

```powershell
.\SerialNumberExtractorCLI.exe --no-gui --ocr auto "C:\Path\To\Input PDFs" -o "C:\Path\To\serial_numbers.xlsx"
```

强制对所有页面使用 OCR：

```powershell
.\SerialNumberExtractorCLI.exe --no-gui --ocr force "C:\Path\To\Input PDFs" -o "C:\Path\To\serial_numbers.xlsx"
```

### 结果检查

- `SAP_Copy`：主要输出。
- `Details`：来源页、解析方式、backend、OCR 置信度等诊断信息。
- `Review`：低置信度或有歧义的 OCR 候选，不会自动混入主结果。
- `Summary`：数量校验、native/OCR 数量、OCR 状态和 warning。
- 出现 `MISMATCH` 或 `UNVERIFIED` 时仍会导出文件，请人工检查。

### 常见问题

- **Windows 阻止运行 EXE**：确认文件来自本项目的 GitHub Release，然后在
  Windows SmartScreen 中选择“更多信息”并确认运行。
- **点击 Install OCR Support 后该选什么？** 使用本地 OCR ZIP 时选择 **No**；
  选择 **Yes** 会在线下载 OCR 包。
- **OCR 安装失败**：确认选择的是完整、未手动解压或修改的 OCR ZIP。
- **auto 没有对某页运行 OCR**：该页可能已有可用文字层。文字层错误时改用
  **force**。
- **OCR 结果不确定**：检查输出 Excel 的 `Review`、`Details` 和 `Summary`。

---

## English

### Files to download

Download both files into the same folder:

1. `SerialNumberExtractor_v2.0.1_Windows.zip` - main application
2. `SerialNumberExtractor_OCRSupport_v2.0.1_Windows.zip` - offline OCR support

Docker, Python, and a separate PaddleOCR installation are not required. OCR runs
locally; PDFs and images are not uploaded to a cloud service.

### GUI installation and use

1. Extract `SerialNumberExtractor_v2.0.1_Windows.zip`.
2. **Do not extract** `SerialNumberExtractor_OCRSupport_v2.0.1_Windows.zip`.
3. Open the extracted application folder and run `SerialNumberExtractor.exe`.
4. Click **Install OCR Support**.
5. The application displays three choices:
   - **Yes**: download the OCR support package from GitHub.
   - **No**: select an already downloaded offline OCR ZIP.
   - **Cancel**: do not install OCR.
6. To use the downloaded package, click **No**, then select
   `SerialNumberExtractor_OCRSupport_v2.0.1_Windows.zip`.
7. Wait for `OCR support 2.0.1 installed`. OCR only needs to be installed once.
8. Add PDF files or a folder and select an output folder.
9. Select an OCR mode:
   - **auto (recommended)**: use native parsing for text pages and OCR only for
     scanned pages without usable text.
   - **off**: disable OCR.
   - **force**: use OCR results for every page. This is slower and is intended
     for PDFs with an incorrect text layer or explicit OCR verification.
10. Click **Extract to Excel**.

OCR support is installed at:

```text
%LOCALAPPDATA%\Apeiro\SerialNumberExtractor\ocr
```

After installation, the OCR ZIP does not need to remain next to the application,
but keeping it is useful for offline reinstallation.

### CLI installation and use (optional)

Place the OCR ZIP in the extracted application folder and open PowerShell there:

```powershell
.\SerialNumberExtractorCLI.exe --ocr-package ".\SerialNumberExtractor_OCRSupport_v2.0.1_Windows.zip"
```

After installation:

```powershell
.\SerialNumberExtractorCLI.exe --no-gui --ocr auto "C:\Path\To\Input PDFs" -o "C:\Path\To\serial_numbers.xlsx"
```

To use OCR results for every page:

```powershell
.\SerialNumberExtractorCLI.exe --no-gui --ocr force "C:\Path\To\Input PDFs" -o "C:\Path\To\serial_numbers.xlsx"
```

### Checking the results

- `SAP_Copy`: main output.
- `Details`: source page, extraction method, backend, OCR confidence, and diagnostics.
- `Review`: low-confidence or ambiguous OCR candidates; these are not inserted
  automatically into the main output.
- `Summary`: quantity checks, native/OCR counts, OCR status, and warnings.
- The export still completes for `MISMATCH` or `UNVERIFIED`; review those rows manually.

### Troubleshooting

- **Windows blocks the EXE**: verify that it came from this project's GitHub
  Release, then use Windows SmartScreen's **More info** option to confirm it.
- **Which option should I select after clicking Install OCR Support?** Select
  **No** when using the local OCR ZIP. **Yes** downloads the package.
- **OCR installation fails**: select the complete, unmodified OCR ZIP; do not
  extract it first.
- **auto does not OCR a page**: the page may contain a usable text layer. Retry
  with **force** if that text layer is incorrect.
- **OCR output is uncertain**: inspect the `Review`, `Details`, and `Summary`
  worksheets.
