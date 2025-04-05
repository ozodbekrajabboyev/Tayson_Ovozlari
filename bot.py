from aiogram import Bot, Dispatcher
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart,Command, or_f
from aiogram import F, types
from aiogram.types import (Message,InlineQuery,InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultCachedVoice)
from data import config
from aiogram.enums import ParseMode
import asyncio
import logging
import sys
from menucommands.set_bot_commands  import set_default_commands
from baza.sqlite import Database
from filterss.admin import IsBotAdminFilter
from filterss.check_sub_channel import IsCheckSubChannels
from keyboard_buttons import admin_keyboard
from keyboard_buttons.admin_keyboard import home_button
from aiogram.fsm.context import FSMContext #new
from states.reklama import Adverts, AudioState, AdminMSG
from aiogram.utils.keyboard import InlineKeyboardBuilder
import time
from aiogram.fsm.context import FSMContext

ADMINS = config.ADMINS
TOKEN = config.BOT_TOKEN
from aiogram.filters import Command, CommandObject  
CHANNELS = config.CHANNELS

dp = Dispatcher()


commands = ["/start", "/about", "/help", "/admin"]

# Start command
@dp.message(CommandStart())
async def start_command(message:Message,state:FSMContext):
 
    full_name = message.from_user.full_name
    telegram_id = message.from_user.id
    try:
        db.add_user(full_name=full_name,telegram_id=telegram_id)
        await message.answer(text=f"Assalomu alaykum {full_name}, botimizga xush kelibsiz🙂\nBu bot orqali siz hohlagan ovozingizni topishingiz mumkin!✅", reply_markup = home_button)
        await state.clear()
    except:
        await message.answer(text=f"Assalomu alaykum {full_name}. Xush kelibsiz 😊", reply_markup = home_button)
        await state.clear()


# Help command
@dp.message(Command("help"))
async def help_commands(message:Message):
    await message.answer("""
🔥Buyruqlar 
Botdan foydalanish ...
/about - Bot haqida 
/start - Botni ishga tushurish
                         
Admin bilan bog'lanmoqchi bo'lsangiz \n👤Admin tugmasini bosing va\n✉️ Xabaringizni yozib qoldiring!""")

# About command
@dp.message(Command("about"))
async def about_commands(message:Message):
    await message.answer("Bot dan shikoyatingiz yoki taklifingiz bo'lsa📜\n👤Admin tugmasini bosing va \nxabaringizni yozib qoldiring✅\n\nBotdan foydalanish tartibi👇🏻\n👉🏻@voise_ovozqani_bot yozib o'zingizga kerakli ovozlarni toping🙂")



# Inline query search(Searching audio messages inline)
@dp.inline_query()
async def inline_voice_search(inline_query: InlineQuery):
    title = inline_query.query.strip()

    results = []
    print("***************",title,"***************")
    if not title:
        # No query entered, offer all audio files
        try:
            all_audios = db.select_all_audios()
            print("***************",all_audios,"***************")
            for item in all_audios:
                voice_file_id = item[1]
                file_id = item[0]
                try:
                    
                    stats = db.get_voice_stats(file_id)
                    usage_count = stats['usage_count'] if stats else 0
                    
                    formatted_title = f"{item[2]} 🎵{usage_count}"

                    keyboard1 = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Barcha Ovozlar", url="https://t.me/Tayson_ovozlari_bot")]
                    ])
                    result = InlineQueryResultCachedVoice(
                        id=str(item[0]), 
                        voice_file_id=voice_file_id, 
                        title=formatted_title,
                        caption = item[2],
                        reply_markup = keyboard1
                    )
                    results.append(result)
                except Exception as e:
                    print(f"Error creating InlineQueryResultCachedVoice for ID {item[0]} with voice_file_id {voice_file_id}: {e}")
                
        except Exception as e:
            print(f"Error fetching all audio files: {e}")
    else:
        # Query entered, search for matching audio files
        try:
            audiolar = db.search_audios_title(title)
            for audio in audiolar:
                voice_file_id = audio[1]
                file_id = audio[0]
                if voice_file_id and isinstance(voice_file_id, str) and voice_file_id.startswith("AwACAg"):
                    try:
                        
                        stats = db.get_voice_stats(audio_id = audio[0])
                        usage_count = stats['usage_count'] if stats else 0

                        formatted_title = f"{audio[2]} 🎵{usage_count}"
                        keyboard1 = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="Barcha Ovozlar", url="https://t.me/Tayson_ovozlari_bot")]
                        ])
                        result = InlineQueryResultCachedVoice(
                            id=str(audio[0]),
                            voice_file_id=voice_file_id,
                            title=formatted_title,
                            caption = audio[2],
                            reply_markup = keyboard1
                        )
                        results.append(result)
                    except Exception as e:
                        print(f"Error creating InlineQueryResultCachedVoice for ID {audio[0]} with voice_file_id {voice_file_id}: {e}")
                else:
                    print(f"Invalid or malformed voice_file_id: {voice_file_id}")
        except Exception as e:
            print(f"Error searching audio titles: {e}")

    if not results:
        await inline_query.answer(results=[], cache_time=0, switch_pm_text="No results found", switch_pm_parameter="start")
    else:
        try:
            await inline_query.answer(results=results, cache_time=0)
        except Exception as e:
            print(f"Error sending inline query answer: {e}")
            

