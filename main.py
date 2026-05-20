#!/usr/bin/env python3
"""
自動化驗收與測試文檔平台
Main Entry Point
"""
import asyncio
import argparse
import sys

from core.db_manager import init_db, get_all_sessions
from core.recorder import TestRecorder
from generator.markdown_gen import generate_markdown_report, generate_all_sessions_report


def list_sessions():
    """列出所有測試會話"""
    sessions = get_all_sessions()
    if not sessions:
        print("尚無測試會話記錄")
        return []
    print("\n測試會話列表：")
    for s in sessions:
        print(f"  ID: {s[0]} | {s[1]} | {s[2]} | {s[5]}")
    return sessions


async def run_test_recorder(url: str, session_name: str = "測試會話"):
    """執行測試錄製"""
    print(f"開始錄製：{session_name}")
    print(f"目標網址：{url}")

    recorder = TestRecorder(session_name)
    page = await recorder.start(url)

    # 這裡可以根據需要添加更多測試邏輯
    # 例如：從配置文件讀取測試腳本，或通過 CLI 參數傳遞

    await recorder.stop()
    return recorder.session_id


def generate_report(session_id: int):
    """生成測試報告"""
    output_path = generate_markdown_report(session_id)
    print(f"報告已生成：{output_path}")


def main():
    parser = argparse.ArgumentParser(description="自動化驗收與測試文檔平台")
    parser.add_argument("--init-db", action="store_true", help="初始化數據庫")
    parser.add_argument("--list", action="store_true", help="列出所有測試會話")
    parser.add_argument("--record", type=str, help="開始錄製測試（提供 URL）")
    parser.add_argument("--report", type=int, help="生成指定 session 的報告")
    parser.add_argument("--session-name", type=str, default="測試會話", help="Session 名稱")

    args = parser.parse_args()

    if args.init_db:
        db_path = init_db()
        print(f"數據庫已初始化：{db_path}")
        return

    if args.list:
        list_sessions()
        return

    if args.record:
        session_id = asyncio.run(run_test_recorder(args.record, args.session_name))
        print(f"錄製完成 - Session ID: {session_id}")
        return

    if args.report:
        generate_report(args.report)
        return

    # 默认顯示幫助
    parser.print_help()


if __name__ == "__main__":
    main()
