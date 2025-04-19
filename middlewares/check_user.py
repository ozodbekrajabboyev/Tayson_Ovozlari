from aiogram import BaseMiddleware
from aiogram.types import InlineQuery
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from typing import Callable, Dict, Any, Awaitable
from baza.sqlite import Database
from aiogram import Bot

class CheckUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[InlineQuery, Dict[str, Any]], Awaitable[Any]],
        event: InlineQuery,
        data: Dict[str, Any]
    ) -> Any:
        from_user_id = event.from_user.id
        bot: Bot = data['bot']  # aiogram v3'da bot instance data dict ichida bo'ladi

        db = Database(path_to_db="data/main.db")
        user_exists = db.check_user_exists(from_user_id)

        if not user_exists:
            await event.answer(
                results=[],
                switch_pm_text="👉 Botni ishga tushirish uchun bosing",
                switch_pm_parameter="start",
                cache_time=0
            )
            return

        # Check if the user has not blocked the bot
        try:
            await bot.send_chat_action(chat_id=from_user_id, action="typing")
        except (TelegramForbiddenError, TelegramBadRequest):
            # Foydalanuvchi botni bloklagan yoki unga yozib bo'lmaydi
            await event.answer(
                results=[],
                switch_pm_text="Iltimos, botni blokdan chiqarib qo'ying!",
                switch_pm_parameter="start",
                cache_time=0
            )
            return

        return await handler(event, data)
