#!/usr/bin/env python3
"""
自動化驗收與測試文檔平台
Main Entry Point

使用方式：
  # 初始化數據庫
  python main.py --init-db

  # 列出所有測試會話
  python main.py --list

  # 互動模式：打開瀏覽器，人工操作自動記錄
  python main.py --interactive "https://example.com" --session-name "我的測試"

  # 互動模式 + 指定錄製尺寸
  python main.py --interactive "https://example.com" --dimensions FHD

  # 自訂錄製尺寸
  python main.py --interactive "https://example.com" --width 1920 --height 1080

  # 腳本模式：從 JSON 腳本自動執行測試
  python main.py --script scripts/login_test.json --session-name "登入測試"

  # 生成 Markdown 測試報告
  python main.py --report 1

  # 生成 HTML 驗收測試計畫報告
  python main.py --report-html 1
"""
import asyncio
import argparse
import sys
import signal

from core.db_manager import init_db, get_all_sessions
from core.recorder import TestRecorder
from generator.markdown_gen import generate_markdown_report
from generator.report_gen import generate_html_report
import config
from i18n import set_lang, get_lang, t


def list_sessions():
    """列出所有測試會話"""
    sessions = get_all_sessions()
    if not sessions:
        print(t("no_sessions"))
        return []
    print(f"\n{t('sessions_list')}:")
    print(f"  {t('session_id'):<4} {t('test_name'):<20} {t('test_url'):<40} {t('status'):<10}")
    print(f"  {'-'*4} {'-'*20} {'-'*40} {'-'*10}")
    for s in sessions:
        print(f"  {s[0]:<4} {s[1]:<20} {s[2]:<40} {s[5]:<10}")
    return sessions


def parse_dimensions(width_str, height_str, preset_str):
    """Parse dimensions from CLI arguments."""
    if preset_str and preset_str in config.VIEWPORT_PRESETS:
        preset = config.VIEWPORT_PRESETS[preset_str]
        return preset["width"], preset["height"], preset_str

    if width_str and height_str:
        try:
            w = int(width_str)
            h = int(height_str)
            return w, h, f"{w}x{h}"
        except ValueError:
            pass

    return config.VIEWPORT_WIDTH, config.VIEWPORT_HEIGHT, f"{config.VIEWPORT_WIDTH}x{config.VIEWPORT_HEIGHT}"


async def run_interactive_recorder(
    url: str,
    session_name: str = "Test Session",
    viewport_width: int = None,
    viewport_height: int = None,
    lang: str = None,
):
    """
    互動模式：打開瀏覽器，人工操作時自動記錄
    支援停止按鈕和 Esc 鍵結束錄製
    """
    vp_w = viewport_width or config.VIEWPORT_WIDTH
    vp_h = viewport_height or config.VIEWPORT_HEIGHT

    print("\n" + "=" * 60)
    print(f"  {t('interactive_mode')}")
    print(f"  {t('test_name')}: {session_name}")
    print(f"  {t('test_url')}: {url}")
    print(f"  {t('recording_size')}: {vp_w} x {vp_h}")
    print("=" * 60 + "\n")

    recorder = TestRecorder(session_name)
    await recorder.start(
        url,
        headless=False,
        interactive=True,
        viewport_width=vp_w,
        viewport_height=vp_h,
    )

    # 等待停止信號（來自 polling 中的 stop button 或 Esc）
    stop_event = asyncio.Event()

    def signal_handler(sig, frame):
        print("\n\n⏹️  收到 Ctrl+C，正在停止錄製...")
        stop_event.set()

    # 註冊信號處理
    if sys.platform != "win32":
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, lambda: stop_event.set())
    else:
        signal.signal(signal.SIGINT, signal_handler)

    # 同時監聽 polling 中的 stop_requested 和信號
    async def wait_for_stop():
        while not stop_event.is_set() and not recorder.is_stop_requested:
            await asyncio.sleep(0.3)
        if recorder.is_stop_requested:
            print("\n⏹️  收到停止請求（來自停止按鈕或 Esc 鍵）")
        stop_event.set()

    stop_monitor = asyncio.ensure_future(wait_for_stop())

    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        pass

    # 確保停止 monitor 被取消
    stop_monitor.cancel()
    try:
        await stop_monitor
    except (asyncio.CancelledError, Exception):
        pass

    await recorder.stop()

    # 自動生成報告 (Markdown + HTML)
    if recorder.session_id:
        print(f"\n📄 {t('generating_report')}")
        md_path = generate_markdown_report(recorder.session_id, lang=args_lang)
        print(f"  {t('markdown_report')}: {md_path}")

        html_path = generate_html_report(recorder.session_id, lang=args_lang)
        print(f"  {t('html_report')}: {html_path}")

    return recorder.session_id


async def run_script_recorder(
    script_path: str,
    session_name: str = "Test Session",
    viewport_width: int = None,
    viewport_height: int = None,
    lang: str = None,
):
    """
    腳本模式：從 JSON 腳本自動執行測試步驟
    """
    vp_w = viewport_width or config.VIEWPORT_WIDTH
    vp_h = viewport_height or config.VIEWPORT_HEIGHT

    print("\n" + "=" * 60)
    print(f"  {t('script_mode')}")
    print(f"  {t('test_name')}: {session_name}")
    print(f"  Script: {script_path}")
    print(f"  {t('recording_size')}: {vp_w} x {vp_h}")
    print("=" * 60 + "\n")

    recorder = TestRecorder(session_name)

    # 從腳本中讀取起始 URL
    import json
    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    url = script_data.get("url", "https://example.com")
    headless = script_data.get("headless", config.HEADLESS)

    await recorder.start(
        url,
        headless=headless,
        interactive=False,
        viewport_width=vp_w,
        viewport_height=vp_h,
    )

    # 執行腳本
    await recorder.run_script(script_path)

    await recorder.stop()

    # 自動生成報告 (Markdown + HTML)
    if recorder.session_id:
        print(f"\n📄 {t('generating_report')}")
        md_path = generate_markdown_report(recorder.session_id, lang=lang)
        print(f"  {t('markdown_report')}: {md_path}")

        html_path = generate_html_report(recorder.session_id, lang=lang)
        print(f"  {t('html_report')}: {html_path}")

    return recorder.session_id


