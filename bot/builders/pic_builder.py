from __future__ import annotations
import io
import asyncio
from typing import Optional
from PIL import Image
from playwright.async_api import Browser,BrowserContext, PlaywrightContextManager, Page, async_playwright, TimeoutError, Error

from ..utils.config import get_config_value
from ..utils.pic_process import join_pic

class DynamicRemovedException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

def cookie_to_dict_list(cookie: str, domain: str):
    if not cookie:
        return []
    cookie_list = cookie.split(";")
    cookies = []
    for c in cookie_list:
        if not c:
            continue
        cookie_pair = c.lstrip().rstrip().split("=")
        cookies.append({
            "name": cookie_pair[0],
            "value": cookie_pair[1],
            "domain": domain,
            "path": "/"
        })
    return cookies

class PicBuilder:

    DEFAULT_MOBILE_UA = 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
    DEFAULT_PC_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'

    def __init__(self) -> None:
        self._playwright_context: Optional[PlaywrightContextManager] = None
        self._browser: Optional[Browser] = None
    
    async def get_browser(self) -> Browser:
        if(self._playwright_context is None):
            self._playwright_context = await async_playwright().start()
        if(self._browser is None):
            self._browser = await self._playwright_context.chromium.launch()
        elif(self._browser.is_connected() == False):
            await self._browser.close()
            self._browser = await self._playwright_context.chromium.launch()
        return self._browser

    async def close_browser(self) -> None:
        if(not self._browser is None):
            await self._browser.close()
            self._browser = None
        if(not self._playwright_context is None):
            await self._playwright_context.stop()
            self._playwright_context = None

    async def restart_browser(self) -> Browser:
        await self.close_browser()
        return await self.get_browser()

    async def get_wb_pic(self, wb_id: str, created_time: str = None, cookie: str = None, ua: str = None) -> bytes:
        browser = await self.get_browser()
        if ua is None:
            ua = self.DEFAULT_MOBILE_UA
        context = await browser.new_context(user_agent=ua, device_scale_factor=2)
        await context.add_cookies(cookie_to_dict_list(cookie, ".weibo.cn"))
        page = await context.new_page()
        try:
            page.set_default_timeout(10000)
            await page.set_viewport_size({'width':1300, 'height':3500})
            await page.goto('https://m.weibo.cn/detail/'+wb_id, wait_until="networkidle", timeout=15000)
            if not created_time is None:
                try:
                    await page.evaluate("""
        var elements = document.getElementsByClassName("time");
        for(i=0;i<elements.length;i++) {
            if(elements[i].tagName == "SPAN") {
                elements[i].textContent = """ + f'"{created_time}"' + """;
                break;
            }
        }
                    """)
                except:
                    pass
            try:
                await page.evaluate("""
    var className = "main";
    var divs = document.getElementsByClassName(className);
    var elements = new Array()
    for(i=0;i<divs.length;i++) {
        elements.push(divs[i])
    }

    for(i=0;i<elements.length;i++) {
        var element = elements[i];
        elementClassName = element.className
        var fsStr = getComputedStyle(element).fontSize;
        var heightStr = getComputedStyle(element).height;
        var fs = parseInt((fsStr).substring(0, fsStr.length-2))
        var height = parseInt((heightStr).substring(0, heightStr.length-2))
        var hasDiv = false
        var isSpan = element.tagName == "SPAN"
        var isA = element.tagName == "A"
        var isBtn = element.tagName == "BUTTON"
        var isFooter = element.tagName == "FOOTER"
        var divnum = 0
        if(isBtn || element.className.includes('-container') || isFooter) {
            continue
        }
        for(j=0;j<element.children.length;j++) {
            elements.push(element.children[j])
            if(element.children[j].tagName == "DIV") {
                hasDiv = true
                divnum += 1
            }
        }
        if(isNaN(fs) || isSpan) {
            continue
        }
        if(hasDiv || isA) {
            continue
        }
        element.style.fontFamily = "'Microsoft YaHei', 'Noto Color Emoji', 'Unifont', 'sans-serif'"
        if(element.className == "weibo-text") {
            element.style.fontSize = parseInt(document.defaultView.getComputedStyle(element, null).fontSize)+3 + 'px'
        }
    }
                """)
            except:
                pass
            try: # 图片大小
                await page.evaluate('document.getElementsByClassName("m-auto-list")[0].style.maxWidth = "100%"')
            except:
                pass
            try: # 顶栏
                await page.evaluate('document.getElementsByClassName("lite-topbar")[0].style.display = "none"')
            except:
                pass
            # await page.wait_for_timeout(600000)
            upper_pic = await page.locator('[class="card-wrap"]').first.screenshot()
            lower_pic = await page.locator('[class="weibo-main"]').screenshot()
        except Exception as e:
            try:
                page.screenshot(full_page=True, path="wb_error_record.png")
            except:
                pass
            raise e
        finally:
            await page.close()
            await context.close()
        pic = join_pic(upper_pic, lower_pic)
        # debug
        # debug_save_pic(pic, "weibo", wb_id)
        return pic

    async def font_replace_js(self, page: Page, class_name: str, font_list: list[str] = ['Microsoft YaHei', 'Noto Color Emoji', 'Unifont', 'sans-serif']):
        await page.evaluate("""
var className = \""""+ class_name +"""\"; // 指定从哪个元素开始匹配
var divs = document.getElementsByClassName(className);
var elements = new Array()
for(i=0;i<divs.length;i++) {
    elements.push(divs[i])
}

for(i=0;i<elements.length;i++) {
    var element = elements[i];
    elementClassName = element.className
    var fsStr = getComputedStyle(element).fontSize;
    var heightStr = getComputedStyle(element).height;
    var fs = parseInt((fsStr).substring(0, fsStr.length-2))
    var height = parseInt((heightStr).substring(0, heightStr.length-2))
    var hasDiv = false
    var isSpan = element.tagName == "SPAN"
    var isA = element.tagName == "A"
    var isBtn = element.tagName == "BUTTON"
    if(isBtn) {
        continue
    }
    for(j=0;j<element.children.length;j++) {
        elements.push(element.children[j])
    }
    if(element.children.length == 0) {
        element.style.fontFamily = '"""+ ", ".join(font_list) +"""'
    }
}
            """)
    
    async def text_resize_js(self, page: Page, class_name: str):
        await page.evaluate("""
var className = \""""+ class_name +"""\"; // 指定从哪个元素开始匹配
var divs = document.getElementsByClassName(className);
var elements = new Array()
for(i=0;i<divs.length;i++) {
    elements.push(divs[i])
}

for(i=0;i<elements.length;i++) {
    var element = elements[i];
    elementClassName = element.className
    var fsStr = getComputedStyle(element).fontSize;
    var heightStr = getComputedStyle(element).height;
    var fs = parseInt((fsStr).substring(0, fsStr.length-2))
    var height = parseInt((heightStr).substring(0, heightStr.length-2))
    var hasDiv = false
    var isSpan = element.tagName == "SPAN"
    var isA = element.tagName == "A"
    var isBtn = element.tagName == "BUTTON"
    if(isBtn) {
        if(element.className == "dyn-reserve__card__btn") {
            element.style.height = 'auto'
            element.style.minWidth = '14.93333vmin'
            element.style.fontSize = '3vmin'
            element.children[0].style.width = 'auto'
            element.children[0].style.height = 'auto'
        }
        continue
    }
    for(j=0;j<element.children.length;j++) {
        elements.push(element.children[j])
    }
    if(element.children.length == 0) {
        element.style.fontSize = '4vmin'
        element.style.lineHeight = '5.9vmin'
        element.style.height = 'auto'
    }
    if(element.className == "bili-dyn-topic__icon" || element.className == "bili-rich-text-emoji") {
        element.style.height = '4vmin'
        element.style.width = '4vmin'
    }
    if(element.className == "opus-module-topic__icon") {
        element.style.height = ''
    }
    if(element.className == "dyn-music__card") {
        element.style.height = "auto"
    }
    if(element.className == "dyn-music__card__left") {
        element.style.flexBasis = "5vmax"
    }
}
            """)

    async def bili_dyn_opus_process(self, page: Page, created_time: str = None):
        try: # 底部开启APP提示框
            await page.evaluate('document.getElementsByClassName("openapp-dialog")[0].style.display = "none"')
        except:
            pass
        await page.evaluate('document.getElementsByClassName("m-float-openapp")[0].style.display = "none"') # 开启APP浮动按钮
        if await page.locator('[class="opus-read-more"]').is_visible():
            # await page.locator('[class="opus-read-more"]').click() # 展开全文
            # await page.locator('[class="open-app-dialog-btn cancel"]').click() # 打开APP->取消
            await page.evaluate('document.getElementsByClassName("opus-module-content limit")[0].className = "opus-module-content"')
            await page.evaluate('document.getElementsByClassName("opus-read-more")[0].style.display = "none"')
        try: # 关注按钮
            await page.evaluate('document.getElementsByClassName("opus-module-author__action")[0].style.display = "none"')
        except:
            pass
        try: # 顶部导航栏
            await page.evaluate('document.getElementsByClassName("opus-nav")[0].style.display = "none"')
        except:
            pass
        try: # 字体
            await self.font_replace_js(page, "opus-modules")
        except:
            pass
        try: # 字体大小
            await self.text_resize_js(page, "opus-modules")
        except:
            pass
        try: # 图片大小
            await page.evaluate("""
            var pic_block = document.getElementsByClassName("bm-pics-block")[0]
            for(i=0;i<pic_block.children.length;i++) {
                pic_block.children[i].style.paddingLeft = "0px"
                pic_block.children[i].style.paddingRight = "0px"
            }
            """)
        except:
            pass
        if not created_time is None:
            try:
                await page.evaluate(f'document.getElementsByClassName("opus-module-author__pub__time")[0].textContent = "{created_time}"')
            except:
                pass
        # await page.wait_for_timeout(600000)
        # 设置动态界面最大高度
        await page.evaluate('document.getElementsByClassName("opus-modules")[0].style.maxHeight = "6000px"')
        return await page.locator('[class="opus-modules"]').screenshot()

    async def bili_dyn_dynamic_process(self, page: Page, created_time: str = None):
        try:
            await page.evaluate('document.getElementsByClassName("dynamic-float-btn")[0].style.display = "none"') # 打开APP浮动按钮
        except:
            pass
        try: # 关注按钮
            await page.evaluate('document.getElementsByClassName("dyn-header__following")[0].style.display = "none"')
        except:
            pass
        try: # 转发原动态关注按钮
            await page.evaluate('document.getElementsByClassName("dyn-orig-author__right")[0].style.display = "none"')
        except:
            pass
        try: # 分享栏
            await page.evaluate('document.getElementsByClassName("dyn-share")[0].style.display = "none"')
        except:
            pass
        try: # 取消文章栏高度限制
            await page.evaluate('document.getElementsByClassName("dyn-article__card")[0].style.maxHeight = "fit-content"')
        except:
            pass
        try:
            await self.font_replace_js(page, "dyn-card")# 字体
        except:
            pass
        try: # 字体大小
            await self.text_resize_js(page, "dyn-content")
        except:
            pass
        if not created_time is None:
            try:
                await page.evaluate(f'document.getElementsByClassName("dyn-header__author__time")[0].textContent = "{created_time}"')
            except:
                pass
        # await page.wait_for_timeout(600000)
        return await page.locator('[class="dyn-card"]').screenshot()

    async def bili_dyn_pc_process(self, page: Page, created_time: str = None):
        # await page.wait_for_timeout(600000)
        try: # 右下角登录提示
            await page.evaluate('document.getElementsByClassName("login-tip")[0].style.display = "none"')
        except:
            pass
        try: # 顶栏登录提示
            await page.evaluate('document.getElementsByClassName("van-popover").forEach(e => e.style.display = "none")')
        except:
            pass
        try: # 顶栏
            await page.evaluate('document.getElementsByClassName("international-header")[0].style.display = "none"')
        except:
            pass
        # await page.wait_for_timeout(600000)
        try:
            return await page.locator('[class="bili-dyn-item__main"]').screenshot()
        except Exception as e:
            await page.screenshot(path="bili_dyn_pc_err_pic.png")
            raise e

    async def new_context(self, **kwargs) -> BrowserContext:
        browser = await self.get_browser()
        try:
            context = await browser.new_context(**kwargs)
        except Error as e:
            if "Target page, context or browser has been closed" in e.message:
                await self.restart_browser()
                context = await browser.new_context(**kwargs)
        return context

    async def get_bili_dyn_pic(self, dynamic_id: str, created_time: str = None, cookie: str = None) -> bytes:
        if get_config_value("builder", "bili_dyn", "is_pc"):
            context = await self.new_context(user_agent=self.DEFAULT_PC_UA, device_scale_factor=2)
        else:
            context = await self.new_context(user_agent=self.DEFAULT_MOBILE_UA, device_scale_factor=2)
        await context.add_cookies(cookie_to_dict_list(cookie, ".bilibili.com"))
        page = await context.new_page()
        await page.add_init_script("Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});")
        try:
            await page.set_viewport_size({'width':1300, 'height':3500})
            if get_config_value("builder", "bili_dyn", "is_pc"):
                await page.goto('https://t.bilibili.com/'+dynamic_id, wait_until="networkidle", timeout=15000)
            elif get_config_value("builder", "bili_dyn", "is_new_layout"):
                await page.goto('https://m.bilibili.com/opus/'+dynamic_id, wait_until="networkidle", timeout=15000)
                try:
                    await page.locator('[class="error-container"]').text_content(timeout=500)
                    raise DynamicRemovedException()
                except TimeoutError:
                    pass
            else:
                await page.goto('https://m.bilibili.com/dynamic/'+dynamic_id, wait_until="networkidle", timeout=15000)
                if page.url.startswith("https://m.bilibili.com/404"):
                    raise DynamicRemovedException()
            if get_config_value("builder", "bili_dyn", "is_pc"):
                pic = await self.bili_dyn_pc_process(page, created_time)
            elif "opus" in page.url:
                pic = await self.bili_dyn_opus_process(page, created_time)
            else:
                pic = await self.bili_dyn_dynamic_process(page, created_time)
        except Exception as e:
            raise e
        finally:
            try:
                await page.close()
                await context.close()
            except Exception as e:
                await self.restart_browser()
        # debug
        # debug_save_pic(pic, "dyn", dynamic_id)
        return pic

def debug_save_pic(pic: bytes, typ: str, id: str):
    img = Image.open(io.BytesIO(pic))
    img.save(f"debug_pic/{typ}/{id}.png")