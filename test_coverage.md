# 測試覆蓋度：FileTree

測量日期：2026-10-28。數字來自這台 Windows 機器上的一次實測，不是估計，也不是只數檔案。

| 項目 | 內容 |
|---|---|
| 直譯器 | 3.14.4 |
| 直譯器說明 | 系統 Python 3.14（此專案的 .venv 沒有 pytest，或沒有 .venv） |
| 工具 | coverage 7.15.0，`coverage run --branch` |
| 測量範圍 | `je_file_tree` |
| 測試路徑 | `test` |
| 命令 | `python -m coverage run --branch --source=je_file_tree -m pytest test` |
| 敘述覆蓋 | 90.65%（22908 / 25270） |
| 分支覆蓋 | 78.15%（5414 / 6928） |
| 測試結果 | 2782 passed, 53 skipped in 577.49s (0:09:37) |
| 耗時 | 586.0 秒 |

敘述覆蓋是執行到的敘述數除以全部敘述數。分支覆蓋是執行到的分支數除以全部分支數。兩者分開算，沒有把分支混進敘述百分比。

## 這次怎麼量

專案 `.venv` 是空的，沒有 pytest。這次用系統 Python 3.14，並把專案根目錄放進 `PYTHONPATH`。

## 覆蓋較低的檔案

只列這次測量裡敘述覆蓋最低的檔案，最多 12 個。

| 檔案 | 敘述覆蓋 | 已覆蓋 / 敘述 |
|---|---:|---:|
| `je_file_tree/gui/startup_posix.py` | 25.19% | 34 / 135 |
| `je_file_tree/core/bin_empty.py` | 25.59% | 65 / 254 |
| `je_file_tree/core/linux_watch.py` | 31.13% | 33 / 106 |
| `je_file_tree/core/finder_bin.py` | 35.79% | 68 / 190 |
| `je_file_tree/core/trash_restore.py` | 45.21% | 66 / 146 |
| `je_file_tree/core/priority.py` | 57.35% | 39 / 68 |
| `je_file_tree/gui/file_actions.py` | 66.67% | 46 / 69 |
| `je_file_tree/__main__.py` | 66.67% | 2 / 3 |
| `je_file_tree/core/mft_reader.py` | 66.93% | 168 / 251 |
| `je_file_tree/core/mounts.py` | 68.16% | 122 / 179 |
| `je_file_tree/core/recycle_shell.py` | 69.34% | 95 / 137 |
| `je_file_tree/core/copy_io.py` | 70.76% | 121 / 171 |
