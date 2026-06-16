# Serial Number Extractor Version History

本文件用于记录 Serial Number Extractor 的版本号、变更原因和验证记录。发布 GitHub release 前，应先更新本文件。

This file tracks version numbers, change reasons, and verification notes for Serial Number Extractor. Update it before creating a GitHub release.

## Version Number Definition / 版本号定义

Format / 格式:

```text
MAJOR.MINOR.PATCH
```

### MAJOR / 主版本号

中文：当加入新的主工作流或明显改变工具能力边界时增加。

English: Increase when a new main workflow is added or the tool capability boundary changes materially.

### MINOR / 次版本号

中文：当主工作流不变，但支持范围明显扩大时增加，例如新增大类 vendor adapter、OCR 工作流或新的输出模式。

English: Increase when the main workflow stays the same but support expands materially, such as a new major vendor adapter, OCR workflow, or output mode.

### PATCH / 修订号

中文：当修复 bug、修正 vendor-specific 解析规则、改善校验逻辑、调整文档或修复包装问题时增加。

English: Increase for bug fixes, vendor-specific parsing corrections, validation improvements, documentation updates, or packaging fixes.

## Current Version / 当前版本

Current version: `1.0.2`.

当前版本：`1.0.2`。

Latest released version: `1.0.2`.

最新已发布版本：`1.0.2`。

## Change Log / 更新记录

### `1.0.2` - 2026-06-16 Adtran Parent Part Mapping Fix / Adtran 主产品映射修复

中文：

- 修复 Adtran 特殊格式：`This Position Line Contains` 下的行只用于读取数量，例如 `13 1063707680-11 F7/9TCE-PCN-10GU+10G` 只取 `Qty = 13`。
- `Part Number` / `Part Name` 改为使用上方主产品块，例如 `BC00000647 / F7/9TCE-PCN-10GU+10G&1P-L`，不再把 position line 中的 `1063707680-11` 当成最终 Part Number。
- 新增 `BC########` 型 Adtran part number 识别，避免主产品块被误判为 serial-like token。
- 保留并完善 S/N 与 USI Code 优先级：有明确 serial marker 时优先使用 S/N/Serial；只有 USI Code 时才把 USI Code 作为 serial number。
- 清理 `SN:FA...` 在 PDF 文本抽取中变成 `FA...SN` 的尾缀问题。
- 本版本已重新打包，并将作为 GitHub release `v1.0.2` 发布。

English:

- Fixed an Adtran special format where rows under `This Position Line Contains` provide quantity only. For example, `13 1063707680-11 F7/9TCE-PCN-10GU+10G` contributes only `Qty = 13`.
- `Part Number` / `Part Name` now come from the parent product block, such as `BC00000647 / F7/9TCE-PCN-10GU+10G&1P-L`, instead of the position-line material `1063707680-11`.
- Added recognition for `BC########` Adtran part numbers so parent product blocks are not rejected as serial-like tokens.
- Preserved and tightened S/N vs USI Code priority: explicit serial markers win; USI Code is exported only when no marked serial exists.
- Cleaned the PDF extraction artifact where `SN:FA...` can appear as `FA...SN`.
- This version has been rebuilt and will be published as GitHub release `v1.0.2`.

Verification:

- `01_Input_PDFs` Adtran regression: `242` serials, `OK=242`, `MISMATCH=0`, `UNVERIFIED=0`.
- `BC00000647 / F7/9TCE-PCN-10GU+10G&1P-L`: one `13/13 OK` group and one `9/9 OK` group.
- No rows remain with `Part Number = 1063707680-11`.
- Original 7 vendor samples: `1073` serials, `MISMATCH=0`; existing `UNVERIFIED=15` best-effort rows unchanged.

### `1.0.1` - 2026-06-16 USI Code Duplicate Source Fix / USI Code 重复来源修复

中文：

- 修复 Adtran PDF 中 `USI Code:` 区域被误识别为 serial number 的问题，避免同一设备同时由 S/N 和 USI 产生重复或 mismatch。
- 重新生成并发布 `v1.0.1` 包。

English:

- Fixed Adtran PDFs where the `USI Code:` section could be misread as serial numbers, preventing duplicate records or mismatch when both S/N and USI are present.
- Rebuilt and released package `v1.0.1`.

### `1.0.0` - 2026-06-16 Initial Release / 初始发布

中文：

- 发布初版 Serial Number Extractor，支持 GUI / CLI，从 vendor PDF 中提取 `Part Number`、`Part Name`、`Serial Number` 并输出 Excel / CSV。
- 输出包含 `SAP_Copy`、`Details`、`Summary`，支持 `Order Qty`、`Serial Count`、`Qty Check` 校验。
- 使用 Esther 提供的 7 个 vendor sample 验证，总 serial 数为 `1073`。

English:

- Released the initial Serial Number Extractor with GUI / CLI support for extracting `Part Number`, `Part Name`, and `Serial Number` from vendor PDFs into Excel / CSV.
- Output includes `SAP_Copy`, `Details`, and `Summary`, with `Order Qty`, `Serial Count`, and `Qty Check` validation.
- Verified against Esther's 7 vendor samples with total serial count `1073`.
