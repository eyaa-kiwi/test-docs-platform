"""
i18n - 國際化模組
支援語言：zh (繁體中文), en (English)

用法:
    from i18n import t, set_lang, get_lang

    set_lang("en")          # 設定為英文
    set_lang("zh")           # 設定為中文

    t("report_title")        # 取翻譯
    t("click_result", selector="#btn")  # 帶參數
"""

from typing import Literal

# 當前語言 (預設中文)
_current_lang: Literal["zh", "en"] = "zh"


# ============================================================
# 翻譯字典
# ============================================================

_ZH = {
    # Markdown 報告
    "report_title": "測試計畫報告",
    "generated_at": "生成時間",
    "test_overview": "測試概覽",
    "session_id": "Session ID",
    "test_name": "測試名稱",
    "test_url": "測試網址",
    "start_time": "開始時間",
    "end_time": "結束時間",
    "status": "狀態",
    "total_actions": "總操作數",
    "test_steps_detail": "測試步驟詳情",
    "no_actions": "無操作記錄",
    "step_num": "序號",
    "time": "時間",
    "action_type": "操作類型",
    "page_title_col": "頁面名稱",
    "element_name": "元素名稱",
    "element_type": "元素類型",
    "target_selector": "目標選擇器",
    "input_value": "輸入值",
    "screenshot": "截圖",
    "purpose": "目的",
    "screenshot_record": "截圖記錄",
    "auto_acceptance_criteria": "自動驗收標準",
    "item_num": "編號",
    "verify_item": "驗證項目",
    "verify_method": "驗證方法",
    "expected_result": "預期結果",
    "footer": "本報告由 Test Docs Platform 自動生成",
    "auto_recorded": "自動記錄",
    "click_verify": "點擊功能驗證",
    "click_desc": "執行點擊操作",
    "click_result": "成功觸發 {selector} 點擊事件",
    "type_verify": "輸入功能驗證",
    "type_desc": "執行輸入操作",
    "type_result": "成功在 {selector} 輸入 {value}",
    "navigate_verify": "頁面導航驗證",
    "navigate_desc": "執行導航操作",
    "navigate_result": "成功跳轉至 {selector}",
    "all_sessions_title": "所有測試會話列表",
    "total_sessions": "共 {count} 個會話",
    "generate_report": "生成報告",
    "step": "步驟",

    # HTML 報告
    "html_title": "驗收測試計畫",
    "html_subtitle": "自動化驗收測試報告",
    "overview_title": "測試概覽",
    "test_summary": "測試摘要",
    "actions_count": "操作總數",
    "clicks_count": "點擊次數",
    "screenshots_count": "截圖數量",
    "duration": "總時長",
    "steps_title": "測試步驟",
    "step_col": "步驟",
    "time_col": "時間",
    "action_col": "操作",
    "selector_col": "選擇器",
    "value_col": "值",
    "screenshot_col": "截圖",
    "screenshots_title": "截圖記錄",
    "step_time": "時間",
    "acceptance_criteria_title": "自動驗收標準",
    "criteria_pass": "通過",
    "criteria_fail": "失敗",
    "criteria_no_method": "無",

    # Status
    "status_completed": "完成",
    "status_running": "執行中",
    "status_failed": "失敗",

    # CLI
    "db_initialized": "數據庫已初始化",
    "no_sessions": "尚無測試會話記錄",
    "sessions_list": "測試會話列表",
    "interactive_mode": "互動錄製模式",
    "script_mode": "腳本錄製模式",
    "recording_size": "錄製尺寸",
    "stopping_recording": "收到停止請求（來自停止按鈕或 Esc 鍵）",
    "generating_report": "正在生成測試報告...",
    "markdown_report": "Markdown 報告",
    "html_report": "HTML 驗收測試計畫",
    "test_complete": "測試腳本執行完成",
    "recording_complete": "錄製結束",
    "script_loaded": "載入測試腳本",
    "script_desc": "描述",
    "script_steps": "步驟數",
    "step_progress": "步驟 {i}/{total}",
    "unknown_action": "未知操作",
    "view_dimensions": "可用尺寸預設",
    "interactive_help": "互動錄製模式：打開瀏覽器，人工操作時自動記錄（提供 URL）",
    "script_help": "腳本執行模式：從 JSON 檔案讀取測試步驟自動執行",

    # recorder.py
    "recording_initial_page": "初始頁面載入",
    "page_initial": "初始頁面",
    "url": "URL",
    "navigated_to": "已導航至",
    "click_failed": "點擊失敗",
    "fill_failed": "輸入失敗",
    "select_failed": "選擇失敗",
    "assert_pass": "斷言",
    "assert_fail": "斷言",
    "contains": "包含",
    "actual": "實際",
    "viewport_size": "錄製尺寸",

    # Action types
    "action_click": "點擊",
    "action_type": "輸入",
    "action_fill": "填寫",
    "action_navigate": "導航",
    "action_scroll": "滾動",
    "action_hover": "懸停",
    "action_dblclick": "雙擊",
    "action_check": "勾選",
    "action_uncheck": "取消勾選",
    "action_select": "選擇",
    "action_wait": "等待",
    "action_assert": "斷言",
    "action_screenshot": "截圖",
    "action_custom": "自定義操作",
    "action_initial_state": "初始狀態",

    # Misc
    "waiting_ms": "等待 {ms}ms",
    "total_events_recorded": "總共記錄 {count} 個交互事件",
    "screenshot_count_num": "截圖數量",
    "test_overview_id": "ID",
    "test_overview_name": "名稱",
    "test_overview_url": "目標 URL",
}


