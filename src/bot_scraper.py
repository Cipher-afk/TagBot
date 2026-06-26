from playwright.async_api import async_playwright, BrowserContext, Page
from aiogram.types import Message, FSInputFile
from aiogram import Bot
from buttons import login_button
import ddddocr, asyncio, os
from pathlib import Path
from backend.models import Plan

ocr = ddddocr.DdddOcr()
BASE_DIR = Path(__file__).parent.resolve()


class BotScraper:
    @staticmethod
    def captcha_translate(img_bytes):
        result = ocr.classification(img=img_bytes)
        print(result)
        return result

    async def login(
        self, page: Page, phone_number: str, password: str, message: Message
    ):
        # await page.fill("input[placeholder = 'Account / Phone number']",phone_number)
        await message.answer("Login Started 💻🚀")
        logged_in = False
        print("Done")
        await page.wait_for_selector(
            "input[placeholder='Account / Phone number']", timeout=10000
        )
        print("Selector found")
        while True:
            await page.wait_for_timeout(5000)
            await page.get_by_placeholder("Account / Phone number").fill(
                phone_number, timeout=10000
            )
            await page.fill("#login-pwd", password, timeout=10000)
            await message.answer(
                "Solving captcha...\n This might take time depending on your network speed 📶"
            )
            while True:
                captcha_image = await page.query_selector(".span-verify")
                img_screenshot = await captcha_image.screenshot()
                captcha_code = await asyncio.to_thread(
                    BotScraper.captcha_translate, img_screenshot
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
                    await message.answer("Captcha Solved Logging in 🎉".title())
                    break
            await page.wait_for_timeout(8000)
            if await page.get_by_text(
                "Incorrect account or password", exact=True
            ).is_visible(timeout=8000):
                await page.locator(".dialog-button", has_text="OK").click()
                await page.get_by_placeholder("Account / Phone number").clear()
                await page.locator("#login-pwd").clear()
                await page.locator('input[name="user-verify"]').clear()
                await message.answer(
                    "Account or password is incorrect please Login again",
                    reply_markup=login_button,
                )
                return
            elif await page.get_by_text("Incorrect password.").is_visible(timeout=8000):
                await page.locator(".dialog-button", has_text="OK").click()
                await page.get_by_placeholder("Account / Phone number").clear()
                await page.locator("#login-pwd").clear()
                await page.locator('input[name="user-verify"]').clear()
                await message.answer(
                    "Password is incorrect please Login again",
                    reply_markup=login_button,
                )
                return
            else:
                break
        await page.wait_for_url(
            "https://m.tag368.net/#/home/", wait_until="domcontentloaded"
        )
        # break

    async def do_tasks(self, plan: str, page: Page, message: Message, bot: Bot):
        await message.answer("Home Page Loading... 🔃")
        await page.goto(
            "https://m.tag368.net/#/member-center/order-center/0/",
            wait_until="domcontentloaded",
            timeout=100000,
        )
        await message.answer("Home Page loaded ✅")
        # await page.locator(".copybutton", has_text="Get New Order").click()
        # await page.wait_for_timeout(7000)
        await message.answer("Doing Tasks.... 🤖")
        await page.wait_for_selector(".jindu", timeout=10000, state="visible")
        await page.wait_for_timeout(7000)
        task_el = await page.query_selector(".jindu")
        task_text = await task_el.text_content()
        print(task_text)
        print(task_text.split(" "))
        if plan == Plan.free:
            task_value = 3
        else:
            task_value = int(
                task_text.split(" ")[1].lstrip("Progress ").split("/")[1][0]
            )  # splitting Task Progress（0/0）
            print(task_value)
        # await page.wait_for_timeout(20000)
        tasks_done = 0
        for i in range(int(task_value)):
            await message.answer(f"({tasks_done}/{task_value}) Completed")
            await page.locator(".copybutton", has_text="Get New Order").click()
            await page.wait_for_timeout(3000)
            if await page.get_by_text(
                "You have reached the maximum number of orders for today and cannot accept more orders"
            ).is_visible():
                await message.answer("Your have completed all your tasks for today ✅")
                return
            if await page.get_by_text(
                "You have a pending order, would you like to view it now?", exact=True
            ).is_visible():
                await message.answer("Pending order found, viewing now...")
                await page.locator(".dialog-button", has_text="OK").click()
                await page.wait_for_timeout(3000)
            await page.wait_for_selector(".copy", timeout=10000)
            await page.get_by_text("Fill in the rating", exact=True).click()
            print("clicked")
            await page.wait_for_selector(".info", state="visible", timeout=10000)
            await page.get_by_text("Submit Rating", exact=True).click()
            await page.wait_for_timeout(3000)
            tasks_done += 1
        await message.answer(f"({tasks_done}/{task_value}) Completed")
        await page.wait_for_timeout(6000)
        await page.screenshot(path="tasks_done.png")
        file_path = Path(BASE_DIR, "task_done.png")
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=FSInputFile(path=file_path),
            caption=f"All tasks completed! Total tasks done: {tasks_done}",
        )
        os.remove(file_path)

    async def main(
        self, plan: str, phone_number: str, password: str, message: Message, bot: Bot
    ):
        async with async_playwright() as playwright:
            await message.answer("Loading....🔃")
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await message.answer("Tag Website Launching.... 🚀")
            await page.goto(
                "https://m.tag368.net/#/", wait_until="domcontentloaded", timeout=200000
            )
            await message.answer("Login Page loaded 🔑🔐")
            await self.login(
                page=page, phone_number=phone_number, password=password, message=message
            )
            await message.answer("Login Completed ✅")
            task_page = await context.new_page()
            await self.do_tasks(plan=plan, page=task_page, message=message, bot=bot)
            # await context.close()
            # await browser.close()


if __name__ == "__main__":
    scraper = BotScraper()
    asyncio.run(scraper.main(phone_number="7025614656", password="123456"))
