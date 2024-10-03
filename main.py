import os
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from moviepy.editor import VideoFileClip

TOKEN = 'токен тг бота'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет, {user.mention_html()}! Я бот, созданный m0ln1z. Отправь мне видео, и я извлеку из него аудио)))",
        reply_markup=ForceReply(selective=True),
    )
    print("Команда /start получена от пользователя:", user.username)

async def extract_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.video:
        print("Получено видео:", update.message.video.file_id)

        video_file = await update.message.video.get_file()
        video_path = f"video_{update.message.video.file_id}.mp4"
        
        await video_file.download_to_drive(video_path)

        audio_path = f"audio_{update.message.video.file_id}.mp3"

        try:
            print("Извлечение аудио...")
            video = VideoFileClip(video_path)
            video.audio.write_audiofile(audio_path)
            video.close()

            print("Аудио успешно извлечено.")
            await update.message.reply_audio(audio=open(audio_path, 'rb'))
        except Exception as e:
            print("Произошла ошибка при извлечении аудио:", e)
            await update.message.reply_text(f"Произошла ошибка: {e}")
        finally:
            if os.path.exists(video_path):
                os.remove(video_path)
                print("Временный файл видео удален.")
            if os.path.exists(audio_path):
                os.remove(audio_path)
                print("Временный файл аудио удален.")
    else:
        await update.message.reply_text("Пожалуйста, отправь видеофайл.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, extract_audio))

    print("Бот запущен. Ожидание сообщений...")
    app.run_polling()
