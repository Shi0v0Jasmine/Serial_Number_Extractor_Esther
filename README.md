# Serial Number Extractor App

Fix note 2026-06-16: Adtran `This Position Line Contains` rows now provide quantity only; final Part Number / Part Name come from the parent product block. When a primary serial marker such as S/N exists alongside USI Code, the marked serial is preferred; when only USI Code exists, USI Code is exported as the serial number.

这个小工具用于 Esther / BizOps 场景：从 vendor PDF、packing list、invoice 中提取 Part Number、Part Name 和 Serial Number，并生成 Excel / CSV。工具本地运行，不上传 PDF 到外部 AI 或云服务。

## 推荐运行方式

双击：

```text
dist\SerialNumberExtractor.exe
```

第一次启动可能需要几秒钟。

操作步骤：

1. 点击 `Add PDFs` 或 `Add Folder`。
2. 选择 vendor PDF 文件或文件夹。
3. 选择 output folder。
4. 点击 `Extract to Excel`。
5. 打开生成的 Excel，查看 `SAP_Copy` sheet。

## 输出列

`SAP_Copy` sheet 和 CSV 会包含这些列：

| Column | Meaning |
| --- | --- |
| `Part Number` | 产品料号 |
| `Part Name` | 产品短名称 / 型号 |
| `Serial Number` | 对应序列号 |
| `Order Qty` | PDF 中识别到的订单数量 |
| `Serial Count` | 同一个 part block 下识别到的 serial 数量 |
| `Qty Check` | `OK` / `MISMATCH` / `UNVERIFIED` |

`Details` sheet 会额外保留 source file、page、method、confidence 和 block source，方便排错。

`Summary` sheet 会列出每个 PDF 的 serial 总数、每个 part 的数量校验结果，以及 warnings。

## 校验规则

- `OK`：`Order Qty` 等于 `Serial Count`。
- `MISMATCH`：两者不一致。工具会继续导出，但会在 Excel 中标红，并在 `Summary` / 日志中写 warning。
- `UNVERIFIED`：serial 已识别，但该 vendor 样式下没有可靠识别到 order quantity；例如部分 ECI 样例会使用 best-effort part mapping。

## 命令行 / 排障版本

如果需要批量测试或查看日志，用：

```text
dist\SerialNumberExtractorCLI.exe --no-gui "<PDF文件或文件夹>" -o "<输出xlsx路径>"
```

示例：

```text
dist\SerialNumberExtractorCLI.exe --no-gui "..\Vendor Document Sample" -o "outputs\sample_test.xlsx"
```

## 已用样例验证

使用 Esther 发来的 `Vendor Document Sample` 跑过完整验证：

| PDF | Count |
| --- | ---: |
| `1) PI 990183217.PDF` | 92 |
| `2) 1042924 PL (IL).pdf` | 15 |
| `2) Packing list  RD20260409A1.pdf` | 187 |
| `2) Packing List SDH201003533.pdf` | 16 |
| `2) Packing List SO20621.pdf` | 117 |
| `2) PL 251212147.pdf` | 46 |
| `BL F-APE001-24152.pdf` | 600 |
| **Total** | **1073** |

关键校验：

- Adtran `1042004437-01 / F150/ADV/XG120PRO/FAN-EXH` 输出 2 条 serial，`Qty Check = OK`。
- RUID range 展开后分别为 180 和 7，均为 `OK`。
- Smartoptics 已排除 `85043100` 这类 customs code。
- DTC 各 part block 的 qty 与 serial count 一致。
- PURE IT 两个 `Quantité 300` block 各输出 300 条。

## 当前支持的样例格式

- Adtran: `S/N:` 后接多行 serial numbers，并支持跨页 serial 延续。
- DTC: `Part Name -> Vendor -> Part Number -> Qty -> Serial numbers are:`。
- Smartoptics: product line 中的 part code / qty，以及 `*VB...*VB...`、`*VK...*VK...` serial。
- RUID: `Item code` + serial range，例如 `B2426041342001-180`。
- Ciena: `Line # Qty UOM Description of Goods/Part #` 表格。
- PURE IT: `Part (Quantité 300)` 后接连续 serial block。
- ECI-style packing list: `LOT/SERIAL NO.` 区域内的纯数字 serial，并做 best-effort part mapping。

## 边界

- 如果 PDF 是扫描图片，没有可抽取文字，当前版本可能读不到，需要 OCR 版本。
- 如果 vendor 格式很新，可能需要补规则。
- `Part Name` 取产品短名称 / 型号，不取后面的长描述文本。

## 重新打包

如果修改了源码，双击：

```text
build_exe.cmd
```

成功后会重新生成：

```text
dist\SerialNumberExtractor.exe
dist\SerialNumberExtractorCLI.exe
```
