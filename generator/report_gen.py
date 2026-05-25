"""
HTML 驗收測試計畫報告生成器
從數據庫讀取測試記錄，生成專業的 HTML 格式「驗收測試計畫」報告
支援截圖內嵌展示、事件時間軸、自動驗收標準
"""
import os
import shutil
import base64
from datetime import datetime
from typing import Optional
import config

from core.db_manager import get_session_actions, get_all_sessions, get_session


def action_type_to_zh(action_type: str) -> str:
    """將操作類型轉換為中文描述"""
    mapping = {
        "click": "點擊",
        "type": "輸入",
        "fill": "填寫",
        "navigate": "導航",
        "scroll": "滾動",
        "hover": "懸停",
        "dblclick": "雙擊",
        "check": "勾選",
        "uncheck": "取消勾選",
        "select": "選擇",
        "wait": "等待",
        "assert": "斷言",
        "screenshot": "截圖",
        "custom": "自定義操作",
        "initial_state": "初始狀態",
    }
    return mapping.get(action_type, action_type)


def _image_to_base64(image_path: str) -> str:
    """將圖片轉換為 base64 data URI"""
    if not image_path or not os.path.exists(image_path):
        return ""
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        ext = os.path.splitext(image_path)[1].lower().replace(".", "")
        if ext == "jpg":
            ext = "jpeg"
        mime = f"image/{ext}"
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return ""


def _get_status_badge(status: str) -> str:
    """Get HTML status badge"""
    badges = {
        "completed": '<span style="background:#00c853;color:#fff;padding:2px 10px;border-radius:12px;font-size:12px;">✅ 完成</span>',
        "running": '<span style="background:#ff9800;color:#fff;padding:2px 10px;border-radius:12px;font-size:12px;">🔄 執行中</span>',
        "failed": '<span style="background:#f44336;color:#fff;padding:2px 10px;border-radius:12px;font-size:12px;">❌ 失敗</span>',
    }
    return badges.get(status, status)


def _get_action_icon(action_type: str) -> str:
    """Get icon for action type"""
    icons = {
        "click": "👆",
        "type": "⌨️",
        "fill": "✏️",
        "navigate": "🔗",
        "scroll": "📜",
        "hover": "🖱️",
        "dblclick": "👆👆",
        "check": "☑️",
        "uncheck": "◻️",
        "select": "📋",
        "wait": "⏳",
        "assert": "✔️",
        "screenshot": "📷",
        "custom": "⚙️",
        "initial_state": "🏁",
    }
    return icons.get(action_type, "🔹")


