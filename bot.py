import logging
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN    = "8791950861:AAG-YcpgrrQ6l2KDX0ClOj8ofOVWEBwf7eo"
CLICKUP_API_TOKEN = "pk_106663989_PGMR0EIAVC14BW3MJ8YQAAJ9PCQKDJCA"
CLICKUP_LIST_ID   = "901522274038"
FIELD_PIB_KONTAKT = "770029eb-479c-44c2-952b-ab6e65644fdb"
FIELD_POSADA      = "0f16e7f4-e3a2-4c87-a27c-e621e6c5b9ee"
POSADA_OPTIONS    = {"hrd":"f6e2f95c-e554-4de1-a768-d3401878ed3e","cmo":"7fb92f42-f87a-4e07-937c-8a7aa1f7d221","ceo":"b5dd5f11-5fb1-4e79-b2de-20874d42f6d6","cco":"08c2368c-aeb7-455d-9ba5-abf0a215684a","coo":"8b0e933a-2052-4217-a221-1e4ae4003df9","cpo":"55ce900e-21fd-4607-81b4-0b58bfc8158a","бренд менеджер":"c02d24d8-6f58-48d6-83f5-992adca22a82","власник":"2097f45e-e6a8-4564-bba7-3024cddca03c","інше":"91d66190-6f20-4320-98b9-af92c031e520"}
POSADA_DEFAULT    = "91d66190-6f20-4320-98b9-af92c031e520"
GROUP_TRIGGER     = "#лід"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_lead(text):
    lines=[l.strip() for l in text.strip().split("\n") if l.strip()]
    if len(lines)<3: return None
    clean=lambda line: line.split(":",1)[1].strip() if ":" in line else line
    return {"company":clean(lines[0]),"name":clean(lines[1]),"contact":clean(lines[2]),"position":clean(lines[3]) if len(lines)>3 else "інше","comment":clean(lines[4]) if len(lines)>4 else ""}

def resolve_posada(p): return POSADA_OPTIONS.get(p.strip().lower(),POSADA_DEFAULT)

def create_task(lead):
    return requests.post(f"https://api.clickup.com/api/v2/list/{CLICKUP_LIST_ID}/task",json={"name":lead["company"],"description":lead["comment"],"status":"LEADS","priority":2,"custom_fields":[{"id":FIELD_PIB_KONTAKT,"value":lead["name"]+" / "+lead["contact"]},{"id":FIELD_POSADA,"value":resolve_posada(lead["position"])}]},headers={"Authorization":CLICKUP_API_TOKEN,"Content-Type":"application/json"},timeout=10).json()

async def start(u,c): await u.message.reply_text("Надішли:\nКомпанія\nПІБ\nКонтакт\nПосада\nКоментар\n\nУ групових чатах починай з #лід")

async def handle(u,c):
    if not u.message or not u.message.text: return
    text = u.message.text.strip()
    chat_type = u.message.chat.type
    if chat_type in ("group","supergroup"):
        if not text.lower().startswith(GROUP_TRIGGER):
            return
        lines = text.split("\n")
        lines = [l for l in lines if l.strip().lower() != GROUP_TRIGGER]
        text = "\n".join(lines)
    lead=parse_lead(text)
    if not lead: await u.message.reply_text("Потрібно 3+ рядки"); return
    await u.message.reply_text("Створюю...")
    try:
        r=create_task(lead)
        await u.message.reply_text(f"Готово! {r.get('url','')}" if "id" in r else f"Помилка: {r.get('err',r)}")
    except Exception as e: await u.message.reply_text(f"Помилка: {e}")

def main():
    app=Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__": main()