_EN = {
    # Markdown 報告
    "report_title": "Test Plan Report",
    "generated_at": "Generated At",
    "test_overview": "Test Overview",
    "session_id": "Session ID",
    "test_name": "Test Name",
    "test_url": "Test URL",
    "start_time": "Start Time",
    "end_time": "End Time",
    "status": "Status",
    "total_actions": "Total Actions",
    "test_steps_detail": "Test Steps Detail",
    "no_actions": "No action records",
    "step_num": "#",
    "time": "Time",
    "action_type": "Action Type",
    "page_title_col": "Page Title",
    "element_name": "Element Name",
    "element_type": "Element Type",
    "target_selector": "Target Selector",
    "input_value": "Input Value",
    "screenshot": "Screenshot",
    "purpose": "Purpose",
    "screenshot_record": "Screenshot Records",
    "auto_acceptance_criteria": "Automated Acceptance Criteria",
    "item_num": "#",
    "verify_item": "Verification Item",
    "verify_method": "Verification Method",
    "expected_result": "Expected Result",
    "footer": "Generated by Test Docs Platform",
    "auto_recorded": "Auto recorded",
    "click_verify": "Click Function Verification",
    "click_desc": "Execute click operation",
    "click_result": "Successfully triggered click event on {selector}",
    "type_verify": "Input Function Verification",
    "type_desc": "Execute input operation",
    "type_result": "Successfully input {value} into {selector}",
    "navigate_verify": "Navigation Verification",
    "navigate_desc": "Execute navigation operation",
    "navigate_result": "Successfully navigated to {selector}",
    "all_sessions_title": "All Test Sessions",
    "total_sessions": "Total {count} sessions",
    "generate_report": "Generate Report",
    "step": "Step",

    # HTML 報告
    "html_title": "UAT Test Plan",
    "html_subtitle": "Automated Acceptance Test Report",
    "overview_title": "Test Overview",
    "test_summary": "Test Summary",
    "actions_count": "Total Actions",
    "clicks_count": "Total Clicks",
    "screenshots_count": "Screenshots",
    "duration": "Duration",
    "steps_title": "Test Steps",
    "step_col": "Step",
    "time_col": "Time",
    "action_col": "Action",
    "selector_col": "Selector",
    "value_col": "Value",
    "screenshot_col": "Screenshot",
    "screenshots_title": "Screenshot Records",
    "step_time": "Time",
    "acceptance_criteria_title": "Automated Acceptance Criteria",
    "criteria_pass": "Pass",
    "criteria_fail": "Fail",
    "criteria_no_method": "N/A",

    # Status
    "status_completed": "Completed",
    "status_running": "Running",
    "status_failed": "Failed",

    # CLI
    "db_initialized": "Database initialized",
    "no_sessions": "No test sessions found",
    "sessions_list": "Test Sessions",
    "interactive_mode": "Interactive Recording Mode",
    "script_mode": "Script Recording Mode",
    "recording_size": "Viewport Size",
    "stopping_recording": "Stop requested (from stop button or Esc key)",
    "generating_report": "Generating test report...",
    "markdown_report": "Markdown Report",
    "html_report": "HTML Acceptance Test Plan",
    "test_complete": "Test script completed",
    "recording_complete": "Recording stopped",
    "script_loaded": "Loaded test script",
    "script_desc": "Description",
    "script_steps": "Steps",
    "step_progress": "Step {i}/{total}",
    "unknown_action": "Unknown action",
    "view_dimensions": "Available viewport presets",
    "interactive_help": "Interactive mode: open browser and record user actions automatically",
    "script_help": "Script mode: load JSON test steps and execute automatically",

    # recorder.py
    "recording_initial_page": "Initial page loaded",
    "page_initial": "Initial page",
    "url": "URL",
    "navigated_to": "Navigated to",
    "click_failed": "Click failed",
    "fill_failed": "Fill failed",
    "select_failed": "Select failed",
    "assert_pass": "Assertion passed",
    "assert_fail": "Assertion failed",
    "contains": "contains",
    "actual": "Actual",
    "viewport_size": "Viewport Size",

    # Action types
    "action_click": "Click",
    "action_type": "Type",
    "action_fill": "Fill",
    "action_navigate": "Navigate",
    "action_scroll": "Scroll",
    "action_hover": "Hover",
    "action_dblclick": "Double-click",
    "action_check": "Check",
    "action_uncheck": "Uncheck",
    "action_select": "Select",
    "action_wait": "Wait",
    "action_assert": "Assert",
    "action_screenshot": "Screenshot",
    "action_custom": "Custom",
    "action_initial_state": "Initial State",

    # Misc
    "waiting_ms": "Wait {ms}ms",
    "total_events_recorded": "Total {count} interaction events recorded",
    "screenshot_count_num": "Screenshots",
    "test_overview_id": "ID",
    "test_overview_name": "Name",
    "test_overview_url": "Target URL",
}

TRANSLATIONS = {"zh": _ZH, "en": _EN}


# ============================================================
# 核心 API
# ============================================================

def set_lang(lang: Literal["zh", "en"]) -> None:
    """設定當前語言"""
    global _current_lang
    if lang in ("zh", "en"):
        _current_lang = lang


def get_lang() -> Literal["zh", "en"]:
    """取得當前語言"""
    return _current_lang


def t(key: str, **kwargs) -> str:
    """
    翻譯 key，key 不存在時返回 key 本身
    例如: t("click_result", selector="#btn")
    """
    d = TRANSLATIONS[_current_lang]
    text = d.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text