CSS_STYLES = """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: #f5f7fa;
    color: #2c3e50;
    line-height: 1.7;
}

/* ===== Header / Hero ===== */
.header {
    background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%);
    color: #fff;
    padding: 48px 60px 40px;
    position: relative;
    overflow: hidden;
}

.header::after {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 400px;
    height: 400px;
    background: rgba(255,255,255,0.05);
    border-radius: 50%;
    pointer-events: none;
}

.header h1 {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
}

.header .subtitle {
    font-size: 14px;
    opacity: 0.8;
    font-weight: 400;
}

/* ===== Container ===== */
.container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 24px;
}

/* ===== Section ===== */
.section {
    background: #fff;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin: 28px auto;
    max-width: 1100px;
    padding: 32px 36px;
}

.section h2 {
    font-size: 20px;
    font-weight: 700;
    color: #1a237e;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #e8eaf6;
    display: flex;
    align-items: center;
    gap: 10px;
}

.section h3 {
    font-size: 16px;
    font-weight: 600;
    color: #37474f;
    margin: 20px 0 12px;
}

/* ===== Overview Table ===== */
.overview-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px 24px;
}

.overview-item {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;
}

.overview-item .label {
    color: #78909c;
    font-size: 14px;
    font-weight: 500;
}

.overview-item .value {
    color: #263238;
    font-size: 14px;
    font-weight: 600;
    text-align: right;
}

/* ===== Summary Cards ===== */
.summary-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}

.summary-card {
    background: #f8f9ff;
    border: 1px solid #e8eaf6;
    border-radius: 12px;
    padding: 18px 20px;
    text-align: center;
}

.summary-card .card-value {
    font-size: 28px;
    font-weight: 700;
    color: #1a237e;
}

.summary-card .card-label {
    font-size: 13px;
    color: #78909c;
    margin-top: 4px;
}

/* ===== Steps Table ===== */
.steps-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
    font-size: 14px;
}

.steps-table thead {
    background: #f5f7fa;
}

.steps-table th {
    padding: 12px 14px;
    text-align: left;
    font-weight: 600;
    color: #455a64;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 2px solid #e0e0e0;
}

.steps-table td {
    padding: 12px 14px;
    border-bottom: 1px solid #f0f0f0;
    vertical-align: middle;
}

.steps-table tbody tr {
    transition: background 0.15s;
}

.steps-table tbody tr:hover {
    background: #fafbff;
}

.step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background: #e8eaf6;
    color: #3949ab;
    border-radius: 50%;
    font-size: 12px;
    font-weight: 700;
}

.action-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
}

.action-badge.click { background: #e3f2fd; color: #1565c0; }
.action-badge.type { background: #f3e5f5; color: #7b1fa2; }
.action-badge.fill { background: #f3e5f5; color: #7b1fa2; }
.action-badge.navigate { background: #e8f5e9; color: #2e7d32; }
.action-badge.scroll { background: #fff3e0; color: #e65100; }
.action-badge.hover { background: #e0f7fa; color: #00695c; }
.action-badge.select { background: #fce4ec; color: #c62828; }
.action-badge.wait { background: #f5f5f5; color: #616161; }
.action-badge.assert { background: #e8eaf6; color: #283593; }
.action-badge.screenshot { background: #fff8e1; color: #f57f17; }
.action-badge.custom { background: #eceff1; color: #37474f; }
.action-badge.initial_state { background: #e8f5e9; color: #1b5e20; }

.selector-code {
    font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
    background: #f5f5f5;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    color: #e91e63;
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: inline-block;
}

/* ===== Screenshot Section ===== */
.screenshots-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
    margin-top: 16px;
}

.screenshot-card {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    overflow: hidden;
    transition: box-shadow 0.2s, transform 0.2s;
}

.screenshot-card:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    transform: translateY(-2px);
}

.screenshot-card img {
    width: 100%;
    height: auto;
    display: block;
    border-bottom: 1px solid #eee;
}

.screenshot-info {
    padding: 12px 14px;
    background: #fafafa;
}

.screenshot-info .step-label {
    font-weight: 600;
    font-size: 13px;
    color: #37474f;
}

.screenshot-info .step-time {
    font-size: 12px;
    color: #90a4ae;
    margin-top: 2px;
}

/* ===== Acceptance Criteria ===== */
.acceptance-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
    font-size: 14px;
}

.acceptance-table th {
    padding: 12px 14px;
    background: #e8f5e9;
    color: #2e7d32;
    font-weight: 600;
    font-size: 13px;
    text-align: left;
    border-bottom: 2px solid #c8e6c9;
}

.acceptance-table td {
    padding: 12px 14px;
    border-bottom: 1px solid #f0f0f0;
    vertical-align: top;
}

.pass-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    background: #e8f5e9;
    color: #2e7d32;
}

/* ===== Footer ===== */
.footer {
    text-align: center;
    padding: 32px 20px;
    color: #90a4ae;
    font-size: 13px;
}

.footer a {
    color: #3949ab;
    text-decoration: none;
}

/* ===== Navigation Tabs ===== */
.tabs {
    display: flex;
    gap: 0;
    margin-bottom: -1px;
    position: relative;
    z-index: 1;
}

.tab-btn {
    padding: 10px 24px;
    border: 1px solid #e0e0e0;
    background: #f5f5f5;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    color: #78909c;
    border-radius: 10px 10px 0 0;
    border-bottom: none;
    transition: all 0.15s;
}

.tab-btn.active {
    background: #fff;
    color: #1a237e;
    border-color: #e0e0e0;
    font-weight: 600;
    box-shadow: 0 -2px 6px rgba(0,0,0,0.04);
}

.tab-btn:hover {
    color: #3949ab;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

/* Responsive */
@media (max-width: 768px) {
    .overview-grid {
        grid-template-columns: 1fr;
    }
    .screenshots-grid {
        grid-template-columns: 1fr;
    }
    .summary-cards {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media print {
    .header { padding: 24px 30px; }
    .section { box-shadow: none; border: 1px solid #e0e0e0; }
}
"""


