# Test Docs Platform

自動化驗收與測試文檔平台 - 使用 Playwright (Python) 自動記錄測試操作並生成專業測試報告。

## 功能特色

- 自動記錄所有測試操作（點擊、輸入、導航等）
- 每次操作自動截圖保存
- SQLite 存储測試會話和操作記錄
- 生成 Markdown 格式測試報告（帶截圖）
- 可選 AI 增強功能（自動標註操作目的）

## 安裝

```bash
pip install -r requirements.txt
playwright install chromium
```

## 使用方式

### 初始化數據庫

```bash
python main.py --init-db
```

### 列出所有測試會話

```bash
python main.py --list
```

### 開始錄製測試

```bash
python main.py --record "https://example.com" --session-name "我的測試"
```

### 生成測試報告

```bash
python main.py --report 1  # 生成 session 1 的報告
```

## 目錄結構

```
test-docs-platform/
├── core/                   # 核心模塊
│   ├── db_manager.py       # SQLite 數據庫管理
│   └── recorder.py         # 測試錄製器
├── generator/              # 報告生成
│   └── markdown_gen.py     # Markdown 生成器
├── ai_enhanced/            # AI 增強（可選）
├── tests/                  # 測試腳本
├── reports/                # 生成的報告
├── storage/                # 數據庫/截圖存储
├── config.py               # 配置文件
├── main.py                 # 入口
└── requirements.txt        # Python 依賴
```

## License

MIT
