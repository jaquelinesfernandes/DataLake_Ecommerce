import os
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from agente import chat, gerar_relatorio

load_dotenv()


def _log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def salvar_chat_id(chat_id: int):
    chat_id_str = str(chat_id)
    current = os.getenv("CHAT_ID")
    if current == chat_id_str:
        return

    env_path = ".env"
    if not os.path.exists(env_path):
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(f"CHAT_ID={chat_id_str}\n")
        os.environ["CHAT_ID"] = chat_id_str
        _log(f"CHAT_ID={chat_id_str} salvo no .env")
        return

    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    found = False
    new_lines = []
    for line in lines:
        if line.startswith("CHAT_ID="):
            new_lines.append(f"CHAT_ID={chat_id_str}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"CHAT_ID={chat_id_str}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    os.environ["CHAT_ID"] = chat_id_str
    _log(f"CHAT_ID={chat_id_str} salvo no .env")


async def _send_long(update: Update, text: str):
    chunks = [text[i : i + 4096] for i in range(0, len(text), 4096)]
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(chunk)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    salvar_chat_id(update.message.chat_id)
    await update.message.reply_text(
        "Olá! Sou o agente de dados do e-commerce.\n\n"
        "Você pode me fazer qualquer pergunta sobre vendas, clientes e pricing.\n\n"
        "Comandos disponíveis:\n"
        "/start — Boas-vindas\n"
        "/relatorio — Gera o relatório executivo completo"
    )


async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    salvar_chat_id(update.message.chat_id)
    await update.message.chat.send_action("typing")
    await update.message.reply_text("Gerando relatório executivo, aguarde...")

    rel = gerar_relatorio()
    await _send_long(update, rel)


async def mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    salvar_chat_id(update.message.chat_id)
    await update.message.chat.send_action("typing")

    pergunta = update.message.text

    if "historico" not in context.user_data:
        context.user_data["historico"] = []

    historico = context.user_data["historico"]
    resposta = chat(pergunta, historico)

    historico.append({"role": "user", "content": pergunta})
    historico.append({"role": "assistant", "content": resposta})
    if len(historico) > 20:
        context.user_data["historico"] = historico[-20:]

    await _send_long(update, resposta)


def main():
    token = os.getenv("TELEGRAM")
    if not token:
        raise ValueError("TELEGRAM token não configurado no .env")

    _log("Iniciando bot Telegram...")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("relatorio", relatorio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensagem))

    _log("Bot rodando! Ctrl+C para parar.")
    app.run_polling()


if __name__ == "__main__":
    main()