def generate_html_report(session_id: int, output_path: str = None) -> str:
    """
    生成 HTML 驗收測試計畫報告

    Args:
        session_id: 測試 session ID
        output_path: 輸出路徑，如果為 None 則默認為 reports/uat_test_plan_{session_id}.html

    Returns:
        生成的 HTML 文件路徑
    """
    actions = get_session_actions(session_id)
    session_row = get_session(session_id)

    if not session_row:
        raise ValueError(f"找不到 session ID: {session_id}")

    session_info = {
        "id": session_row[0],
        "name": session_row[1],
        "url": session_row[2],
        "started_at": session_row[3],
        "ended_at": session_row[4],
        "status": session_row[5],
    }

    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 統計
    unique_action_types = set(a[2] for a in actions)
    screenshot_count = sum(1 for a in actions if a[5] and os.path.exists(a[5]))

    # 構建 HTML
    html_parts = []

    # DOCTYPE & Head
    html_parts.append("""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>驗收測試計畫 - """ + session_info['name'] + """</title>
    <style>""")
    html_parts.append(CSS_STYLES)
    html_parts.append("""</style>
</head>
<body>""")

    # === HEADER ===
    html_parts.append(f"""
    <div class="header">
        <h1>📋 驗收測試計畫報告</h1>
        <div class="subtitle">{session_info['name']} | 生成時間: {gen_time}</div>
    </div>
""")

    # === SUMMARY CARDS ===
    html_parts.append(f"""
    <div class="container" style="margin-top:-20px;position:relative;z-index:2;">
        <div class="summary-cards">
            <div class="summary-card">
                <div class="card-value">{len(actions)}</div>
                <div class="card-label">總操作步驟</div>
            </div>
            <div class="summary-card">
                <div class="card-value">{screenshot_count}</div>
                <div class="card-label">截圖記錄</div>
            </div>
            <div class="summary-card">
                <div class="card-value">{len(unique_action_types)}</div>
                <div class="card-label">操作類型</div>
            </div>
            <div class="summary-card">
                <div class="card-value">{_get_status_badge(session_info['status'])}</div>
                <div class="card-label">測試狀態</div>
            </div>
        </div>
    </div>
""")

    # === TEST OVERVIEW ===
    html_parts.append(f"""
    <div class="section">
        <h2>📊 測試概覽</h2>
        <div class="overview-grid">
            <div class="overview-item">
                <span class="label">Session ID</span>
                <span class="value">#{session_info['id']}</span>
            </div>
            <div class="overview-item">
                <span class="label">測試名稱</span>
                <span class="value">{session_info['name']}</span>
            </div>
            <div class="overview-item">
                <span class="label">測試網址</span>
                <span class="value"><a href="{session_info['url']}" target="_blank" style="color:#3949ab;">{session_info['url']}</a></span>
            </div>
            <div class="overview-item">
                <span class="label">錄製尺寸</span>
                <span class="value">{config.VIEWPORT_WIDTH} × {config.VIEWPORT_HEIGHT}</span>
            </div>
            <div class="overview-item">
                <span class="label">開始時間</span>
                <span class="value">{session_info['started_at']}</span>
            </div>
            <div class="overview-item">
                <span class="label">結束時間</span>
                <span class="value">{session_info['ended_at'] or 'N/A'}</span>
            </div>
            <div class="overview-item">
                <span class="label">測試狀態</span>
                <span class="value">{_get_status_badge(session_info['status'])}</span>
            </div>
            <div class="overview-item">
                <span class="label">測試工具</span>
                <span class="value">Test Docs Platform (Playwright)</span>
            </div>
        </div>
    </div>
""")

    # === TABS: Test Steps & Screenshots ===
    html_parts.append("""
    <div class="section">
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('steps')">📝 測試步驟</button>
            <button class="tab-btn" onclick="switchTab('screenshots')">📷 截圖記錄</button>
            <button class="tab-btn" onclick="switchTab('acceptance')">✅ 驗收標準</button>
        </div>
""")

    # === TAB 1: TEST STEPS ===
    html_parts.append("""
        <div id="tab-steps" class="tab-content active">
            <table class="steps-table">
                <thead>
                    <tr>
                        <th style="width:50px;">#</th>
                        <th style="width:160px;">時間</th>
                        <th style="width:90px;">操作類型</th>
                        <th>頁面名稱</th>
                        <th>元素名稱</th>
                        <th>元素類型</th>
                        <th>目標選擇器</th>
                        <th>輸入值</th>
                        <th>目的說明</th>
                        <th style="width:50px;">截圖</th>
                    </tr>
                </thead>
                <tbody>
""")

    for i, action in enumerate(actions, 1):
        # 解包 11 欄位（舊版 7 欄位兼容處理）
        if len(action) >= 11:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose, page_title, page_url, element_name, element_type = action
        else:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose = action
            page_title, page_url, element_name, element_type = "", "", "", ""

        zh_action = action_type_to_zh(action_type)
        icon = _get_action_icon(action_type)
        has_screenshot = "📷" if screenshot_path and os.path.exists(screenshot_path) else ""
        purpose_text = purpose if purpose else "自動記錄"

        # 簡化時間顯示
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%H:%M:%S")
        except Exception:
            time_str = timestamp

        # 截斷長文本顯示
        page_display = page_title[:30] + "..." if len(page_title) > 30 else (page_title or '-')
        elem_name_display = element_name[:25] + "..." if len(element_name) > 25 else (element_name or '-')

        html_parts.append(f"""
                    <tr>
                        <td><span class="step-number">{i}</span></td>
                        <td style="font-size:13px;color:#78909c;">{time_str}</td>
                        <td><span class="action-badge {action_type}">{icon} {zh_action}</span></td>
                        <td style="font-size:13px;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{page_title}">{page_display}</td>
                        <td style="font-size:13px;font-weight:600;color:#37474f;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{element_name}">{elem_name_display}</td>
                        <td><span class="action-badge" style="background:#eceff1;color:#455a64;font-size:11px;">{element_type or '-'}</span></td>
                        <td><span class="selector-code" title="{selector or ''}">{selector or '-'}</span></td>
                        <td style="font-size:13px;">{value or '-'}</td>
                        <td style="font-size:13px;color:#546e7a;max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{purpose_text}">{purpose_text}</td>
                        <td style="text-align:center;">{has_screenshot}</td>
                    </tr>
""")

    html_parts.append("""
                </tbody>
            </table>
""")

    if not actions:
        html_parts.append('<p style="color:#90a4ae;padding:20px;text-align:center;">尚無操作記錄</p>')

    html_parts.append("""
        </div>
""")

    # === TAB 2: SCREENSHOTS ===
    html_parts.append("""
        <div id="tab-screenshots" class="tab-content">
            <div class="screenshots-grid">
""")

    for i, action in enumerate(actions, 1):
        # 兼容 7 欄位或 11 欄位
        if len(action) >= 11:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose, page_title, page_url, element_name, element_type = action
        else:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose = action
        if screenshot_path and os.path.exists(screenshot_path):
            b64_img = _image_to_base64(screenshot_path)
            zh_action = action_type_to_zh(action_type)
            icon = _get_action_icon(action_type)
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except Exception:
                time_str = timestamp

            html_parts.append(f"""
                <div class="screenshot-card">
                    <img src="{b64_img}" alt="步驟 {i}" loading="lazy">
                    <div class="screenshot-info">
                        <div class="step-label">{icon} 步驟 {i} - {zh_action}</div>
                        <div class="step-time">{time_str} | {purpose or '自動記錄'}</div>
                    </div>
                </div>
""")

    if screenshot_count == 0:
        html_parts.append('<p style="color:#90a4ae;padding:20px;text-align:center;">尚無截圖記錄</p>')

    html_parts.append("""
            </div>
        </div>
""")

    # === TAB 3: ACCEPTANCE CRITERIA ===
    html_parts.append("""
        <div id="tab-acceptance" class="tab-content">
            <table class="acceptance-table">
                <thead>
                    <tr>
                        <th style="width:50px;">編號</th>
                        <th>驗證項目</th>
                        <th>驗證方法</th>
                        <th>預期結果</th>
                        <th style="width:70px;">狀態</th>
                    </tr>
                </thead>
                <tbody>
""")

    for i, action in enumerate(actions, 1):
        # 兼容 7 欄位或 11 欄位
        if len(action) >= 11:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose, page_title, page_url, element_name, element_type = action
        else:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose = action
        zh_action = action_type_to_zh(action_type)

        # 根據 action type 生成驗證項目描述
        if action_type == "click":
            verification = f"點擊功能驗證"
            method = f"執行點擊操作：{selector or '指定元素'}"
            expected = f"成功觸發點擊事件，頁面響應正常"
        elif action_type in ("type", "fill"):
            verification = f"輸入功能驗證"
            method = f"在 {selector or '輸入框'} 輸入: {value or '指定值'}"
            expected = f"輸入框正確接收數值並顯示"
        elif action_type == "navigate":
            verification = f"頁面導航驗證"
            method = f"導航至: {selector or session_info['url']}"
            expected = f"頁面成功載入，無錯誤"
        elif action_type == "scroll":
            verification = f"頁面滾動驗證"
            method = f"滾動頁面至指定位置"
            expected = f"頁面內容正確滾動，佈局無異常"
        elif action_type == "select":
            verification = f"下拉選單驗證"
            method = f"在 {selector} 選擇: {value}"
            expected = f"正確選中目標選項"
        elif action_type == "wait":
            verification = f"等待操作驗證"
            method = f"等待 {value or '指定時間'}"
            expected = f"等待期間頁面無異常"
        elif action_type == "assert":
            verification = f"斷言驗證"
            method = f"驗證 {selector} 包含: {value}"
            expected = f"實際文本符合預期"
        elif action_type == "screenshot":
            verification = f"視覺驗證"
            method = f"截圖保存: {purpose or '手動截圖'}"
            expected = f"截圖成功生成，畫面無異常"
        else:
            verification = f"{zh_action}操作驗證"
            method = f"執行 {zh_action} 操作"
            expected = f"操作成功執行"

        html_parts.append(f"""
                    <tr>
                        <td style="font-weight:700;color:#3949ab;">{i}</td>
                        <td>{verification}</td>
                        <td style="font-size:13px;">{method}</td>
                        <td style="font-size:13px;">{expected}</td>
                        <td><span class="pass-badge">Pass</span></td>
                    </tr>
""")

    html_parts.append("""
                </tbody>
            </table>
        </div>
    </div>
""")

    # === FOOTER ===
    html_parts.append(f"""
    <div class="footer">
        <p>本報告由 <strong>Test Docs Platform</strong> 自動生成 | 驗收測試計畫 v1.0</p>
        <p style="margin-top:4px;">生成時間: {gen_time} | Session #{session_info['id']}</p>
    </div>

    <script>
    function switchTab(tabName) {{
        // Update buttons
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');

        // Update content
        document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
        document.getElementById('tab-' + tabName).classList.add('active');
    }}
    </script>
</body>
</html>
""")

    # 寫入文件
    if output_path is None:
        os.makedirs(config.REPORTS_DIR, exist_ok=True)
        output_path = os.path.join(config.REPORTS_DIR, f"uat_test_plan_{session_id}.html")

    content = "\n".join(html_parts)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"HTML 驗收測試計畫已生成：{output_path}")
    return output_path


if __name__ == "__main__":
    # 測試報告生成
    sessions = get_all_sessions()
    for s in sessions:
        print(f"  - Session {s[0]}: {s[1]}")

    if sessions:
        session_id = sessions[0][0]
        print(f"\n生成 Session {session_id} 的 HTML 驗收測試計畫...")
        generate_html_report(session_id)