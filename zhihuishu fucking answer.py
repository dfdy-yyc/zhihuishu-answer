import asyncio
import time
from playwright.async_api import async_playwright
from openai import OpenAI

TARGET_URL = "https://onlineweb.zhihuishu.com/onlinestuh5"
TIMEOUT = 300  # 最大等待时间（秒）

async def monitor_url_change():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="msedge",
            headless=False,
            args=["--start-maximized"]
        )
        context = await browser.new_context()
        page = await context.new_page()

        # 进入登录页面
        await page.goto("https://onlineweb.zhihuishu.com/onlinestuh5")
        print("请手动完成登录...")#自己扫码懂吧，扫的慢上面加时间

        # 使用更可靠的URL等待方式
        try:
            await page.wait_for_url(
                lambda url: TARGET_URL in url,
                timeout=TIMEOUT*1000
            )
            print("检测到目标URL，开始执行后续操作")
        except Exception as e:
            raise TimeoutError(f"{TIMEOUT}秒内未检测到目标URL")

        # 登录后操作流程
        async with page.expect_popup() as page1_info:
            await page.get_by_role("link", name="问答").first.click() #你自己要回答啥问题就写啥，比如第一个就是first
        page1 = await page1_info.value
        
        await page1.get_by_text("最新").click()
        await page1.wait_for_timeout(2000)
        await page1.get_by_text("最新").click()#问为什么click两次问就是网页特性有的时候一次刷不出来最新问题
        await page1.wait_for_selector('//*[@id="app"]/div/div[2]/div[1]/div/div[2]/div[1]/div/ul/li[2]/div/span')
        await page1.wait_for_timeout(2000)
        
        pages = {}  # 用字典存储动态页面
        client = OpenAI(api_key="自己找，什么硅基流动很便宜，而且还送东西，你要是没注册：https://cloud.siliconflow.cn/i/RXQhdWD7，复制网址去注册",base_url="https://api.siliconflow.cn/v1（硅基流动就是这个）") #自己找api,免费试用的一抓一把，而且这玩意很便宜的，deepseekv3回答几十个也就几毛钱
        for i in range(2, 20):     #学过python的都懂吧，第一个是2是因为我xpath的第一个不是问题，前面就别改了，后面你要回答几个问题就写几个
            async with page1.expect_popup() as pagex_info:
                await page1.locator(f'//*[@id="app"]/div/div[2]/div[1]/div/div[2]/div[1]/div/ul/li[{i}]/div/span').scroll_into_view_if_needed()
                await page1.locator('div.infinite-list-wrapper').hover()
                await page1.mouse.wheel(0, 500)  # 垂直滚动500像素（我感觉少了你们也可以加或者有更好的想法，不过我感觉是滑了但也没滑，自动化你可以自己手动往下多滑些
                await page1.wait_for_timeout(2000)
                await page1.locator(f'//*[@id="app"]/div/div[2]/div[1]/div/div[2]/div[1]/div/ul/li[{i}]/div/span').click()
                await page1.wait_for_timeout(2000)
            pages[f'page{i}'] = await pagex_info.value
            await pages[f'page{i}'].wait_for_timeout(2000)
            
            
            question=await pages[f'page{i}'].locator('#app > div > div.question-all.clearfix > div.question-left > div.question-box.clearfix > div.question-content > p > span').text_content()
            await pages[f'page{i}'].wait_for_timeout(2000)
            print(f"第{i}个问题的标题：{question}")
            try:
                # 显式等待元素出现（最多等待5秒）
                locator = pages[f'page{i}'].locator("div").filter(has_text="我来回答").nth(2)
                await locator.wait_for(state="visible", timeout=5000)
                await locator.click()
            except Exception as e:
                print(f"页面{i}无此元素，错误信息：{str(e)}")
                await pages[f'page{i}'].close()
                continue  # 跳过当前循环
                        # 调用OpenAI生成回答
            response = client.chat.completions.create(
                model="Qwen/Qwen2.5-72B-Instruct",
                messages=[
                    {"role": "system", "content": "你是一名大学生，即将回答以下问题，要求回答字数在30字以下，一句话说完"},
                    {"role": "user", "content": question}
                ],
                max_tokens=500
            )

            answer = response.choices[0].message.content


            print(f"正在回答第{i}个问题")
            

            await pages[f'page{i}'].get_by_role("textbox", name="请输入您的回答").fill(answer)
            await pages[f'page{i}'].wait_for_timeout(2000)
            await pages[f'page{i}'].get_by_text("立即发布").click()
            await pages[f'page{i}'].wait_for_timeout(2000)
            await pages[f'page{i}'].locator('//*[@id="app"]/div/div[3]/div[1]/div[2]/ul/li[1]/div[3]/div[2]/div[1]/i').click()
            await pages[f'page{i}'].wait_for_timeout(2000)
            await pages[f'page{i}'].close()
            print(f"第{i}个问题回答完成")

        input("按回车结束程序...")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(monitor_url_change())
