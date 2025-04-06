from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


admin_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Foydalanuvchilar soni"),
            KeyboardButton(text="Reklama yuborish"),
        ],
        [
            KeyboardButton(text="audio qo'shish"),
        ],
        
    ],
   resize_keyboard = True,
   input_field_placeholder="Menudan birini tanlang"
)

home_button = ReplyKeyboardMarkup(
    keyboard = [
        [
            KeyboardButton(text = "🔊Barcha ovozlar"),
            KeyboardButton(text = "🔝 10 Ovozlar"),   
        ],
        [   
            KeyboardButton(text = "👤Admin bilan bog'lanish"),
        ]
    ],
    resize_keyboard = True,
    input_field_placeholder = "Quyidagilardan birini tanlang!"
)