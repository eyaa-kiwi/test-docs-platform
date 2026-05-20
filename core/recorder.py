"""
Recorder Module - 錄製所有用戶操作
使用 Playwright 的事件監聽機制，攔截所有操作並自動記錄
"""
import asyncio
import os
from datetime import datetime
from typing import Optional, Callable
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from core import db_manager
import config


class TestRecorder:
    """測試錄製器"""

    def __init__(self, session_name: str = "測試會話"):
        self.session_name = session_name
        self.session_id: Optional[int] = None
        self.screenshot_count = 0
        os.makedirs(config.SCREENSHOTS_DIR, exist_ok=True)

    async def start(self, url: str, headless: bool = True):
        """開始錄製"""

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)

        self.context = await self.browser.new_context(
            record_video_dir=os.path.join(config.STORAGE_DIR, "videos"),
            record_video_size={"width": 1280, "height": 720}
        )

        self.page = await self.context.new_page()

        # 攔截所有操作事件
        self._setup_event_listeners()

        # 創建 session
        self.session_id = db_manager.create_session(self.session_name, url)

        # 導航到目標 URL
        await self.page.goto(url)

        return self.page

    def _setup_event_listeners(self):
        """設置事件攔截器"""
        # 注意：Playwright Python API 不支援 directly hooking all events
        # 我們會在外部想法中通過重写方法來實現
        pass

    async def record_action(self, action_type: str, selector: str = None, value: str = None):
        """記錄操作"""
        screenshot_path = await self._take_screenshot()
        db_manager.record_action(
            session_id=self.session_id,
            action_type=action_type,
            selector=selector,
            value=value,
            screenshot_path=screenshot_path
        )
        print(f"記錄操作：{action_type} - {selector}")

    async def _take_screenshot(self) -> str:
        """截取屏幕"""
        self.screenshot_count += 1
        filename = f"action_{self.session_id}_{self.screenshot_count}.png"
        filepath = os.path.join(config.SCREENSHOTS_DIR, filename)

        await self.page.screenshot(path=filepath)
        return filepath

    async def click(self, selector: str):
        """錄製點擊操作"""
        await self.page.click(selector)
        await self.record_action("click", selector)

    async def type(self, selector: str, value: str):
        """錄入輸入操作"""
        await self.page.fill(selector, value)
        await self.record_action("type", selector, value)

    async def navigate(self, url: str):
        """錄入導航操作"""
        await self.page.goto(url)
        await self.record_action("navigate", url)

    async def stop(self):
        """停止錄製"""
        db_manager.end_session(self.session_id)
        await self.browser.close()
        await self.playwright.stop()
        print(f"錄製結束 - Session ID: {self.session_id}")


# 用法示例
async def main():
    recorder = TestRecorder("示例測試")
    await recorder.start("https://www.example.com")

    # 執行測試操作
    await recorder.click("text=Click Me")
    await recorder.type("#username", "test@example.com")
    await recorder.navigate("https://www.example.com/next")

    await recorder.stop()


if __name__ == "__main__":
    asyncio.run(main())
