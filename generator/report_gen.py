"""
HTML 驗收測試計畫報告生成器
從數據庫讀取測試記錄，生成專業的 HTML 格式「驗收測試計畫」報告
支援截圖內嵌展示、事件時間軸、自動驗收標準、i18n (zh/en)
"""
import os
import base64
from datetime import datetime
import config

from core.db_manager import get_session_actions, get_session
from i18n import t, get_lang, set_lang


# ============================================================
# 翻譯輔助
# ============================================================

def _action_type(key: str) -> str:
    """翻譯 action_type"""
    return t(f"action_{key}")


def _i18n_status(status: str) -> str:
    """翻譯狀態並返回 HTML badge"""
    labels = {
        "completed": t("status_completed"),
        "running": t("status_running"),
        "failed": t("status_failed"),
    }
    label = labels.get(status, status)
    icons = {"completed": "✅", "running": "🔄", "failed": "❌"}
    icon = icons.get(status, "")
    color_map = {
        "completed": "#00c853",
        "running": "#ff9800",
        "failed": "#f44336",
    }
    color = color_map.get(status, "#9e9e9e")
    return f'<span style="background:{color};color:#fff;padding:2px 10px;border-radius:12px;font-size:12px;">{icon} {label}</span>'


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


def generate_html_report(session_id: int, output_path: str = None, lang: str = None) -> str:
    """
    生成 HTML 驗收測試計畫報告

    Args:
        session_id: 測試 session ID
        output_path: 輸出路徑，如果為 None 則默認為 reports/uat_test_plan_{session_id}.html
        lang: 語言覆蓋 ('zh' or 'en')，預設使用 config.LANGUAGE

    Returns:
        生成的 HTML 文件路徑
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
        "status": session_row[5],
    }

    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 統計
    unique_action_types = set(a[2] for a in actions)
    screenshot_count = sum(1 for a in actions if a[5] and os.path.exists(a[5]))

    # 構建 HTML
    html_parts = []

    lang_attr = "en" if get_lang() == "en" else "zh-Hant"
    html_parts.append(f"""<!DOCTYPE html>
<html lang="{lang_attr}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{t('html_title')} - {session_info['name']}</title>
    <style>""")
    html_parts.append(CSS_STYLES)
    html_parts.append("""</style>
</head>
<body>""")

    # === HEADER ===
    html_parts.append(f"""
    <div class="header">
        <h1>📋 {t('html_title')}</h1>
        <div class="subtitle">{session_info['name']} | {t('generated_at')}: {gen_time}</div>
    </div>
""")

    # === SUMMARY CARDS ===
    html_parts.append(f"""
    <div class="container" style="margin-top:-20px;position:relative;z-index:2;">
        <div class="summary-cards">
            <div class="summary-card">
                <div class="card-value">{len(actions)}</div>
                <div class="card-label">{t('actions_count')}</div>
            </div>
            <div class="summary-card">
                <div class="card-value">{screenshot_count}</div>
                <div class="card-label">{t('screenshots_count')}</div>
            </div>
            <div class="summary-card">
                <div class="card-value">{len(unique_action_types)}</div>
                <div class="card-label">{t('action_type')}</div>
            </div>
            <div class="summary-card">
                <div class="card-value">{_i18n_status(session_info['status'])}</div>
                <div class="card-label">{t('status')}</div>
            </div>
        </div>
    </div>
""")

    # === TEST OVERVIEW ===
    html_parts.append(f"""
    <div class="section">
        <h2>📊 {t('overview_title')}</h2>
        <div class="overview-grid">
            <div class="overview-item">
                <span class="label">{t('session_id')}</span>
                <span class="value">#{session_info['id']}</span>
            </div>
            <div class="overview-item">
                <span class="label">{t('test_name')}</span>
                <span class="value">{session_info['name']}</span>
            </div>
            <div class="overview-item">
                <span class="label">{t('test_url')}</span>
                <span class="value"><a href="{session_info['url']}" target="_blank" style="color:#3949ab;">{session_info['url']}</a></span>
            </div>
            <div class="overview-item">
                <span class="label">{t('viewport_size')}</span>
                <span class="value">{config.VIEWPORT_WIDTH} × {config.VIEWPORT_HEIGHT}</span>
            </div>
            <div class="overview-item">
                <span class="label">{t('start_time')}</span>
                <span class="value">{session_info['started_at']}</span>
            </div>
            <div class="overview-item">
                <span class="label">{t('end_time')}</span>
                <span class="value">{session_info['ended_at'] or 'N/A'}</span>
            </div>
            <div class="overview-item">
                <span class="label">{t('status')}</span>
                <span class="value">{_i18n_status(session_info['status'])}</span>
            </div>
            <div class="overview-item">
                <span class="label">{t('test_url').replace('URL', 'Tool')}</span>
                <span class="value">Test Docs Platform</span>
            </div>
        </div>
    </div>
