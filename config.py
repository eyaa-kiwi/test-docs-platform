"""
配置文件
"""
import os

# 數據庫存儲路徑
STORAGE_DIR = "storage"
DB_PATH = os.path.join(STORAGE_DIR, "test_sessions.db")

# 截圖存储路徑
SCREENSHOTS_DIR = os.path.join(STORAGE_DIR, "screenshots")

# 報告存儲路徑
REPORTS_DIR = "reports"

# 測試腳本存儲路徑
SCRIPTS_DIR = "scripts"

# AI 配置（可選）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_AI_ENHANCE = bool(OPENAI_API_KEY)

# Playwright 配置
BROWSER = "chromium"
HEADLESS = True          # 一般模式使用無頭
INTERACTIVE_HEADLESS = False  # 互動模式顯示瀏覽器
SCREENSHOT_DELAY = 100   # 截圖延遲（毫秒）

# 錄製區域尺寸 (Viewport)
VIEWPORT_WIDTH = 1280    # 預設寬度
VIEWPORT_HEIGHT = 720    # 預設高度

# 常用尺寸預設
VIEWPORT_PRESETS = {
    "HD":     {"width": 1280, "height": 720},
    "FHD":    {"width": 1920, "height": 1080},
    "Laptop": {"width": 1366, "height": 768},
    "Tablet": {"width": 768,  "height": 1024},
    "Mobile": {"width": 375,  "height": 812},
}

# 報告語言 (zh = 繁體中文, en = English)
LANGUAGE = os.getenv("TDP_LANGUAGE", "en")