# Tanlangan audio ustida ishlash

from aiogram.types import ChosenInlineResult

@dp.chosen_inline_result()
async def chosen_inline_result(chosen_result: ChosenInlineResult):
    result_id = chosen_result.result_id  # bu Audio.id sifatida berilgan bo'lishi kerak
    user_id = chosen_result.from_user.id

    # result_id str bo'lishi mumkin, uni int ga o'tkazamiz
    try:
        audio_id = int(result_id)
    except ValueError:
        print(f"Invalid audio_id: {result_id}")
        return

    # Audio ma'lumotlarini olamiz
    audio_info = db.get_audio_by_id(audio_id)  # db.get_audio_by_id() sizda bo'lishi kerak

    if audio_info:
        db.increment_voice_usage(audio_id)  # audio_id orqali statistikani yangilaymiz
        print(f"User {user_id} selected voice {audio_id}")





# Top 10 ovozlarni chiqarish
from aiogram import F
from aiogram.types import Message

@dp.message(F.text == "/stats")
async def show_voice_stats(message: Message):
    # Eng ko'p ishlatilgan 10 ta ovoz
    top_voices = await db.get_top_voices(10)
    
    if not top_voices:
        await message.answer("Hali hech qanday statistik ma'lumot yo'q.")
        return
    
    response = ["🏆 Eng ko'p ishlatilgan ovozlar:\n"]
    for idx, (title, count, last_used) in enumerate(top_voices, 1):
        response.append(f"{idx}. {title} - {count} marta\nSo'ngi foydalanish: {last_used}")
    
    await message.answer("\n".join(response))






#kanalga obuna boshlanadi
@dp.message(IsCheckSubChannels())
async def kanalga_obuna(message:Message):
    text = ""
    inline_channel = InlineKeyboardBuilder()
    for index,channel in enumerate(CHANNELS):
        ChatInviteLink = await bot.create_chat_invite_link(channel)
        inline_channel.add(InlineKeyboardButton(text=f"{index+1}-kanal",url=ChatInviteLink.invite_link))
    inline_channel.adjust(1,repeat=True)
    button = inline_channel.as_markup()
    await message.answer(f"{text} kanallarga azo bo'ling!",reply_markup=button)


@dp.message(Command("admin"),IsBotAdminFilter(ADMINS))
async def is_admin(message:Message):
    await message.answer(text="Admin menu",reply_markup=admin_keyboard.admin_button)



@dp.message(F.text=="Foydalanuvchilar soni",IsBotAdminFilter(ADMINS))
async def users_count(message:Message):
    counts = db.count_users()
    text = f"Botimizda {counts[0]} ta foydalanuvchi bor"
    await message.answer(text=text)



@dp.message(F.text=="Reklama yuborish",IsBotAdminFilter(ADMINS))
async def advert_dp(message:Message,state:FSMContext):
    await state.set_state(Adverts.adverts)
    await message.answer(text="Reklama yuborishingiz mumkin!")


@dp.message(Adverts.adverts)
async def send_advert(message:Message,state:FSMContext):
    
    message_id = message.message_id
    from_chat_id = message.from_user.id
    users = db.all_users_id()
    count = 0
    for user in users:
        try:
            await bot.copy_message(chat_id=user[0],from_chat_id=from_chat_id,message_id=message_id)
            count += 1
        except:
            pass
        time.sleep(0.5)
    
    await message.answer(f"Reklama {count}ta foydalanuvchiga yuborildi!")
    await state.clear()


#audio qo'shish


