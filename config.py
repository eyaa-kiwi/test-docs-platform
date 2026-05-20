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

# AI 配置（可選）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_AI_ENHANCE = bool(OPENAI_API_KEY)

# Playwright 配置
BROWSER = "chromium"
HEADLESS = True
SCREENSHOT_DELAY = 100  # 截圖延遲（毫秒）