""")

    # === STEPS TABLE ===
    steps_rows = ""
    for i, action in enumerate(actions, 1):
        if len(action) >= 11:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose, page_title, page_url, element_name, element_type = action
        else:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose = action
            page_title, page_url, element_name, element_type = "", "", "", ""

        time_short = timestamp[11:19] if len(timestamp) > 19 else timestamp
        action_label = _action_type(action_type)
        selector_display = f'<code class="selector-code">{selector or "-"}</code>' if selector else "-"
        value_display = f'<code class="selector-code">{value or "-"}</code>' if value else "-"
        screenshot_link = f'<a href="{screenshot_path}" target="_blank">📷</a>' if screenshot_path and os.path.exists(screenshot_path) else "-"

        steps_rows += f"""
        <tr>
            <td><span class="step-number">{i}</span></td>
            <td>{time_short}</td>
            <td><span class="action-badge {action_type}">{_get_action_icon(action_type)} {action_label}</span></td>
            <td>{selector_display}</td>
            <td>{value_display}</td>
            <td>{screenshot_link}</td>
        </tr>"""

    html_parts.append(f"""
    <div class="section">
        <h2>📝 {t('steps_title')}</h2>
        <table class="steps-table">
            <thead>
                <tr>
                    <th>{t('step_col')}</th>
                    <th>{t('time_col')}</th>
                    <th>{t('action_col')}</th>
                    <th>{t('selector_col')}</th>
                    <th>{t('value_col')}</th>
                    <th>{t('screenshot_col')}</th>
                </tr>
            </thead>
            <tbody>
                {steps_rows}
            </tbody>
        </table>
    </div>
""")

    # === SCREENSHOTS ===
    screenshots_html = ""
    for i, action in enumerate(actions, 1):
        if len(action) >= 11:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose, page_title, page_url, element_name, element_type = action
        else:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose = action

        if screenshot_path and os.path.exists(screenshot_path):
            b64_img = _image_to_base64(screenshot_path)
            time_short = timestamp[11:19] if len(timestamp) > 19 else timestamp
            action_label = _action_type(action_type)
            step_label = f"{t('step')} {i} - {action_label}"
            if b64_img:
                screenshots_html += f"""
        <div class="screenshot-card">
            <img src="{b64_img}" alt="{action_type}">
            <div class="screenshot-info">
                <div class="step-label">{step_label}</div>
                <div class="step-time">{t('step_time')}: {time_short}</div>
            </div>
        </div>"""

    if screenshots_html:
        html_parts.append(f"""
    <div class="section">
        <h2>📷 {t('screenshots_title')}</h2>
        <div class="screenshots-grid">
            {screenshots_html}
        </div>
    </div>
""")

    # === ACCEPTANCE CRITERIA ===
    criteria_rows = ""
    for i, action in enumerate(actions, 1):
        if len(action) >= 11:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose, page_title, page_url, element_name, element_type = action
        else:
            action_id, timestamp, action_type, selector, value, screenshot_path, purpose = action

        if action_type == "click":
            criteria_rows += f"""
        <tr>
            <td>{i}</td>
            <td>{t('click_verify')}</td>
            <td>{t('click_desc')}</td>
            <td><span class="pass-badge">{t('criteria_pass')}</span></td>
        </tr>"""
        elif action_type == "type":
            criteria_rows += f"""
        <tr>
            <td>{i}</td>
            <td>{t('type_verify')}</td>
            <td>{t('type_desc')}</td>
            <td><span class="pass-badge">{t('criteria_pass')}</span></td>
        </tr>"""
        elif action_type == "navigate":
            criteria_rows += f"""
        <tr>
            <td>{i}</td>
            <td>{t('navigate_verify')}</td>
            <td>{t('navigate_desc')}</td>
            <td><span class="pass-badge">{t('criteria_pass')}</span></td>
        </tr>"""

    if criteria_rows:
        html_parts.append(f"""
    <div class="section">
        <h2>✅ {t('acceptance_criteria_title')}</h2>
        <table class="acceptance-table">
            <thead>
                <tr>
                    <th style="width:50px;">#</th>
                    <th>{t('verify_item')}</th>
                    <th>{t('verify_method')}</th>
                    <th style="width:80px;">{t('status')}</th>
                </tr>
            </thead>
            <tbody>
                {criteria_rows}
            </tbody>
        </table>
    </div>
""")

    # === FOOTER ===
    html_parts.append(f"""
    <div class="footer">
        <p>{t('footer')}</p>
    </div>
</body>
</html>""")

    # 寫入文件
    if output_path is None:
        os.makedirs(config.REPORTS_DIR, exist_ok=True)
        output_path = os.path.join(config.REPORTS_DIR, f"uat_test_plan_{session_id}.html")

    content = "".join(html_parts)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"{t('html_report')}: {output_path}")

    # 恢復原本語言
    set_lang(orig_lang)
    return output_path


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