@dp.message(F.text=="audio qo'shish",IsBotAdminFilter(ADMINS))
async def auido_adds(message:Message,state:FSMContext):
    await message.answer("Audio nomini kiriting!")
    await state.set_state(AudioState.title)



@dp.message(F.text,AudioState.title)
async def auido_title(message:Message,state:FSMContext):
    await message.answer("Audio yuboring!")
    title = message.text
    await state.set_state(AudioState.voice_file_id)
    await state.update_data(title=title)


@dp.message(F.voice,AudioState.voice_file_id)
async def auido_voice(message:Message,state:FSMContext):
    data = await state.get_data()
    title = data.get("title")
    voice_file_id = message.voice.file_id
    db.add_audio(voice_file_id=voice_file_id,title=title)

    await message.answer("Tabriklaymiz Audio muvaffaqiyatli bazaga qo'shildi!✅")
    await state.clear()

#-----------------------=========
from aiogram import Bot,Dispatcher,types
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message,CallbackQuery,ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
import logging
import sys
from keyboard_buttons import admin_keyboard
from menucommands.set_bot_commands  import set_default_commands
from aiogram.fsm.state import StatesGroup, State


class AdminStates(StatesGroup):
    waiting_for_admin_message = State()
    waiting_for_reply_message = State()


# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define admin states
class AdminStates(StatesGroup):
    waiting_for_admin_message = State()
    waiting_for_reply_message = State()

# Function to create inline keyboard for reply
def create_inline_keyboard(user_id):
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(
        text="Javob berish",
        callback_data=f"reply:{user_id}"
    )


    return keyboard_builder.as_markup()



# Admin message handler
@dp.message(F.text == "👤Admin bilan bog'lanish")
async def admin_message(message: Message, state: FSMContext):
    await message.answer("👨‍💼Admin uchun xabar yuborishingiz mumkin. Xabaringizni kiriting!")
    await state.set_state(AdminStates.waiting_for_admin_message)

# Admin message handler
@dp.message(AdminStates.waiting_for_admin_message, F.content_type.in_([
    ContentType.TEXT, ContentType.AUDIO, ContentType.VOICE, ContentType.VIDEO,
    ContentType.PHOTO, ContentType.ANIMATION, ContentType.STICKER, 
    ContentType.LOCATION, ContentType.DOCUMENT, ContentType.CONTACT,
    ContentType.VIDEO_NOTE
]))

async def handle_admin_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ""  # Some users may not have a last name

    # Use username if available, otherwise use first name + last name
    if username:
        user_identifier = f"@{username}"
    else:
        user_identifier = f"{first_name} {last_name}".strip()  # Remove any extra spaces




    video_note = message.video_note
    inline_keyboard = create_inline_keyboard(user_id)
    for admin_id in ADMINS:
        try:
            if video_note:
                print('adfs', message.video_note.file_id)
                # Echo the video note back to the user
                await bot.send_video_note(
                    admin_id,
                    video_note.file_id,
                    reply_markup=inline_keyboard
                )
            elif message.text:
                await bot.send_message(
                    admin_id,
                    f"👤Foydalanuvchi: {user_identifier}\n📜Xabar: {message.text}",
                    reply_markup=inline_keyboard
                )
            elif message.audio:
                await bot.send_audio(
                    admin_id,
                    message.audio.file_id,
                    caption=f"👤Foydalanuvchi: {user_identifier}\n🎙Audio xabar",
                    reply_markup=inline_keyboard
                )
            elif message.voice:
                await bot.send_voice(
                    admin_id,
                    message.voice.file_id,
                    caption=f"👤Foydalanuvchi: {user_identifier}\n⏺Voice xabar",
                    reply_markup=inline_keyboard
                )
            elif message.video:
                await bot.send_video(
                    admin_id,
                    message.video.file_id,
                    caption=f"👤Foydalanuvchi: {user_identifier}\n▶️Video xabar",
                    reply_markup=inline_keyboard
                )
            elif message.photo:
                await bot.send_photo(
                    admin_id,
                    message.photo[-1].file_id,  # using the highest resolution photo
                    caption=f"👤Foydalanuvchi: {user_identifier}\n🏞Rasm xabar",
                    reply_markup=inline_keyboard
                )
            elif message.animation:
                await bot.send_animation(
                    admin_id,
                    message.animation.file_id,
                    caption=f"👤Foydalanuvchi: {user_identifier}\n📜GIF xabar",
                    reply_markup=inline_keyboard
                )
            elif message.sticker:
                await bot.send_sticker(
                    admin_id,
                    message.sticker.file_id,
                    reply_markup=inline_keyboard
                )
            elif message.location:
                await bot.send_location(
                    admin_id,
                    latitude=message.location.latitude,
                    longitude=message.location.longitude,
                    reply_markup=inline_keyboard
                )
            elif message.document:
                await bot.send_document(
                    admin_id,
                    message.document.file_id,
                    caption=f"👤Foydalanuvchi: {user_identifier}\n🗂Hujjat xabar",


                    reply_markup=inline_keyboard
                )
            elif message.contact:
                await bot.send_contact(
                    admin_id,
                    phone_number=message.contact.phone_number,
                    first_name=message.contact.first_name,
                    last_name=message.contact.last_name or "",
                    reply_markup=inline_keyboard
                )
        except Exception as e:
            logging.error(f"Error sending message to admin {admin_id}: {e}")

    await state.clear()
    await bot.send_message(user_id, "Adminga xabaringiz yuborildi. Tez orada admin sizga javob berishi yoki bog'lanishi mumkin!✅")

