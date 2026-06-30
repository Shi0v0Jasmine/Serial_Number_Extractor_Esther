# OCR Sidecar Contract

OCR support is optional and installed under:

```text
%LOCALAPPDATA%\Apeiro\SerialNumberExtractor\ocr
```

The package is a ZIP with this minimum structure:

```text
ocr_support.json
ocr_worker.exe
models/
```

Example manifest:

```json
{
  "version": "2.0.0",
  "worker": "ocr_worker.exe",
  "paddlepaddle": "3.2.2",
  "paddleocr": "3.7.0",
  "require_model_dirs": true,
  "models": [
    "PP-OCRv6_small_det",
    "PP-OCRv6_small_rec"
  ]
}
```

The worker interface is:

```text
ocr_worker.exe --input <pdf> --pages 1,3,4
```

It writes UTF-8 JSON to stdout:

```json
{
  "spans": [
    {
      "text": "FA70000000001",
      "page": 1,
      "bbox": [100, 200, 300, 230],
      "confidence": 0.98
    }
  ]
}
```

Installation verifies the package SHA256 supplied by the download manifest, rejects path traversal, extracts to a temporary directory, validates the worker, and atomically swaps versions. Failed upgrades retain the previous valid installation.

`serial_extractor/ocr_worker.py` is the source worker. Building and publishing the self-contained runtime/models package is a release action and is intentionally not performed in the pending `2.0.0` source change.
