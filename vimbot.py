import time
from io import BytesIO

from PIL import Image
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

vimium_path = "vimium-master"


class Vimbot:
    def __init__(self, headless=False):
        self.context = (
            sync_playwright()
            .start()
            .chromium.launch_persistent_context(
                "",
                headless=False,
                args=[
                    "--headless=new",
                    f"--disable-extensions-except={vimium_path}",
                    f"--load-extension={vimium_path}",
                ],
                ignore_https_errors=True,
            )
        )

        self.page = self.context.new_page()
        stealth_sync(self.page)
        self.page.set_viewport_size({"width": 1080, "height": 720})

    def perform_action(self, action):
        if "DONE" in action:
            return True
        if "CLICK" in action and "TYPE" in action:
            self.click(action["CLICK"])
            self.type(action["TYPE"])
        if "NAVIGATE" in action:
            self.navigate(action["NAVIGATE"])
        elif "TYPE" in action:
            self.type(action["TYPE"])
        elif "CLICK" in action:
            self.click(action["CLICK"])

    def navigate(self, url):
        self.page.goto(url=url if "://" in url else "https://" + url, timeout=60000)
        time.sleep(2)
        self.page.screenshot(full_page=True, path=f"{url.split('/')[-1]}.png")

    def type(self, text):
        time.sleep(1)
        self.page.keyboard.type(text)
        self.page.keyboard.press("Enter")

    def click(self, text):
        self.page.keyboard.type(text)

    def capture(self):
        # capture a screenshot with vim bindings on the screen
        self.page.keyboard.press("Escape")
        self.page.keyboard.type("f")
        
        self.page.wait_for_timeout(1000)
        screenshot = Image.open(BytesIO(self.page.screenshot())).convert("RGB")
        self.page.screenshot(full_page=True, path="asdf.png")
        return screenshot