# Callback query handler for the reply button
@dp.callback_query(lambda c: c.data.startswith('reply:'))
async def process_reply_callback(callback_query: CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split(":")[1])
    await callback_query.message.answer(f"Foydalanuvchi uchun xabaringizni kiriting!")
    await state.update_data(reply_user_id=user_id)
    await state.set_state(AdminStates.waiting_for_reply_message)
    await callback_query.answer()





# Handle admin reply and send it back to the user
@dp.message(AdminStates.waiting_for_reply_message)
async def handle_admin_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    original_user_id = data.get('reply_user_id')

    if original_user_id:
        try:
            if message.text:
                await bot.send_message(original_user_id, f"Admin sizga javob yubordi ✅ \n 📜Xabar: {message.text}")
            elif message.voice:
                await bot.send_voice(original_user_id, message.voice.file_id)

            elif message.video_note:
                await bot.send_video_note(original_user_id, message.video_note.file_id)

            elif message.audio:
                await bot.send_audio(original_user_id, message.audio.file_id)
            
            elif message.sticker:
                await bot.send_sticker(original_user_id, message.sticker.file_id)
            
            elif message.video:
                await bot.send_video(original_user_id, message.video.file_id)
            
            
            usr = db.select_user(telegram_id = original_user_id)
            if usr:
                fname = usr[0]  
            else:
                logger.error("Bunday telegram_id ga ega user topilamdi!!!")
            await bot.send_message(message.from_user.id, f"Foydalanuvchi: {fname} \n Admin: {message.from_user.full_name}\n Xabaringiz muvaffaqiyatli yuborildi!✅")           
            await state.clear()  # Clear state after sending the reply
        except Exception as e:
            logger.error(f"Error sending reply to user {original_user_id}: {e}")
            await message.reply("Xatolik: Javob yuborishda xato yuz berdi.")
    else:
        await message.reply("Xatolik: Javob yuborish uchun foydalanuvchi ID topilmadi.")



@dp.startup()
async def on_startup_notify(bot: Bot):
    for admin in ADMINS:
        try:
            await bot.send_message(chat_id=int(admin),text="Bot ishga tushdi")
        except Exception as err:
            logging.exception(err)


#bot ishga tushganini xabarini yuborish
@dp.shutdown()
async def off_startup_notify(bot: Bot):
    for admin in ADMINS:
        try:
            await bot.send_message(chat_id=int(admin),text="Bot ishdan to'xtadi!")
        except Exception as err:
            logging.exception(err)


def setup_middlewares(dispatcher: Dispatcher, bot: Bot) -> None:
    """MIDDLEWARE"""
    from middlewares.throttling import ThrottlingMiddleware

    # Spamdan himoya qilish uchun klassik ichki o'rta dastur. So'rovlar orasidagi asosiy vaqtlar 0,5 soniya
    dispatcher.message.middleware(ThrottlingMiddleware(slow_mode_delay=0.5))

async def main() -> None:
    global bot,db
    bot = Bot(TOKEN)
    db = Database(path_to_db="data/main.db")
    db.create_table_users()
    db.create_table_audios()
    db.create_table_voice_stats()
    await set_default_commands(bot)
    await dp.start_polling(bot)
    setup_middlewares(dispatcher=dp, bot=bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    asyncio.run(main())