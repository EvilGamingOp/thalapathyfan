import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("നിങ്ങൾ ഒരു ഉപയോക്താവിനെ സൂചിപ്പിക്കുന്നതായി തോന്നുന്നില്ല.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("എനിക്ക് ഈ ഉപയോക്താവിനെ കണ്ടെത്താനാകുന്നില്ല")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("അഡ്മിൻ ആണ്... ബാൻ ചെയ്യാൻ പറ്റില്ല!")
        return ""

    if user_id == bot.id:
        message.reply_text("ഞാൻ എന്നെത്തന്നെ ബാൻ ചെയ്യണം എന്നാണോ പറയുന്നത്?")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        reply = "{} ന് ബണ്ണ് കൊടുത്തു വിട്ടിട്ടുണ്ട് !".format(mention_html(member.user.id, member.user.first_name))
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            reply = "{} ന് ബണ്ണ് കൊടുത്തു വിട്ടിട്ടുണ്ട് !".format(mention_html(member.user.id, member.user.first_name))
            message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("കൊള്ളാം, എനിക്ക് ആ ഉപയോക്താവിനെ നിരോധിക്കാൻ കഴിയില്ല.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("നിങ്ങൾ ഒരു ഉപയോക്താവിനെ സൂചിപ്പിക്കുന്നതായി തോന്നുന്നില്ല.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("എനിക്ക് ഈ ഉപയോക്താവിനെ കണ്ടെത്താനാകുന്നില്ല")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("അഡ്മിൻ ആണ്... ബാൻ ചെയ്യാൻ പറ്റില്ല!")
        return ""

    if user_id == bot.id:
        message.reply_text("ഞാൻ എന്നെത്തന്നെ ബാൻ ചെയ്യണം എന്നാണോ പറയുന്നത്?")
        return ""

    if not reason:
        message.reply_text("ഇയാളെ എത്ര സമയം ബാൻ ചെയ്യണം എന്നു പറഞ്ഞില്ലല്ലോ?")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name),
                                     member.user.id,
                                     time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("ബണ്ണ് കൊടുത്തുവിട്ടു! User will be BANNED for {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("ബണ്ണ് കൊടുത്തുവിട്ടു! User will be BANNED for {}.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("കൊള്ളാം, എനിക്ക് ആ ഉപയോക്താവിനെ നിരോധിക്കാൻ കഴിയില്ല.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("എനിക്ക് ഈ ഉപയോക്താവിനെ കണ്ടെത്താനാകുന്നില്ല")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("അഡ്മിൻ ആണ്... പുറത്താക്കാൻ പറ്റില്ല!")
        return ""

    if user_id == bot.id:
        message.reply_text("അതെ ഞാൻ അത് ചെയ്യാൻ പോയില്ല")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("ലവനെ എടുത്തു വെളിയിൽ കളഞ്ഞിട്ടുണ്ട്!")
        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>Admin:</b> {}" \
              "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                           mention_html(user.id, user.first_name),
                                                           mention_html(member.user.id, member.user.first_name),
                                                           member.user.id)
        if reason:
            log += "\n<b>Reason:</b> {}".format(reason)

        return log

    else:
        message.reply_text("കൊള്ളാം, എനിക്ക് ആ ഉപയോക്താവിനെ ചവിട്ടാൻ കഴിയുന്നിലാ.")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("എനിക്ക് സാധിക്കുമെങ്കിൽ ... പക്ഷെ നിങ്ങൾ ഒരു അഡ്മിൻ ആണ്.")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    #if res:
    #    update.effective_message.reply_text("പ്രശ്നമില്ല.")
    #else:
    #    update.effective_message.reply_text("ഹു എനിക്ക് കഴിയില്ല: /")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("എനിക്ക് ഈ ഉപയോക്താവിനെ കണ്ടെത്താനാകുന്നില്ല")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("ഞാൻ ഇവിടെയില്ലെങ്കിൽ ഞാൻ എങ്ങനെ നിരോധിക്കണം?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("ചാറ്റിനുള്ള ആരെയെങ്കിലും നിരോധിക്കാൻ നിങ്ങൾ എന്തിനാണ് ശ്രമിക്കുന്നത്?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("ശരി, ബാൻ മാറ്റിയിട്ടുണ്ട്... ഇനി ഇയാൾക്ക് ഗ്രൂപ്പിൽ ചേരാൻ കഴിയും!")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    return log


__help__ = """
 - /kickme: ആജ്ഞ പുറപ്പെടുവിച്ച ഉപയോക്താവിനെ കുത്തിവയ്ക്കുക

*Admin only:*
 - /ban <userhandle>: ഒരു ഉപയോക്താവിനെ നിരോധിക്കുക. (via handle, or reply)
 - /tban <userhandle> x(m/h/d): x സമയം ഒരു ഉപയോക്താവിനെ നിരോധിക്കുക. (via handle, or reply). m = minutes, h = hours, d = days.
 - /unban <userhandle>: ഒരു ഉപയോക്താവിനെ ഒഴിവാക്കി. (via handle, or reply)
 - /kick <userhandle>: ഒരു ഉപയോക്താവിനെ തട്ടുക, (via handle, or reply)
"""

__mod_name__ = "നിരോധനം"

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
