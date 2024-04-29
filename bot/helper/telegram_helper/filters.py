#!/usr/bin/env python3
from typing import Union, AsyncContextManager, Callable, Coroutine, Any

import pyrogram.filters
from pyrogram.enums import ChatType
from pyrogram.errors import ChatAdminRequired

from bot import user_data, OWNER_ID
from bot.helper.telegram_helper.message_utils import chat_info


class CustomFilters:

    async def owner_filter(self, _: Any, message: Union[pyrogram.types.Message, pyrogram.types.CallbackQuery]) -> bool:
        """Check if the user is the owner of the bot."""
        user = message.from_user or message.sender_chat
        return user.id == OWNER_ID

    owner = pyrogram.filters.create(owner_filter)

    async def authorized_user(self, _: Any, message: Union[pyrogram.types.Message, pyrogram.types.CallbackQuery]) -> bool:
        """Check if the user is authorized to use the bot."""
        user = message.from_user or message.sender_chat
        user_id = user.id

        if user_id == OWNER_ID or (
            user_id in user_data
            and (user_data[user_id].get('is_auth', False) or user_data[user_id].get('is_sudo', False))
        ):
            return True

        chat_id = message.chat.id
        if chat_id in user_data and user_data[chat_id].get('is_auth', False):
            topic_ids = user_data[chat_id].get('topic_ids', [])
            if not topic_ids:
                return True

            is_forum = message.reply_to_message
            if (
                not is_forum.text and not is_forum.caption and is_forum.id in topic_ids
                or (is_forum.text or is_forum.caption)
                and (
                    not is_forum.reply_to_top_message_id and is_forum.reply_to_message_id in topic_ids
                    or is_forum.reply_to_top_message_id in topic_ids
                )
            ):
                return True

        return False

    authorized = pyrogram.filters.create(authorized_user)

    async def authorized_user_setting(self, _: Any, message: Union[pyrogram.types.Message, pyrogram.types.CallbackQuery]) -> bool:
        """Check if the user is authorized to change settings."""
        user_id = (message.from_user or message.sender_chat).id
        chat_id = message.chat.id

        if (
            user_id == OWNER_ID
            or (user_id in user_data and (user_data[user_id].get('is_auth', False) or user_data[user_id].get('is_sudo', False)))
            or (chat_id in user_data and user_data[chat_id].get('is_auth', False))
        ):
            return True

        if message.chat.type == ChatType.PRIVATE:
            for channel_id in user_data:
                if not (user_data[channel_id].get('is_auth') and str(channel_id).startswith('-100')):
                    continue

                try:
                    if await chat_info(str(channel_id)).get_member(user_id):
                        return True
                except pyrogram.errors.ChatAdminRequired:
                    continue

        return False

    authorized_user_setting = pyrogram.filters.create(authorized_user_setting)

    async def sudo_user(self, _: Any, message: Union[pyrogram.types.Message, pyrogram.types.CallbackQuery]) -> bool:
        """Check if the user is a sudo user."""
        user = message.from_user or message.sender_chat
        user_id = user.id
        return user_id == OWNER_ID or (user_id in user_data and user_data[user_id].get('is_sudo'))

    sudo = pyrogram.filters.create(sudo_user)

    async def blacklist_user(self, _: Any, message: Union[pyrogram.types.Message, pyrogram.types.CallbackQuery]) -> bool:
        """Check if the user is blacklisted."""
        user = message.from_user or message.sender_chat
        user_id = user.id
        return user_id != OWNER_ID and user_id in user_data and user_data[user_id].get('is_blacklist')

    blacklisted = pyrogram.filters.create(blacklist_user)
