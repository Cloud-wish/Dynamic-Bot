from typing import Optional
from playwright.async_api import Browser, async_playwright

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
        self._browser: Optional[Browser] = None
    
    async def get_browser(self) -> Browser:
        if(self._browser == None):
            p = await async_playwright().start()
            self._browser = await p.chromium.launch()
        return self._browser

    async def reset_browser(self, **kwargs) -> Browser:
        if(self._browser):
            try:
                await self._browser.close()
            except:
                pass
        p = await async_playwright().start()
        self._browser = await p.chromium.launch(**kwargs)
        return self._browser

    def get_config(self, key: str) -> str:
        return self._config_dict[key]

    async def get_wb_pic(self, wb_id: str, created_time: str = None) -> bytes:
        browser = await self.get_browser()
        context = await browser.new_context(user_agent=self.get_config("weibo_ua"), device_scale_factor=2)
        await context.add_cookies(cookie_to_dict_list(self.get_config("weibo_cookie"), "https://m.weibo.cn"))
        page = await context.new_page()
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
        await page.close()
        await context.close()
        pic = join_pic(upper_pic, lower_pic)
        return pic

    async def get_bili_dyn_pic(self, dynamic_id: str, created_time: str = None) -> bytes:
        mobile_bili_ua = 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
        browser = await self.get_browser()
        context = await browser.new_context(user_agent=mobile_bili_ua, device_scale_factor=2)
        page = await context.new_page()
        await page.set_viewport_size({'width':560, 'height':3500})
        await page.goto('https://m.bilibili.com/dynamic/'+dynamic_id, wait_until="networkidle", timeout=15000)
        await page.evaluate('document.getElementsByClassName("dynamic-float-btn")[0].style.display = "none"')
        try:
            await page.evaluate('document.getElementsByClassName("dyn-header__following")[0].style.display = "none"')
        except:
            pass
        try:
            await page.evaluate('document.getElementsByClassName("dyn-orig-author__right")[0].style.display = "none"')
        except:
            pass
        try:
            await page.evaluate('document.getElementsByClassName("dyn-share")[0].style.display = "none"')
        except:
            pass
        # await page.wait_for_timeout(600000)
        try:
            await page.evaluate("""
var className = "dyn-card";
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
    element.style.fontFamily = "'Microsoft YaHei', 'Noto Color Emoji', 'Unifont', 'sans-serif'"
}
            """)
        except:
            pass
        if not created_time is None:
            try:
                await page.evaluate(f'document.getElementsByClassName("dyn-header__author__time")[0].textContent = "{created_time}"')
            except:
                pass
        # await page.wait_for_timeout(600000)
        pic = await page.locator('[class="dyn-card"]').screenshot()
        await page.close()
        await context.close()
        return pic