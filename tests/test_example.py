"""
測試示例 - 演示如何使用 TestRecorder
"""
import asyncio
import sys
sys.path.append("..")

from core.recorder import TestRecorder
from core.db_manager import init_db
from generator.markdown_gen import generate_markdown_report


async def test_example():
    """簡單測試示例"""
    # 初始化數據庫
    init_db()

    # 創建錄製器
    recorder = TestRecorder("示例測試")

    # 開始錄製
    await recorder.start("https://www.example.com")

    # 執行一些測試操作
    await recorder.click("text=More information")

    # 截圖並記錄
    await recorder.record_action("custom", "body", "自定義操作")

    # 停止錄製
    await recorder.stop()

    # 生成報告
    if recorder.session_id:
        report_path = generate_markdown_report(recorder.session_id)
        print(f"報告已生成：{report_path}")


if __name__ == "__main__":
    asyncio.run(test_example())
