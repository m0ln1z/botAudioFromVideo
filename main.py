import os
import asyncio
from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import speech_recognition as sr

TOKEN = 'ваш тг токен'

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

            if os.path.exists(audio_path):
                print("Аудио успешно извлечено.")
                await update.message.reply_audio(audio=open(audio_path, 'rb'))
                
                keyboard = [
                    [
                        InlineKeyboardButton("Да", callback_data='yes'),
                        InlineKeyboardButton("Нет", callback_data='no')
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Хочешь преобразовать аудио в текст?", reply_markup=reply_markup)
                
                context.user_data['audio_path'] = audio_path
                context.user_data['delete_timer'] = asyncio.create_task(delete_audio_after_delay(audio_path, 60))
            else:
                print("Ошибка: Аудио файл не создан.")
                await update.message.reply_text("Произошла ошибка: Аудио файл не создан.")

        except Exception as e:
            print("Произошла ошибка при извлечении аудио:", e)
            await update.message.reply_text(f"Произошла ошибка: {e}")
        finally:
            if os.path.exists(video_path):
                os.remove(video_path)
                print("Временный файл видео удален.")

async def delete_audio_after_delay(audio_path, delay):
    await asyncio.sleep(delay)
    if os.path.exists(audio_path):
        os.remove(audio_path)
        print(f"Временный файл аудио {audio_path} удален через {delay} секунд.")

async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    text = query.data
    audio_path = context.user_data.get('audio_path')

    if text == 'yes':
        if audio_path:
            try:
                print("Начинаем преобразование аудио в текст...")
                sound = AudioSegment.from_mp3(audio_path)
                wav_path = audio_path.replace('.mp3', '.wav')
                sound.export(wav_path, format="wav")

                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_path) as source:
                    audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio, language='ru-RU')
                    await query.message.reply_text(f"Текст: {text}")

                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    print(f"Временный файл аудио {audio_path} удален после преобразования.")
                    
                if 'delete_timer' in context.user_data:
                    context.user_data['delete_timer'].cancel()
                    del context.user_data['delete_timer']
            except Exception as e:
                await query.message.reply_text(f"Произошла ошибка при преобразовании: {e}")
        else:
            await query.message.reply_text("Аудио файл не найден.")
    elif text == 'no':
        await query.message.reply_text("Хорошо! Если что отправляй видео , преобразую в аудио сразу же)")
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"Временный файл аудио {audio_path} удален по запросу пользователя.")
        if 'delete_timer' in context.user_data:
            context.user_data['delete_timer'].cancel()
            del context.user_data['delete_timer']
    else:
        await query.message.reply_text("Ответь Да или Нет.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, extract_audio))
    app.add_handler(CallbackQueryHandler(handle_response))

    print("Бот запущен. Ожидание сообщений...")
    app.run_polling()
