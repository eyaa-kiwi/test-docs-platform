# Test Docs Platform

自動化驗收與測試文檔平台 - 使用 Playwright 自動記錄測試操作並生成專業測試報告。

## 功能特色

- **互動模式** - 打開瀏覽器，人工操作時自動記錄所有事件
- **腳本模式** - 從 JSON 自動執行測試步驟
- 支援 5 種 Viewport 預設（HD/FHD/Laptop/Tablet/Mobile）
- 每次操作自動截圖 + JavaScript 增強元素識別
- SQLite 存儲測試會話和操作記錄
- 生成 Markdown / HTML 測試報告（帶截圖）

## 免安裝使用（推薦）

專案已自帶 `.venv/` 虛擬環境和 Chromium，無需額外安裝：

```bash
# macOS / Linux
./run.sh --help

# Windows
run.bat --help
```

### 快速開始

```bash
# 初始化數據庫
./run.sh --init-db

# 列出所有測試會話
./run.sh --list

# 互動錄製模式（打開瀏覽器，人工操作自動記錄）
./run.sh --interactive "https://example.com" --session-name "我的測試"

# 互動錄製 + 指定尺寸
./run.sh --interactive "https://example.com" --dimensions FHD

# 腳本自動執行模式
./run.sh --script scripts/login_test.json --session-name "登入測試"

# 生成 Markdown 報告
./run.sh --report 1

# 生成 HTML 驗收測試計畫報告
./run.sh --report-html 1
```

### 可用尺寸預設

| 預設 | 尺寸 |
|------|------|
| HD | 1280 x 720 |
| FHD | 1920 x 1080 |
| Laptop | 1366 x 768 |
| Tablet | 768 x 1024 |
| Mobile | 375 x 812 |

## 開發者安裝

```bash
# 建立虛擬環境
uv venv .venv
uv pip install -r requirements.txt
playwright install chromium
```

## 目錄結構

```
test-docs-platform/
├── .venv/                  # 虛擬環境（已包含所有依賴）
├── core/                   # 核心模塊
│   ├── db_manager.py       # SQLite 數據庫管理
│   └── recorder.py         # 測試錄製器
├── generator/              # 報告生成
│   ├── markdown_gen.py     # Markdown 生成器
│   └── report_gen.py       # HTML 報告生成器
├── scripts/                # JSON 測試腳本範例
├── tests/                  # 測試腳本
├── storage/                 # 數據庫/截圖/影片存储
├── config.py                # 配置文件
├── main.py                  # 入口
├── run.sh                   # macOS/Linux 啟動腳本
├── run.bat                  # Windows 啟動腳本
└── requirements.txt         # Python 依賴
```

## 依賴

- playwright >= 1.40.0
- sqlite-utils >= 3.24
- pyyaml >= 5.1

## License

MIT