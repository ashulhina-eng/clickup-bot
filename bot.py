import logging
import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN    = os.environ.get("TELEGRAM_TOKEN", "")
CLICKUP_API_TOKEN = os.environ.get("CLICKUP_API_TOKEN", "")
CLICKUP_LIST_ID   = "901522274038"
FIELD_PIB_KONTAKT = "770029eb-479c-44c2-952b-ab6e65644fdb"
FIELD_POSADA      = "0f16e7f4-e3a2-4c87-a27c-e621e6c5b9ee"
POSADA_OPTIONS    = {"hrd":"f6e2f95c-e554-4de1-a768-d3401878ed3e","cmo":"7fb92f42-f87a-4e07-937c-8a7aa1f7d221","ceo":"b5dd5f11-5fb1-4e79-b2de-20874d42f6d6","cco":"08c2368c-aeb7-455d-9ba5-abf0a215684a","coo":"8b0e933a-2052-4217-a221-1e4ae4003df9","cpo":"55ce900e-21fd-4607-81b4-0b58bfc8158a","\u0431\u0440\u0435\u043d\u0434 \u043c\u0435\u043d\u0435\u0434\u0436\u0435\u0440":"c02d24d8-6f58-48d6-83f5-992adca22a82","\u0432\u043b\u0430\u0441\u043d\u0438\u043a":"2097f45e-e6a8-4564-bba7-3024cddca03c","\u0456\u043d\u0448\u0435":"91d66190-6f20-4320-98b9-af92c031e520"}
POSADA_DEFAULT    = "91d66190-6f20-4320-98b9-af92c031e520"
GROUP_TRIGGER     = "#\u043b\u0456\u0434"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_lead(text):
    lines=[l.strip() for l in text.strip().split("\n") if l.strip()]
    if len(lines)<3: return None
    clean=lambda line: line.split(":",1)[1].strip() if ":" in line else line
    return {"company":clean(lines[0]),"name":clean(lines[1]),"contact":clean(lines[2]),"position":clean(lines[3]) if len(lines)>3 else "\u0456\u043d\u0448\u0435","comment":clean(lines[4]) if len(lines)>4 else ""}

def resolve_posada(p): return POSADA_OPTIONS.get(p.strip().lower(),POSADA_DEFAULT)

def create_task(lead):
    return requests.post(f"https://api.clickup.com/api/v2/list/{CLICKUP_LIST_ID}/task",json={"name":lead["company"],"description":lead["comment"],"status":"leads","priority":2,"custom_fields":[{"id":FIELD_PIB_KONTAKT,"value":lead["name"]+" / "+lead["contact"]},{"id":FIELD_POSADA,"value":resolve_posada(lead["position"])}]},headers={"Authorization":CLICKUP_API_TOKEN,"Content-Type":"application/json"},timeout=10).json()

async def start(u,c): await u.message.reply_text("\u041d\u0430\u0434\u0456\u0448\u043b\u0438:\n\u041a\u043e\u043c\u043f\u0430\u043d\u0456\u044f\n\u041f\u0406\u0411\n\u041a\u043e\u043d\u0442\u0430\u043a\u0442\n\u041f\u043e\u0441\u0430\u0434\u0430\n\u041a\u043e\u043c\u0435\u043d\u0442\u0430\u0440\n\n\u0423 \u0433\u0440\u0443\u043f\u043e\u0432\u0438\u0445 \u0447\u0430\u0442\u0430\u0445 \u043f\u043e\u0447\u0438\u043d\u0430\u0439 \u0437 #\u043b\u0456\u0434")

async def handle(u,c):
    if not u.message or not u.message.text: return
    text = u.message.text.strip()
    chat_type = str(u.message.chat.type)
    logger.info(f"Chat type: {chat_type}, text: {text[:50]}")

    if chat_type in ("group", "supergroup"):
        if not text.lower().startswith(GROUP_TRIGGER):
            return
        after_trigger = text[len(GROUP_TRIGGER):]
        if after_trigger == "" or after_trigger.startswith("\n"):
            lines = text.split("\n")[1:]
            text = "\n".join(lines)
        else:
            text = after_trigger.lstrip()

    lead=parse_lead(text)
    if not lead: await u.message.reply_text("\u041f\u043e\u0442\u0440\u0456\u0431\u043d\u043e 3+ \u0440\u044f\u0434\u043a\u0438"); return
    await u.message.reply_text("\u0421\u0442\u0432\u043e\u0440\u044e\u044e...")
    try:
        r=create_task(lead)
        await u.message.reply_text(f"\u0413\u043e\u0442\u043e\u0432\u043e! {r.get('url','')}" if "id" in r else f"\u041f\u043e\u043c\u0438\u043b\u043a\u0430: {r.get('err',r)}")
    except Exception as e: await u.message.reply_text(f"\u041f\u043e\u043c\u0438\u043b\u043a\u0430: {e}")

def main():
    app=Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__": main()
