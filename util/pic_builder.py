from __future__ import annotations
from typing import Optional
from playwright.async_api import Browser, PlaywrightContextManager, Page, async_playwright

from util.pic_process import join_pic

def cookie_to_dict_list(cookie: str, domain: str):
    cookie_list = cookie.split(";")
    cookies = []
    for c in cookie_list:
        cookie_pair = c.lstrip().rstrip().split("=")
        cookies.append({
            "name": cookie_pair[0],
            "value": cookie_pair[1],
            "url": domain
        })
    return cookies

class PicBuilder:

    def __init__(self, config_dict: dict) -> None:
        self._config_dict = config_dict
        self._playwright_context: Optional[PlaywrightContextManager] = None
        self._browser: Optional[Browser] = None
    
    async def get_browser(self) -> Browser:
        if(self._playwright_context is None):
            self._playwright_context = await async_playwright().start()
        if(self._browser is None):
            self._browser = await self._playwright_context.chromium.launch()
        return self._browser

    async def close_browser(self) -> None:
        if(not self._browser is None):
            await self._browser.close()
        if(not self._playwright_context is None):
            await self._playwright_context.stop()

    async def reset_browser(self, **kwargs) -> Browser:
        if(self._browser):
            try:
                await self._browser.close()
            except:
                pass
        p = await async_playwright().start()
        self._browser = await p.chromium.launch(**kwargs)
        return self._browser

    def get_config(self, key: str, default = None) -> str:
        return self._config_dict.get(key, default)

    async def get_wb_pic(self, wb_id: str, created_time: str = None) -> bytes:
        browser = await self.get_browser()
        context = await browser.new_context(user_agent=self.get_config("weibo_ua"), device_scale_factor=2)
        await context.add_cookies(cookie_to_dict_list(self.get_config("weibo_cookie"), "https://m.weibo.cn"))
        page = await context.new_page()
        try:
            page.set_default_timeout(10000)
            await page.set_viewport_size({'width':560, 'height':3500})
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
    }
                """)
            except:
                pass
            # await page.wait_for_timeout(600000)
            upper_pic = await page.locator('[class="card-wrap"]').first.screenshot()
            lower_pic = await page.locator('[class="weibo-main"]').screenshot()
        except Exception as e:
            raise e
        finally:
            await page.close()
            await context.close()
        pic = join_pic(upper_pic, lower_pic)
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
    var divnum = 0
    if(isBtn || element.className.includes('-container')) {
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
    element.style.fontFamily = '"""+ ", ".join(font_list) +"""'
}
            """)

    async def bili_dyn_opus_process(self, page: Page, created_time: str = None):
        try: # 底部开启APP提示框
            await page.evaluate('document.getElementsByClassName("openapp-dialog")[0].style.display = "none"')
        except:
            pass
        await page.evaluate('document.getElementsByClassName("m-float-openapp")[0].style.display = "none"') # 开启APP浮动按钮
        if await page.locator('[class="opus-read-more"]').is_visible():
            await page.locator('[class="opus-read-more"]').click() # 展开全文
            await page.locator('[class="open-app-dialog-btn cancel"]').click() # 打开APP->取消
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
        if not created_time is None:
            try:
                await page.evaluate(f'document.getElementsByClassName("opus-module-author__pub__time")[0].textContent = "{created_time}"')
            except:
                pass
        # await page.wait_for_timeout(600000)
        return await page.locator('[class="opus-modules"]').screenshot()

    async def bili_dyn_dynamic_process(self, page: Page, created_time: str = None):
        await page.evaluate('document.getElementsByClassName("dynamic-float-btn")[0].style.display = "none"') # 打开APP浮动按钮
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
        try: # 字体
            await self.font_replace_js(page, "dyn-card")
        except:
            pass
        if not created_time is None:
            try:
                await page.evaluate(f'document.getElementsByClassName("dyn-header__author__time")[0].textContent = "{created_time}"')
            except:
                pass
        # await page.wait_for_timeout(600000)
        return await page.locator('[class="dyn-card"]').screenshot()

    async def get_bili_dyn_pic(self, dynamic_id: str, created_time: str = None) -> bytes:
        mobile_bili_ua = 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
        browser = await self.get_browser()
        context = await browser.new_context(user_agent=mobile_bili_ua, device_scale_factor=2)
        page = await context.new_page()
        try:
            await page.set_viewport_size({'width':560, 'height':3500})
            if self.get_config("bili_dyn_new_style", False):
                await page.goto('https://m.bilibili.com/opus/'+dynamic_id, wait_until="networkidle", timeout=15000)
            else:
                await page.goto('https://m.bilibili.com/dynamic/'+dynamic_id, wait_until="networkidle", timeout=15000)
            if "opus" in page.url:
                pic = await self.bili_dyn_opus_process(page, created_time)
            else:
                pic = await self.bili_dyn_dynamic_process(page, created_time)
        except Exception as e:
            raise e
        finally:
            await page.close()
            await context.close()
        return pic