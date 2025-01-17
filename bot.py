import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from spotify import get_playlist_top_tracks, search_tracks, get_artist_profile, get_album_tracks, get_top_tracks_for_artist
import bot_tokens

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("bot_activity.log", mode="a"), logging.StreamHandler()]
)

conn = sqlite3.connect("user_data.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    query TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')



MAIN_MENU = ReplyKeyboardMarkup(
    [["Топ-10 треков", "Поиск треков", "Профиль исполнителя", "Список треков из альбома", "Топ треки артиста"]],
    resize_keyboard=True
)

def log_user_query(user_id, username, query):
    try:
        cursor.execute(
            "SELECT query FROM users WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
        )
        last_query = cursor.fetchone()

        if last_query and last_query[0] == query:
            logging.info(f"Повторный запрос от пользователя {username} ({user_id}): {query}")
            return

        cursor.execute(
            "INSERT INTO users (user_id, username, query) VALUES (?, ?, ?)",
            (user_id, username, query)
        )
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Ошибка записи в базу данных: {e}")




async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    log_user_query(user.id, user.username, "start")
    logging.info(f"Пользователь {user.username} ({user.id}) использовал команду /start")
    await update.message.reply_text(
        "Привет! Выберите действие из меню ниже.",
        reply_markup=MAIN_MENU
    )

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user = update.message.from_user
    log_user_query(user.id, user.username, user_input)
    logging.info(f"Пользователь {user.username} ({user.id}) выбрал: {user_input}")

    if user_input == "Топ-10 треков":
        playlist_id = "6qv7CRaZr9nJaamM8Xtrv6" 
        tracks = get_playlist_top_tracks(playlist_id)
        if tracks:
            message = "\n".join([f"{i+1}. {t['name']} - {t['artist']} [Слушать]({t['url']})" for i, t in enumerate(tracks)])
            await update.message.reply_text(f"Топ-10 треков:\n{message}", parse_mode="Markdown")
        else:
            await update.message.reply_text("Не удалось загрузить треки.")
    elif user_input == "Поиск треков":
        await update.message.reply_text("Введите название трека:")
        context.user_data["search_mode"] = "track"
    elif user_input == "Профиль исполнителя":
        await update.message.reply_text("Введите имя исполнителя:")
        context.user_data["search_mode"] = "artist"
    elif user_input == "Список треков из альбома":
        await update.message.reply_text("Введите название альбома:")
        context.user_data["search_mode"] = "album"
    elif user_input == "Топ треки артиста":
        await update.message.reply_text("Введите имя исполнителя:")
        context.user_data["search_mode"] = "artist_top_tracks"
    else:
        search_mode = context.user_data.get("search_mode")
        if search_mode == "track":
            await search_for_tracks(update, user_input)
        elif search_mode == "artist":
            await search_artist_profile(update, user_input)
        elif search_mode == "album":
            await search_for_album_tracks(update, user_input)
        elif search_mode == "artist_top_tracks":
            await search_top_tracks(update, user_input)
        else:
            await update.message.reply_text("Пожалуйста, выберите действие из меню.")

async def search_for_tracks(update: Update, query):
    tracks = search_tracks(query)
    user = update.message.from_user
    log_user_query(user.id, user.username, query)
    if tracks:
        tracks_message = "\n".join([f"{i+1}. {t['name']} - {t['artist']} [Слушать]({t['url']})" for i, t in enumerate(tracks)])
        await update.message.reply_text(f"Найденные треки:\n{tracks_message}", parse_mode="Markdown")
    else:
        await update.message.reply_text("Треки не найдены.")

async def search_artist_profile(update: Update, artist_name):
    profile = get_artist_profile(artist_name)
    user = update.message.from_user
    log_user_query(user.id, user.username, artist_name)
    if profile:
        await update.message.reply_text(f"Профиль исполнителя {artist_name}:\n[Ссылка на профиль]({profile})", parse_mode="Markdown")
    else:
        await update.message.reply_text("Исполнитель не найден.")

async def search_for_album_tracks(update: Update, album_name):
    tracks_message = get_album_tracks(album_name)
    user = update.message.from_user
    log_user_query(user.id, user.username, album_name)
    await update.message.reply_text(tracks_message)

async def search_top_tracks(update: Update, artist_name):
    tracks = get_top_tracks_for_artist(artist_name)
    user = update.message.from_user
    log_user_query(user.id, user.username, artist_name)
    if tracks:
        tracks_message = "\n".join([f"{i+1}. {t['name']} - {t['artist']} [Слушать]({t['url']})" for i, t in enumerate(tracks)])
        await update.message.reply_text(f"Топ треки исполнителя {artist_name}:\n{tracks_message}", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"Топ треки для {artist_name} не найдены.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(bot_tokens.bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

    print("Бот запущен!")
    app.run_polling()

    conn.close()
