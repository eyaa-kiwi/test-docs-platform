"""
Recorder Module - 錄製所有用戶操作
支援兩種模式：
  1. 腳本模式：從 JSON 載入測試步驟自動執行
  2. 互動模式：打開瀏覽器，自動監聽並記錄用戶操作

互動模式功能：
  - Dimensions 錄製區域尺寸選擇
  - 停止錄製按鈕（注入頁面右下角浮動按鈕）
  - 啟動時記錄所有交互事件（click、input、scroll、keydown、navigation）
  - 每個 Action 強制截圖
  - 增強識別 ASP.NET 傳統表單元件 (type="image", name 屬性等)
"""
import asyncio
import json
import os
import base64
from datetime import datetime
from typing import Optional, List, Dict
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from core import db_manager
import config
from i18n import t

# stop_recording_styles
_STOP_BUTTON_STYLES = """
position: fixed;
bottom: 20px;
right: 20px;
z-index: 2147483647;
display: flex;
align-items: center;
gap: 8px;
padding: 12px 20px;
background: linear-gradient(135deg, #ff416c, #ff4b2b);
color: #fff;
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
font-size: 15px;
font-weight: 600;
border: none;
border-radius: 28px;
cursor: pointer;
box-shadow: 0 4px 16px rgba(255, 65, 108, 0.45);
transition: transform 0.15s, box-shadow 0.15s;
user-select: none;
pointer-events: auto;
"""

_STOP_BUTTON_HOVER_STYLES = """
transform: scale(1.06);
box-shadow: 0 6px 24px rgba(255, 65, 108, 0.6);
"""

_STOP_BUTTON_HTML = """
<div id="__tdp_stop_btn__" style="{styles}">
  <svg width="18" height="18" viewBox="0 0 24 24" fill="white" style="flex-shrink:0;">
    <rect x="4" y="4" width="16" height="16" rx="3" fill="white"/>
  </svg>
  <span>停止錄製</span>
</div>
"""