def generate_report(session_id: int, fmt: str = "markdown", lang: str = None):
    """生成測試報告"""
    if fmt == "html":
        output_path = generate_html_report(session_id, lang=lang)
    else:
        output_path = generate_markdown_report(session_id, lang=lang)
    print(f"{t('footer')}: {output_path}")


def main():
    # 初始化 i18n 語言
    if config.LANGUAGE in ("zh", "en"):
        set_lang(config.LANGUAGE)

    parser = argparse.ArgumentParser(
        description="Test Docs Platform - Automated Test Documentation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database
  python main.py --init-db

  # List all sessions
  python main.py --list

  # Interactive recording mode
  python main.py --interactive "https://example.com" --session-name "My Test"

  # Interactive recording + viewport preset
  python main.py --interactive "https://example.com" --dimensions FHD

  # Script auto execution mode
  python main.py --script scripts/login_test.json --session-name "Login Test"

  # Generate Markdown report
  python main.py --report 1

  # Generate HTML report
  python main.py --report-html 1

  # Language: --lang en (English) or --lang zh (Chinese)
  python main.py --report 1 --lang en

Available viewport presets:
  HD     - 1280 x 720
  FHD    - 1920 x 1080
  Laptop - 1366 x 768
  Tablet - 768 x 1024
  Mobile - 375 x 812
        """
    )
    parser.add_argument("--init-db", action="store_true", help="Initialize database")
    parser.add_argument("--list", action="store_true", help="List all test sessions")
    parser.add_argument("--interactive", type=str, metavar="URL",
                        help="Interactive mode: open browser and record user actions (provide URL)")
    parser.add_argument("--script", type=str, metavar="SCRIPT.json",
                        help="Script mode: load JSON test steps and execute automatically")
    parser.add_argument("--record", type=str, metavar="URL",
                        help="[Legacy] Simple recording mode (requires manual API calls)")
    parser.add_argument("--report", type=int, metavar="SESSION_ID",
                        help="Generate Markdown report for session")
    parser.add_argument("--report-html", type=int, metavar="SESSION_ID",
                        help="Generate HTML acceptance test plan for session")
    parser.add_argument("--session-name", type=str, default="Test Session",
                        help="Session name (default: Test Session)")
    parser.add_argument("--lang", type=str, choices=["zh", "en"], default=None,
                        help="Report language (zh=Chinese, en=English, default: config.LANGUAGE)")

    # Dimensions 參數
    parser.add_argument("--dimensions", type=str, metavar="PRESET",
                        choices=["HD", "FHD", "Laptop", "Tablet", "Mobile"],
                        help="Viewport size preset (HD/FHD/Laptop/Tablet/Mobile)")
    parser.add_argument("--width", type=int, metavar="WIDTH",
                        help="Viewport width (pixels)")
    parser.add_argument("--height", type=int, metavar="HEIGHT",
                        help="Viewport height (pixels)")

    args = parser.parse_args()

    # 解析尺寸
    vp_width, vp_height, dim_label = parse_dimensions(
        args.width, args.height, args.dimensions
    )

    # 設定語言 (CLI 參數優先)
    if args.lang and args.lang in ("zh", "en"):
        set_lang(args.lang)

    # 初始化數據庫
    if args.init_db:
        db_path = init_db()
        print(f"{t('db_initialized')}: {db_path}")
        return

    # 列出會話
    if args.list:
        list_sessions()
        return

    # 互動錄製模式（主要模式）
    if args.interactive:
        init_db()  # 確保數據庫存在
        if args.dimensions or args.width:
            print(f"🖥️  {t('recording_size')}: {dim_label}")
        asyncio.run(run_interactive_recorder(
            args.interactive, args.session_name,
            viewport_width=vp_width,
            viewport_height=vp_height,
            lang=args.lang,
        ))
        return

    # 腳本執行模式
    if args.script:
        init_db()
        if args.dimensions or args.width:
            print(f"🖥️  {t('recording_size')}: {dim_label}")
        asyncio.run(run_script_recorder(
            args.script, args.session_name,
            viewport_width=vp_width,
            viewport_height=vp_height,
            lang=args.lang,
        ))
        return

    # 舊版兼容：簡單錄製模式
    if args.record:
        from core.recorder import TestRecorder

        async def simple_record(url, session_name):
            print("⚠️  注意：--record 模式不會自動執行操作")
            print("   請改用 --interactive 互動模式 或 --script 腳本模式\n")
            recorder = TestRecorder(session_name)
            await recorder.start(url, headless=config.HEADLESS)
            await recorder.stop()
            return recorder.session_id

        init_db()
        session_id = asyncio.run(simple_record(args.record, args.session_name))
        print(f"錄製完成 - Session ID: {session_id}")
        return

    # 生成 Markdown 報告
    if args.report:
        generate_report(args.report, fmt="markdown", lang=args.lang)
        return

    # 生成 HTML 報告
    if args.__dict__.get("report_html"):
        generate_report(args.__dict__["report_html"], fmt="html", lang=args.lang)
        return

    # 默認顯示幫助
    parser.print_help()


if __name__ == "__main__":
    main()