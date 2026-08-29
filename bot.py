import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

reminders = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salam!\n\n"
        "Mən sənin xatırlatma botunam.\n\n"
        "Xatırlatma yaratmaq üçün belə yaz:\n"
        "29.08.2026 15:00 Arazla görüş\n\n"
        "📋 /list — xatırlatmaları göstərir\n"
        "🗑 /delete 1 — xatırlatmanı silir\n"
        "🗑 /deleteall — hamısını silir"
    )

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_reminders = reminders.get(user_id, [])

    if not user_reminders:
        await update.message.reply_text("📭 Aktiv xatırlatma yoxdur.")
        return

    text = "📋 Aktiv xatırlatmalar:\n\n"

    for i, r in enumerate(user_reminders, 1):
        text += f"{i}️⃣ {r['time'].strftime('%d.%m.%Y %H:%M')} — {r['text']}\n"

    await update.message.reply_text(text)

async def delete_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("Məsələn: /delete 1")
        return

    try:
        number = int(context.args[0]) - 1
    except ValueError:
        await update.message.reply_text("❌ Nömrəni düzgün yaz.")
        return

    user_reminders = reminders.get(user_id, [])

    if number < 0 or number >= len(user_reminders):
        await update.message.reply_text("❌ Belə xatırlatma yoxdur.")
        return

    deleted = user_reminders.pop(number)

    await update.message.reply_text(
        f"🗑 Silindi:\n{deleted['time'].strftime('%d.%m.%Y %H:%M')} — {deleted['text']}"
    )

async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reminders[user_id] = []

    await update.message.reply_text("🗑 Bütün xatırlatmalar silindi.")

async def check_reminders(application):
    while True:
        now = datetime.now()

        for user_id in list(reminders.keys()):
            user_reminders = reminders[user_id]
            remaining = []

            for r in user_reminders:
                if now >= r["time"]:
                    try:
                        await application.bot.send_message(
                            chat_id=user_id,
                            text=f"🔔 XATIRLATMA\n\n{r['text']}"
                        )
                    except Exception as e:
                        print("Mesaj göndərilmədi:", e)
                else:
                    remaining.append(r)

            reminders[user_id] = remaining

        await asyncio.sleep(10)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text.strip()

    try:
        date_part = message[:16]
        reminder_text = message[17:].strip()

        reminder_time = datetime.strptime(
            date_part,
            "%d.%m.%Y %H:%M"
        )

        if not reminder_text:
            raise ValueError

        if reminder_time <= datetime.now():
            await update.message.reply_text(
                "❌ Bu vaxt artıq keçib."
            )
            return

        reminders.setdefault(user_id, []).append({
            "time": reminder_time,
            "text": reminder_text
        })

        await update.message.reply_text(
            f"✅ Xatırlatma əlavə edildi!\n\n"
            f"⏰ {reminder_time.strftime('%d.%m.%Y %H:%M')}\n"
            f"📝 {reminder_text}"
        )

    except Exception:
        await update.message.reply_text(
            "❌ Format düzgün deyil.\n\n"
            "Belə yaz:\n"
            "29.08.2026 15:00 Arazla görüş"
        )

async def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_reminders))
    application.add_handler(CommandHandler("delete", delete_reminder))
    application.add_handler(CommandHandler("deleteall", delete_all))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )

    asyncio.create_task(check_reminders(application))

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