class TestRecorder:
    """測試錄製器"""

    def __init__(self, session_name: str = "測試會話"):
        self.session_name = session_name
        self.session_id: Optional[int] = None
        self.screenshot_count = 0
        self._stop_requested = False  # 停止請求標誌
        self._recorded_events: List[Dict] = []  # 記錄所有交互事件（記憶體緩衝）
        os.makedirs(config.SCREENSHOTS_DIR, exist_ok=True)

    async def start(
        self,
        url: str,
        headless: bool = True,
        interactive: bool = False,
        viewport_width: int = None,
        viewport_height: int = None,
    ):
        """
        開始錄製

        Args:
            url: 目標網址
            headless: 是否使用無頭模式
            interactive: 是否為互動模式（等待用戶操作）
            viewport_width: 錄製區域寬度（預設 1280）
            viewport_height: 錄製區域高度（預設 720）
        """
        self.interactive = interactive

        vp_width = viewport_width or config.VIEWPORT_WIDTH
        vp_height = viewport_height or config.VIEWPORT_HEIGHT

        print(f"\n🖥️  錄製尺寸: {vp_width} x {vp_height}")

        self.playwright = await async_playwright().start()
        # 使用本機已安裝的 Chrome 瀏覽器（因網路限制無法從 CDN 下載）
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            channel="chrome",
            executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            args=["--ignore-certificate-errors", "--disable-web-security"],
        )

        # 建立錄影目錄
        self.video_dir = os.path.join(config.STORAGE_DIR, "videos")
        os.makedirs(self.video_dir, exist_ok=True)

        self.context = await self.browser.new_context(
            viewport={"width": vp_width, "height": vp_height},
            record_video_dir=self.video_dir,
            record_video_size={"width": vp_width, "height": vp_height},
        )

        self.page = await self.context.new_page()

        # 創建 session
        self.session_id = db_manager.create_session(self.session_name, url)

        # 如果是互動模式，先暴露停止函數（必須在導航前，這樣函數會在所有頁面生效）
        if interactive:
            await self.page.expose_function("__tdp_request_stop__", self._handle_stop_from_js)

        # 導航到目標 URL（使用 domcontentloaded 避免某些頁面一直 network polling）
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        print(f"✅ 已導航至：{url}")

        # 如果是互動模式，在導航完成後設置事件監聽器和停止按鈕
        if interactive:
            await self._setup_interactive_listeners()
            await self._inject_stop_button()
            # 每次導航後重新注入
            self.page.on("framenavigated", lambda frame: asyncio.ensure_future(
                self._on_frame_navigated(frame)
            ))

        # 啟動時記錄初始頁面狀態（強制截圖）
        await self._record_initial_state()

        return self.page

    async def _record_initial_state(self):
        """啟動時記錄初始頁面狀態"""
        try:
            page_title = await self.page.title()
            current_url = self.page.url
            print(f"\n📄 初始頁面: \"{page_title}\"")
            print(f"   URL: {current_url}")
            # 強制截圖記錄初始狀態
            await self.record_action("navigate", current_url, purpose=t('purpose_initial_page').format(title=page_title))
        except Exception as e:
            print(f"  ⚠️ 記錄初始狀態時出錯: {e}")

    async def _setup_interactive_listeners(self):
        """
        互動模式：監聽瀏覽器事件並自動記錄所有交互
        監聽事件：click, input, scroll, keydown, navigation
        """
        page = self.page

        async def on_navigation(frame):
            """監聽頁面導航"""
            if frame == page.main_frame:
                new_url = frame.url
                old_url = getattr(self, "_last_url", "")
                if new_url != old_url:
                    timestamp = datetime.now().isoformat()
                    event_data = {
                        "timestamp": timestamp,
                        "event": "navigate",
                        "from": old_url,
                        "to": new_url,
                    }
                    self._recorded_events.append(event_data)
                    await self.record_action("navigate", new_url, purpose=t('purpose_navigate'))
                    self._last_url = new_url

        # Playwright 原生事件
        page.on("framenavigated", on_navigation)

        # 在頁面中注入 JavaScript 來捕獲事件
        await self._inject_js_listeners()

        # 用 polling 方式取得 JavaScript 端收集的事件
        self._stop_polling = False
        self._poll_task = asyncio.ensure_future(self._poll_js_events())

        print("🔍 互動錄製模式已啟動 — 所有交互事件將自動記錄")
        print("   監聽事件：click, input, scroll, keydown, navigation")
        print("   點擊右下角「停止錄製」按鈕或按 Esc 鍵結束錄製\n")

    async def _inject_js_listeners(self):
        """在頁面中注入 JavaScript 事件監聽器（導航後需重新注入）"""
        await self.page.evaluate("""() => {
            // 避免重複注入
            if (window.__tdp_listeners_injected__) return;
            window.__tdp_listeners_injected__ = true;

            // 輔助函數：獲取元素標籤名稱/欄位名稱
            function getElementLabel(el) {
                const tag = el.tagName.toLowerCase();
                
                let name = el.getAttribute('aria-label') || 
                           el.getAttribute('title') || 
                           el.getAttribute('placeholder') || 
                           el.getAttribute('alt');
                           
                if (!name && (tag === 'input' && ['button', 'submit', 'reset'].includes(el.type))) {
                    name = el.getAttribute('value');
                }
                
                if (!name) name = el.getAttribute('name') || '';

                if (!name && (tag === 'input' || tag === 'textarea' || tag === 'select')) {
                    const id = el.id;
                    if (id) {
                        const labelEl = document.querySelector('label[for="' + CSS.escape(id) + '"]');
                        if (labelEl) name = labelEl.textContent.trim();
                    }
                    if (!name) {
                        const parentLabel = el.closest('label');
                        if (parentLabel) name = parentLabel.textContent.trim();
                    }
                }

                if (!name && (tag === 'button' || el.getAttribute('role') === 'button')) {
                    name = (el.textContent || '').trim().slice(0, 80);
                }
                if (!name && tag === 'a') {
                    name = (el.textContent || '').trim().slice(0, 80);
                }

                return name || '';
            }

            function getElementType(el) {
                const tag = el.tagName.toLowerCase();
                if (tag === 'input') return el.type || 'text';
                if (tag === 'button' || el.getAttribute('role') === 'button') return 'button';
                if (tag === 'a') return 'link';
                if (tag === 'select') return 'select';
                if (tag === 'textarea') return 'textarea';
                return tag;
            }

            function extractElementData(el) {
                return {
                    tag: el.tagName.toLowerCase(),
                    id: el.id || '',
                    name: el.name || el.getAttribute('name') || '',
                    alt: el.getAttribute('alt') || '',
                    inputType: el.type || '',
                    classList: Array.from(el.classList).join('.'),
                    text: (el.textContent || '').trim().slice(0, 80),
                    element_name: getElementLabel(el),
                    element_type: getElementType(el)
                };
            }

            // 點擊監聽（排除停止按鈕）
            document.addEventListener('click', (e) => {
                const el = e.target;
                if (el.closest && el.closest('#__tdp_stop_btn__')) return;
                window.__tdp_last_click__ = JSON.stringify(extractElementData(el));
            }, true);

            // 輸入監聽
            window.__tdp_input_counter__ = window.__tdp_input_counter__ || 0;
            document.addEventListener('input', (e) => {
                const el = e.target;
                if (['input', 'textarea', 'select'].includes(el.tagName.toLowerCase())) {
                    window.__tdp_input_counter__++;
                    const data = extractElementData(el);
                    data.value = el.value || '';
                    data.counter = window.__tdp_input_counter__;
                    data.ts = Date.now();
                    window.__tdp_last_input__ = JSON.stringify(data);
                }
            }, true);

            // 鍵盤監聽
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    window.__tdp_esc_pressed__ = true;
                    if (window.__tdp_request_stop__) window.__tdp_request_stop__();
                }
            }, true);

            // 滾動監聽
            let scrollTimer = null;
            window.__tdp_last_scroll__ = window.__tdp_last_scroll__ || 0;
            document.addEventListener('scroll', () => {
                if (scrollTimer) clearTimeout(scrollTimer);
                scrollTimer = setTimeout(() => {
                    window.__tdp_last_scroll__ = window.scrollY;
                }, 300);
            }, {passive: true});
        }""")

    async def _poll_js_events(self):
        """定期從頁面 JavaScript 獲取事件"""
        last_click = ""
        last_input_counter = 0
        last_scroll = 0

        while not self._stop_polling:
            # ============ 優先檢查停止信號（獨立 try/except 確保不被跳過） ============
            try:
                stop_clicked = await self.page.evaluate(
                    "() => window.__tdp_stop_clicked__ || false"
                )
                if stop_clicked:
                    print("\n⏹️  停止按鈕被點擊，停止錄製...")
                    self._stop_requested = True
                    break

                esc_pressed = await self.page.evaluate("() => window.__tdp_esc_pressed__ || false")
                if esc_pressed:
                    print("\n⏹️  偵測到 Esc 鍵，停止錄製...")
                    self._stop_requested = True
                    break
            except Exception:
                pass

            try:
                # ============ 處理點擊事件 ============
                click_data = await self.page.evaluate("() => window.__tdp_last_click__ || ''")
                if click_data and click_data != last_click:
                    last_click = click_data
                    try:
                        info = json.loads(click_data)
                        selector = ""
                        if info.get("id"):
                            selector = f"#{info['id']}"
                        elif info.get("name"): # 優先使用 name 選擇器
                            selector = f"input[name='{info['name']}']"
                        elif info.get("text"):
                            selector = f"text={info['text']}"
                        elif info.get("classList"):
                            selector = f"{info['tag']}.{info['classList']}"
                        else:
                            selector = info.get("tag", "unknown")
                            
                        timestamp = datetime.now().isoformat()
                        self._recorded_events.append({
                            "timestamp": timestamp,
                            "event": "click",
                            "selector": selector,
                            **info,
                        })
                        
                        # 生成更精確的點擊描述
                        display_name = info.get('element_name') or info.get('alt') or info.get('name') or info.get('text') or selector
                        detail_desc = t('purpose_click').format(name=display_name)
                        if info.get('name') and info.get('name') != display_name:
                            detail_desc += t('purpose_click_field').format(name=info['name'])
                        if info.get('inputType') == 'image':
                            detail_desc += t('purpose_click_image_btn')

                        element_info = {
                            "element_name": info.get("element_name", ""),
                            "element_type": info.get("element_type", ""),
                        }
                        element_id = info.get("id", "") or ""
                        
                        await self.record_action("click", selector, purpose=detail_desc, element_info=element_info, element_id=element_id)
                    except Exception:
                        pass

                # ============ 處理輸入事件 ============
                input_data = await self.page.evaluate("() => window.__tdp_last_input__ || ''")
                if input_data:
                    try:
                        info = json.loads(input_data)
                        counter = info.get("counter", 0)
                        if counter > last_input_counter:
                            last_input_counter = counter
                            selector = ""
                            if info.get("id"):
                                selector = f"#{info['id']}"
                            elif info.get("name"): # 優先使用 name 選擇器
                                selector = f"input[name='{info['name']}']"
                            elif info.get("classList"):
                                selector = f"{info['tag']}.{info['classList']}"
                            else:
                                selector = info.get("tag", "unknown")
                                
                            value = info.get("value", "")
                            timestamp = datetime.now().isoformat()
                            self._recorded_events.append({
                                "timestamp": timestamp,
                                "event": "input",
                                "selector": selector,
                                "value": value,
                                **info,
                            })
                            
                            if value:
                                # 生成更精確的輸入描述
                                display_name = info.get("element_name") or info.get("name") or selector
                                detail_desc = t('purpose_input').format(name=display_name, value=value)
                                
                                element_info = {
                                    "element_name": info.get("element_name", ""),
                                    "element_type": info.get("element_type", ""),
                                }
                                element_id = info.get("id", "") or ""
                        await self.record_action("type", selector, value, purpose=detail_desc, element_info=element_info, element_id=element_id)
                    except Exception:
                        pass

                # ============ 檢查滾動事件 ============
                scroll_data = await self.page.evaluate("() => window.__tdp_last_scroll__ || 0")
                if scroll_data and abs(scroll_data - last_scroll) > 150:
                    last_scroll = scroll_data
                    timestamp = datetime.now().isoformat()
                    self._recorded_events.append({
                        "timestamp": timestamp,
                        "event": "scroll",
                        "scrollY": scroll_data,
                    })
                    await self.record_action("scroll", purpose=t('purpose_scroll').format(value=scroll_data))

            except Exception:
                pass

            await asyncio.sleep(0.5)

    async def _inject_stop_button(self):
        """在頁面右下角注入停止錄製按鈕（使用 Shadow DOM 隔離，避免被網站 JS 攔截）"""
        await self.page.evaluate("""() => {
            // 移除舊的停止按鈕（如果存在）
            const old = document.getElementById('__tdp_stop_host__');
            if (old) old.remove();

            // 創建宿主元素
            const host = document.createElement('div');
            host.id = '__tdp_stop_host__';
            host.style.cssText = 'position:fixed; bottom:20px; right:20px; z-index:2147483647; pointer-events:auto;';
            document.documentElement.appendChild(host);

            // 使用 Shadow DOM 完全隔離
            const shadow = host.attachShadow({ mode: 'closed' });

            // 注入樣式和按鈕
            shadow.innerHTML = `
                <style>
                    #tdp-stop-btn {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        padding: 12px 20px;
                        background: linear-gradient(135deg, #ff416c, #ff4b2b);
                        color: #fff;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        font-size: 15px;
                        font-weight: 600;
                        border: none;
                        border-radius: 28px;
                        cursor: pointer;
                        box-shadow: 0 4px 16px rgba(255, 65, 108, 0.45);
                        transition: transform 0.15s, box-shadow 0.15s;
                        user-select: none;
                        pointer-events: auto;
                    }
                    #tdp-stop-btn:hover {
                        transform: scale(1.06);
                        box-shadow: 0 6px 24px rgba(255, 65, 108, 0.6);
                    }
                    #tdp-stop-btn:active {
                        transform: scale(0.96);
                    }
                    #tdp-stop-btn.stopping {
                        pointer-events: none;
                        opacity: 0.5;
                    }
                </style>
                <div id="tdp-stop-btn">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="white" style="flex-shrink:0;">
                        <rect x="4" y="4" width="16" height="16" rx="3" fill="white"/>
                    </svg>
                    <span>停止錄製</span>
                </div>
            `;

            const btn = shadow.getElementById('tdp-stop-btn');
            btn.addEventListener('pointerdown', (e) => {
                e.stopPropagation();
                e.preventDefault();
                btn.classList.add('stopping');
                btn.querySelector('span').textContent = '停止中...';
                window.__tdp_stop_clicked__ = true;
                if (window.__tdp_request_stop__) {
                    window.__tdp_request_stop__();
                }
            });
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                window.__tdp_stop_clicked__ = true;
                if (window.__tdp_request_stop__) {
                    window.__tdp_request_stop__();
                }
            });
        }""")

        print("🔴 停止錄製按鈕已注入（頁面右下角）")

    async def _get_clickable_selector(self, element) -> Optional[str]:
        """嘗試生成一個可識別的元素選擇器 (Playwright 原生備用)"""
        try:
            tag = await element.evaluate("el => el.tagName.toLowerCase()")
            text = await element.evaluate("el => el.textContent?.trim() || ''")
            _id = await element.evaluate("el => el.id || ''")
            classes = await element.evaluate(
                "el => Array.from(el.classList).join('.') || ''"
            )

            if _id:
                return f"#{_id}"
            if text and len(text) < 50:
                return f'text={text.strip()}'
            if classes:
                return f"{tag}.{classes}"
            return tag
        except Exception:
            return None

    def _on_console_message(self, msg):
        """監聽 console 訊息，用於可靠的停止偵測"""
        if msg.text == "__TDP_STOP__":
            self._stop_requested = True

    def _handle_stop_from_js(self):
        """從 JS expose_function 回調，直接設定停止標誌"""
        print("\n⏹️  停止按鈕被點擊，停止錄製...")
        self._stop_requested = True

    async def _on_frame_navigated(self, frame):
        """頁面導航後重新注入停止按鈕和事件監聽器"""
        if frame == self.page.main_frame:
            try:
                await asyncio.sleep(1)  # 等待頁面載入
                await self._inject_js_listeners()
                await self._inject_stop_button()
            except Exception:
                pass

    async def _get_page_info(self) -> tuple:
        """獲取當前頁面標題和 URL"""
        try:
            page_title = await self.page.title()
            page_url = self.page.url
            return page_title, page_url
        except Exception:
            return "", ""

    async def _get_element_label_info(self, element) -> dict:
        """從 DOM 元素提取標籤/名稱資訊 (保留作備用)"""
        try:
            info = await element.evaluate("""el => {
                const tag = el.tagName.toLowerCase();
                let elementType = tag;
                if (tag === 'input') elementType = el.type || 'text';
                else if (tag === 'button' || el.getAttribute('role') === 'button') elementType = 'button';
                else if (tag === 'a') elementType = 'link';
                else if (tag === 'select') elementType = 'select';
                else if (tag === 'textarea') elementType = 'textarea';

                let elementName = el.getAttribute('aria-label') || el.getAttribute('name') ||
                                  el.getAttribute('title') || el.getAttribute('placeholder') || 
                                  el.getAttribute('alt') || '';

                if (!elementName && (tag === 'input' || tag === 'textarea' || tag === 'select')) {
                    const id = el.id;
                    if (id) {
                        const label = document.querySelector(`label[for="${id}"]`);
                        if (label) elementName = label.textContent.trim();
                    }
                    if (!elementName) {
                        const parentLabel = el.closest('label');
                        if (parentLabel) elementName = parentLabel.textContent.trim();
                    }
                }

                if (!elementName && tag === 'button') elementName = (el.textContent || '').trim().slice(0, 80);
                if (!elementName && tag === 'a') elementName = (el.textContent || '').trim().slice(0, 80);

                return {
                    element_name: elementName || '',
                    element_type: elementType || tag,
                };
            }""")
            return info
        except Exception:
            return {"element_name": "", "element_type": ""}

    async def record_action(
        self,
        action_type: str,
        selector: str = None,
        value: str = None,
        purpose: str = None,
        force_screenshot: bool = True,
        element_info: dict = None,
        element_id: str = None,
    ):
        """記錄操作（強制截圖）"""
        # 每個 Action 強制截圖
        screenshot_path = None
        if force_screenshot:
            screenshot_path = await self._take_screenshot()

        # 獲取當前頁面資訊
        page_title, page_url = await self._get_page_info()

        # 提取元素資訊
        element_name = ""
        element_type = ""
        if element_info:
            element_name = element_info.get("element_name", "")
            element_type = element_info.get("element_type", "")

        db_manager.record_action(
            session_id=self.session_id,
            action_type=action_type,
            selector=selector,
            value=value,
            screenshot_path=screenshot_path,
            purpose=purpose,
            page_title=page_title,
            page_url=page_url,
            element_name=element_name,
            element_type=element_type,
            element_id=element_id,
        )
        timestamp = datetime.now().strftime("%H:%M:%S")
        action_zh = self._action_type_to_zh(action_type)
        selector_text = f" on {selector}" if selector else ""
        elem_text = f" [{element_name}]" if element_name else ""
        
        # 如果已經有精確的 purpose 描述，可以選擇優先列印 purpose
        display_msg = purpose if purpose else f"{action_zh}{selector_text}{elem_text}"
        print(f"  [{timestamp}] 📝 {display_msg}")

    def _action_type_to_zh(self, action_type: str) -> str:
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

    async def _take_screenshot(self) -> str:
        """截取屏幕"""
        self.screenshot_count += 1
        filename = f"action_{self.session_id}_{self.screenshot_count}.png"
        filepath = os.path.join(config.SCREENSHOTS_DIR, filename)

        await self.page.screenshot(path=filepath, full_page=False)
        return filepath

    # ============ 腳本模式：手動操作 API ============

    async def click(self, selector: str):
        """點擊元素（強制截圖）"""
        try:
            await self.page.wait_for_selector(selector, timeout=5000)
            await self.page.click(selector)
            await self.record_action("click", selector)
        except Exception as e:
            print(f"  ⚠️ 點擊失敗 {selector}: {e}")

    async def fill(self, selector: str, value: str):
        """填寫輸入框（先清除再輸入，強制截圖）"""
        try:
            await self.page.wait_for_selector(selector, timeout=5000)
            await self.page.fill(selector, value)
            await self.record_action("type", selector, value)
        except Exception as e:
            print(f"  ⚠️ 輸入失敗 {selector}: {e}")

    async def select(self, selector: str, value: str):
        """選擇下拉選單"""
        try:
            await self.page.wait_for_selector(selector, timeout=5000)
            await self.page.select_option(selector, value)
            await self.record_action("select", selector, value)
        except Exception as e:
            print(f"  ⚠️ 選擇失敗 {selector}: {e}")

    async def wait(self, milliseconds: int = 1000, purpose: str = None):
        """等待一段時間"""
        await asyncio.sleep(milliseconds / 1000)
        purpose_text = purpose or f"等待 {milliseconds}ms"
        await self.record_action("wait", purpose=purpose_text)

    async def screenshot(self, purpose: str = "手動截圖"):
        """手動截圖"""
        await self.record_action("screenshot", purpose=purpose)

    async def navigate(self, url: str):
        """導航到新 URL"""
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await self.record_action("navigate", url)

    async def assert_text(self, selector: str, expected: str):
        """斷言元素文本"""
        try:
            await self.page.wait_for_selector(selector, timeout=5000)
            text = await self.page.text_content(selector)
            passed = expected in (text or "")
            status = "✅" if passed else "❌"
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] {status} 斷言: "
                  f"{selector} 包含 '{expected}' (實際: '{text}')")
            await self.record_action("assert", selector, expected)
        except Exception as e:
            print(f"  ⚠️ 斷言失敗 {selector}: {e}")

    # ============ 腳本執行器 ============

    async def run_script(self, script_path: str):
        """
        從 JSON 腳本檔案載入並執行測試步驟
        腳本格式請參考 scripts/ 目錄下的範例
        """
        with open(script_path, "r", encoding="utf-8") as f:
            script = json.load(f)

        print(f"\n📋 載入測試腳本：{script.get('name', script_path)}")
        print(f"   描述：{script.get('description', '')}")
        print(f"   步驟數：{len(script.get('steps', []))}\n")

        steps = script.get("steps", [])
        for i, step in enumerate(steps, 1):
            action = step.get("action", "")
            selector = step.get("selector", "")
            value = step.get("value", "")
            purpose = step.get("purpose", "")

            print(f"  步驟 {i}/{len(steps)}: {purpose or action}")

            if action == "navigate":
                await self.navigate(step["url"])
            elif action == "click":
                await self.click(selector)
            elif action == "fill":
                await self.fill(selector, value)
            elif action == "type":
                await self.fill(selector, value)
            elif action == "select":
                await self.select(selector, value)
            elif action == "wait":
                await self.wait(int(value) if value else 1000, purpose)
            elif action == "screenshot":
                await self.screenshot(purpose)
            elif action == "assert_text":
                await self.assert_text(selector, value)
            else:
                print(f"  ⚠️ 未知操作: {action}")

        print(f"\n✅ 測試腳本執行完成\n")

    @property
    def is_stop_requested(self) -> bool:
        """檢查是否已請求停止"""
        return self._stop_requested

    def get_recorded_events(self) -> List[Dict]:
        """獲取所有記錄的事件"""
        return list(self._recorded_events)

    async def _save_video(self) -> str:
        """儲存 Playwright 錄製的影片，回傳影片檔案路徑或空字串"""
        try:
            # 先取得 video 原始路徑（在 context close 之前）
            original_video_path = None
            if self.context.video:
                try:
                    original_video_path = await self.context.video.path()
                except Exception:
                    pass

            # 關閉 context（這會 flush video 到磁碟）
            try:
                await self.context.close()
            except Exception:
                pass

            await asyncio.sleep(0.5)  # 等待 flush 完成

            if original_video_path and os.path.exists(original_video_path):
                ext = os.path.splitext(original_video_path)[1] or ".webm"
                dest_filename = f"session_{self.session_id}{ext}"
                dest_path = os.path.join(self.video_dir, dest_filename)

                import shutil
                try:
                    shutil.copy2(original_video_path, dest_path)
                    print(f"  🎬 影片已保存: {dest_path}")
                    return dest_path
                except Exception as e:
                    print(f"  ⚠️ 複製影片失敗: {e}")
                    return original_video_path

            return ""
        except Exception as e:
            print(f"  ⚠️ 儲存影片時出錯: {e}")
            return ""

    async def stop(self):
        """停止錄製"""
        # 停止 polling
        self._stop_polling = True

        # 記錄結束前的完整事件清單
        print(f"\n📊 總共記錄 {len(self._recorded_events)} 個交互事件")
        print(f"   截圖數量: {self.screenshot_count}")

        # 儲存影片（在關閉 context/browser 前）
        video_path = ""
        if hasattr(self, 'context') and self.context:
            video_path = await self._save_video()
            if video_path:
                db_manager.update_session_video(self.session_id, video_path)

        db_manager.end_session(self.session_id)

        # 關閉瀏覽器
        try:
            await self.browser.close()
        except Exception:
            pass

        try:
            await self.playwright.stop()
        except Exception:
            pass

        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{dt}] 錄製結束 - Session ID: {self.session_id}")
