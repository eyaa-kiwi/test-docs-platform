"""
Markdown 報告生成器
從數據庫讀取測試記錄，生成帶有截圖的測試報告
"""
import os
from datetime import datetime
from typing import List, Dict, Any
import config

# 導入數據庫模塊
from core.db_manager import get_session_actions, get_all_sessions


def action_type_to_zh(action_type: str) -> str:
    """將操作類型轉換為中文描述"""
    mapping = {
        "click": "點擊",
        "type": "輸入",
        "navigate": "導航",
        "scroll": "滾動",
        "hover": "懸停",
        "dblclick": "雙擊",
        "check": "勾選",
        "uncheck": "取消勾選",
        "select": "選擇",
        "wait": "等待",
        "assert": "斷言"
    }
    return mapping.get(action_type, action_type)


def generate_markdown_report(session_id: int, output_path: str = None) -> str:
    """
    生成 Markdown 測試報告

    Args:
        session_id: 測試 session ID
        output_path: 輸出路徑，如果為 None 則默認為 reports/test_plan_{session_id}.md

    Returns:
        生成的 Markdown 文件路徑
    """
    actions = get_session_actions(session_id)
    sessions = get_all_sessions()

    # 找到 session 信息
    session_info = None
    for s in sessions:
        if s[0] == session_id:
            session_info = {
                "id": s[0],
                "name": s[1],
                "url": s[2],
                "started_at": s[3],
                "ended_at": s[4],
                "status": s[5]
            }
            break

    if not session_info:
        raise ValueError(f"找不到 session ID: {session_id}")

    # 構建報告
    lines = []

    # 標題
    lines.append(f"# 測試計書報告 - {session_info['name']}")
    lines.append("")
    lines.append(f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # 測試概覽
    lines.append("## 測試概覽")
    lines.append("")
    lines.append(f"| 項目 | 內容 |")
    lines.append(f"|------|------|")
    lines.append(f"| Session ID | {session_info['id']} |")
    lines.append(f"| 測試名稱 | {session_info['name']} |")
    lines.append(f"| 測試網址 | {session_info['url']} |")
    lines.append(f"| 開始時間 | {session_info['started_at']} |")
    lines.append(f"| 結束時間 | {session_info['ended_at']} |")
    lines.append(f"| 狀態 | {session_info['status']} |")
    lines.append(f"| 總操作數 | {len(actions)} |")
    lines.append("")

    # 測試步驟詳情
    lines.append("## 測試步驟詳情")
    lines.append("")

    if not actions:
        lines.append("> 無操作記錄")
    else:
        lines.append("| 序號 | 時間 | 操作類型 | 目標選擇器 | 輸入值 | 截圖 | 目的 |")
        lines.append("|------|------|----------|------------|--------|------|------|")

        for i, action in enumerate(actions, 1):
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose = action

            zh_action = action_type_to_zh(action_type)
            screenshot_mark = "📷" if screenshot_path and os.path.exists(screenshot_path) else ""
            purpose_text = purpose if purpose else "自動記錄"

            lines.append(f"| {i} | {timestamp} | {zh_action} | `{selector or '-'}` | `{value or '-'}` | {screenshot_mark} | {purpose_text} |")

        lines.append("")

        # 截圖部分
        lines.append("## 截圖記錄")
        lines.append("")

        for i, action in enumerate(actions, 1):
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose = action
            if screenshot_path and os.path.exists(screenshot_path):
                lines.append(f"### 步驟 {i} - {action_type_to_zh(action_type)}")
                lines.append("")
                lines.append(f"![{action_type}]({screenshot_path})")
                lines.append("")

    # 驗證標準
    lines.append("## 自動驗收標準")
    lines.append("")
    lines.append("| 編號 | 驗證項目 | 驗證方法 | 預期結果 |")
    lines.append("|------|----------|----------|---------|")

    for i, action in enumerate(actions, 1):
        action_id, timestamp, action_type, selector, value, screenshot_path, purpose = action
        if action_type == "click":
            lines.append(f"| {i} | 點擊功能驗證 | 執行點擊操作 | 成功觸發 {selector} 點擊事件 |")
        elif action_type == "type":
            lines.append(f"| {i} | 輸入功能驗證 | 執行輸入操作 | 成功在 {selector} 輸入 {value} |")
        elif action_type == "navigate":
            lines.append(f"| {i} | 頁面導航驗證 | 執行導航操作 | 成功跳轉至 {selector} |")

    lines.append("")
    lines.append("---")
    lines.append(f"*本報告由 Test Docs Platform 自動生成*")

    # 寫入文件
    if output_path is None:
        os.makedirs(config.REPORTS_DIR, exist_ok=True)
        output_path = os.path.join(config.REPORTS_DIR, f"test_plan_{session_id}.md")

    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"測試報告已生成：{output_path}")
    return output_path


def generate_all_sessions_report() -> str:
    """生成所有 session 的報告列表"""
    sessions = get_all_sessions()

    lines = []
    lines.append("# 所有測試會話列表")
    lines.append("")
    lines.append(f"共 {len(sessions)} 個會話")
    lines.append("")
    lines.append("| ID | 名稱 | 網址 | 開始時間 | 狀態 | 生成報告 |")
    lines.append("|----|------|------|----------|------|----------|")

    for s in sessions:
        session_id, name, url, started_at, ended_at, status = s
        lines.append(f"| {session_id} | {name} | {url} | {started_at} | {status} | [報告](test_plan_{session_id}.md) |")

    lines.append("")

    output_path = os.path.join(config.REPORTS_DIR, "all_sessions.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


if __name__ == "__main__":
    # 測試報告生成
    print("可用的 sessions:")
    sessions = get_all_sessions()
    for s in sessions:
        print(f"  - Session {s[0]}: {s[1]}")

    if sessions:
        session_id = sessions[0][0]
        print(f"\n生成 Session {session_id} 的報告...")
        generate_markdown_report(session_id)
