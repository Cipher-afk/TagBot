from playwright.async_api import async_playwright, BrowserContext, Page
import ddddocr
import asyncio

ocr = ddddocr.DdddOcr()


class Scraper:
    @staticmethod
    def captcha_translate(img_bytes):
        result = ocr.classification(img=img_bytes)
        print(result)
        return result

    async def login(self, page: Page, phone_number: str, password: str):
        # await page.fill("input[placeholder = 'Account / Phone number']",phone_number)
        logged_in = False
        await page.wait_for_load_state("networkidle")
        while not logged_in:
            await page.get_by_placeholder("Account / Phone number").fill(phone_number)
            await page.fill("#login-pwd", password)
            while not logged_in:
                print("Solving captcha...")
                captcha_image = await page.query_selector(".span-verify")
                img_screenshot = await captcha_image.screenshot()
                captcha_code = await asyncio.to_thread(
                    Scraper.captcha_translate, img_screenshot
                )
                if captcha_code == "":
                    print("Captcha recognition failed, retrying...")
                    continue
                await page.fill('input[name="user-verify"]', captcha_code)
                await page.get_by_role("link", name="Log in").click()
                await page.wait_for_timeout(8000)
                # , has_text="Incorrect verification code"
                if await page.get_by_text(
                    "Incorrect verification code", exact=True
                ).is_visible():
                    print("Verification code is incorrect,trying again...")
                    await page.locator(".dialog-button", has_text="OK").click()
                    await page.locator('input[name="user-verify"]').clear()
                    continue
                else:
                    print("Code Correct")
                    break
            await page.wait_for_timeout(8000)
            if await page.get_by_text(
                "Incorrect account or password", exact=True
            ).is_visible(timeout=8000):
                print("Account or password is incorrect")
                await page.locator(".dialog-button", has_text="OK").click()
                await page.get_by_placeholder("Account / Phone number").clear()
                await page.locator("#login-pwd").clear()
                await page.locator('input[name="user-verify"]').clear()
                break
            else:
                break
        await page.wait_for_url(
            "https://m.tag368.net/#/home/", wait_until="domcontentloaded"
        )
        # break

    async def do_tasks(self, page: Page):
        await page.goto(
            "https://m.tag368.net/#/member-center/order-center/0/",
            wait_until="domcontentloaded",
        )
        # await page.locator(".copybutton", has_text="Get New Order").click()
        # await page.wait_for_timeout(7000)
        await page.wait_for_selector(".jindu", timeout=10000, state="visible")
        await page.wait_for_timeout(5000)
        task_el = await page.query_selector(".jindu")
        task_text = await task_el.text_content()
        print(task_text)
        print(task_text.split(" "))
        task_value = int(
            task_text.split(" ")[1].lstrip("Progress ").split("/")[1][0]
        )  # splitting Task Progress（0/0）
        print(task_value)
        # await page.wait_for_timeout(20000)
        tasks_done = 0
        for i in range(int(task_value)):
            await page.locator(".copybutton", has_text="Get New Order").click()
            await page.wait_for_timeout(3000)
            if await page.get_by_text(
                "You have a pending order, would you like to view it now?", exact=True
            ).is_visible():
                print("Pending order found, viewing now...")
                await page.locator(".dialog-button", has_text="OK").click()
                await page.wait_for_timeout(3000)
            await page.wait_for_selector(".copy", timeout=10000)
            await page.get_by_text("Fill in the rating", exact=True).click()
            print("clicked")
            await page.wait_for_selector(".info", state="visible", timeout=10000)
            await page.get_by_text("Submit Rating", exact=True).click()
            await page.wait_for_timeout(3000)
            tasks_done += 1
        await page.screenshot(path="tasks_done.png")
        print(f"All tasks completed! Total tasks done: {tasks_done}")

    async def main(self, phone_number: str, password: str):
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(
                "https://m.tag368.net/#/", wait_until="networkidle", timeout=100000
            )
            await self.login(page=page, phone_number="7025614656", password="123456")
            task_page = await context.new_page()
            await self.do_tasks(page=task_page)


scraper = Scraper()
asyncio.run(scraper.main())
