"""
測試示例 - 演示如何使用 TestRecorder
"""
import asyncio
import sys
sys.path.append("..")

from core.recorder import TestRecorder
from core.db_manager import init_db
from generator.markdown_gen import generate_markdown_report
from generator.report_gen import generate_html_report
import config


async def test_example():
    """簡單測試示例 - 腳本模式"""
    # 初始化數據庫
    init_db()

    # 創建錄製器
    recorder = TestRecorder("示例測試")

    # 開始錄製（使用自訂尺寸）
    await recorder.start(
        "https://www.example.com",
        viewport_width=1280,
        viewport_height=720,
    )

    # 執行一些測試操作
    await recorder.click("text=More information")

    # 截圖並記錄
    await recorder.record_action("custom", "body", "自定義操作")

    # 停止錄製
    await recorder.stop()

    # 生成 Markdown 報告
    if recorder.session_id:
        md_path = generate_markdown_report(recorder.session_id)
        print(f"Markdown 報告: {md_path}")

    # 生成 HTML 驗收測試計畫
    if recorder.session_id:
        html_path = generate_html_report(recorder.session_id)
        print(f"HTML 驗收測試計畫: {html_path}")


async def test_dimensions_example():
    """演示不同尺寸的錄製"""
    init_db()

    # 使用 Tablet 尺寸
    recorder = TestRecorder("Tablet 測試")
    await recorder.start(
        "https://www.example.com",
        viewport_width=768,
        viewport_height=1024,
    )
    await recorder.record_action("screenshot", purpose="Tablet 尺寸截圖")
    await recorder.stop()

    if recorder.session_id:
        report_path = generate_html_report(recorder.session_id)
        print(f"HTML 驗收測試計畫: {report_path}")


if __name__ == "__main__":
    print(f"可用尺寸預設: {list(config.VIEWPORT_PRESETS.keys())}")
    # 執行第一個測試
    asyncio.run(test_example())