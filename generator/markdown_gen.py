"""
Markdown 報告生成器
從數據庫讀取測試記錄，生成帶有截圖的測試報告
"""
import os
from datetime import datetime
import config

from core.db_manager import get_session_actions, get_all_sessions, get_session
from i18n import t, get_lang, set_lang


def _action_type(key: str) -> str:
    """翻譯 action_type"""
    return t(f"action_{key}")


def generate_markdown_report(session_id: int, output_path: str = None, lang: str = None) -> str:
    """
    生成 Markdown 測試報告

    Args:
        session_id: 測試 session ID
        output_path: 輸出路徑，如果為 None 則默認為 reports/test_plan_{session_id}.md
        lang: 語言覆蓋 ('zh' or 'en')，預設使用 config.LANGUAGE

    Returns:
        生成的 Markdown 文件路徑
    """
    # 設定語言
    orig_lang = get_lang()
    if lang and lang in ("zh", "en"):
        set_lang(lang)
    elif config.LANGUAGE and config.LANGUAGE in ("zh", "en"):
        set_lang(config.LANGUAGE)

    actions = get_session_actions(session_id)
    session_row = get_session(session_id)

    if not session_row:
        raise ValueError(f"Session not found: {session_id}")

    session_info = {
        "id": session_row[0],
        "name": session_row[1],
        "url": session_row[2],
        "started_at": session_row[3],
        "ended_at": session_row[4],
        "status": session_row[5]
    }

    # 構建報告
    lines = []

    # 標題
    lines.append(f"# {t('report_title')} - {session_info['name']}")
    lines.append("")
    lines.append(f"**{t('generated_at')}**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # 測試概覽
    lines.append(f"## {t('test_overview')}")
    lines.append("")
    lines.append(f"| {t('test_overview_id')} | {t('session_id')} |")
    lines.append(f"| {t('test_overview_name')} | {session_info['name']} |")
    lines.append(f"| {t('test_overview_url')} | {session_info['url']} |")
    lines.append(f"| {t('start_time')} | {session_info['started_at']} |")
    lines.append(f"| {t('end_time')} | {session_info['ended_at'] or '-'} |")
    lines.append(f"| {t('status')} | {session_info['status']} |")
    lines.append(f"| {t('total_actions')} | {len(actions)} |")
    lines.append("")

    # 測試步驟詳情
    lines.append(f"## {t('test_steps_detail')}")
    lines.append("")

    if not actions:
        lines.append(f"> {t('no_actions')}")
    else:
        lines.append(f"| {t('step_num')} | {t('time')} | {t('action_type')} | {t('page_title_col')} | {t('element_id')} | {t('element_name')} | {t('element_type')} | {t('target_selector')} | {t('input_value')} | {t('screenshot')} | {t('purpose')} |")
        lines.append("|------|------|----------|----------|------|----------|----------|------------|--------|------|------|")

        for i, action in enumerate(actions, 1):
            # 兼容 7 / 11 / 12 欄位
            if len(action) >= 12:
                action_id, timestamp, action_type, selector, value, screenshot_path, purpose, page_title, page_url, element_name, element_type, element_id = action
            elif len(action) >= 11:
                action_id, timestamp, action_type, selector, value, screenshot_path, purpose, page_title, page_url, element_name, element_type = action
                element_id = ""
            else:
                action_id, timestamp, action_type, selector, value, screenshot_path, purpose = action
                page_title, page_url, element_name, element_type, element_id = "", "", "", "", ""

            zh_action = _action_type(action_type)
            screenshot_mark = "📷" if screenshot_path and os.path.exists(screenshot_path) else ""
            purpose_text = purpose if purpose else t("auto_recorded")

            # 截斷長文本
            page_display = (page_title[:30] + "...") if len(page_title) > 30 else (page_title or '-')
            elem_display = (element_name[:25] + "...") if len(element_name) > 25 else (element_name or '-')
            elem_id_display = element_id if element_id else '-'

            lines.append(f"| {i} | {timestamp} | {zh_action} | {page_display} | `{elem_id_display}` | {elem_display} | {element_type or '-'} | `{selector or '-'}` | `{value or '-'}` | {screenshot_mark} | {purpose_text} |")

        lines.append("")

        # 截圖部分
        lines.append(f"## {t('screenshot_record')}")
        lines.append("")

        for i, action in enumerate(actions, 1):
            if len(action) >= 12:
                action_id, timestamp, action_type, selector, value, screenshot_path, purpose, page_title, page_url, element_name, element_type, element_id = action
            elif len(action) >= 11:
                action_id, timestamp, action_type, selector, value, screenshot_path, purpose, page_title, page_url, element_name, element_type = action
            else:
                action_id, timestamp, action_type, selector, value, screenshot_path, purpose = action
            if screenshot_path and os.path.exists(screenshot_path):
                # 使用相對於 reports/ 資料夾的路徑
                rel_path = os.path.relpath(screenshot_path, config.REPORTS_DIR).replace("\\", "/")
                lines.append(f"### {t('step')} {i} - {_action_type(action_type)}")
                lines.append("")
                lines.append(f"![{action_type}]({rel_path})")
                lines.append("")

    # 驗證標準
    lines.append(f"## {t('auto_acceptance_criteria')}")
    lines.append("")
    lines.append(f"| {t('item_num')} | {t('verify_item')} | {t('verify_method')} | {t('expected_result')} |")
    lines.append("|------|----------|----------|---------|")

    for i, action in enumerate(actions, 1):
        if len(action) >= 12:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose, page_title, page_url, element_name, element_type, element_id = action
        elif len(action) >= 11:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose, page_title, page_url, element_name, element_type = action
        else:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose = action
        if action_type == "click":
            lines.append(f"| {i} | {t('click_verify')} | {t('click_desc')} | {t('click_result', selector=selector or '-')} |")
        elif action_type == "type":
            lines.append(f"| {i} | {t('type_verify')} | {t('type_desc')} | {t('type_result', selector=selector or '-', value=value or '')} |")
        elif action_type == "navigate":
            lines.append(f"| {i} | {t('navigate_verify')} | {t('navigate_desc')} | {t('navigate_result', selector=selector or '-')} |")

    lines.append("")
    lines.append("---")
    lines.append(f"*{t('footer')}*")

    # 寫入文件
    if output_path is None:
        os.makedirs(config.REPORTS_DIR, exist_ok=True)
        output_path = os.path.join(config.REPORTS_DIR, f"test_plan_{session_id}.md")

    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"{t('markdown_report')}: {output_path}")

    # 恢復原本語言
    set_lang(orig_lang)
    return output_path


def generate_all_sessions_report(lang: str = None) -> str:
    """生成所有 session 的報告列表"""
    orig_lang = get_lang()
    if lang and lang in ("zh", "en"):
        set_lang(lang)
    elif config.LANGUAGE and config.LANGUAGE in ("zh", "en"):
        set_lang(config.LANGUAGE)

    sessions = get_all_sessions()

    lines = []
    lines.append(f"# {t('all_sessions_title')}")
    lines.append("")
    lines.append(t("total_sessions", count=len(sessions)))
    lines.append("")
    lines.append(f"| {t('session_id')} | {t('test_name')} | {t('test_url')} | {t('start_time')} | {t('status')} | {t('generate_report')} |")
    lines.append("|------|------|------|----------|------|----------|")

    for s in sessions:
        session_id, name, url, started_at, ended_at, status = s
        lines.append(f"| {session_id} | {name} | {url} | {started_at} | {status} | [📄](test_plan_{session_id}.md) |")

    lines.append("")

    output_path = os.path.join(config.REPORTS_DIR, "all_sessions.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    set_lang(orig_lang)
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