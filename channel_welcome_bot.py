"""
Telegram 频道 - 新成员欢迎 Bot（3C 电子产品电商）
================================================
功能：
1. 监听频道新成员加入事件
2. 把当天/当批加入的新成员名字先攒起来
3. 定时（比如每小时）批量发一条欢迎消息到频道，附带产品/品牌图片
4. 消息里可以带按钮，引导去店铺

使用前准备：
1. Bot 必须被加为频道管理员，且至少要有"添加管理员"里的基础权限
   （频道设置 -> Administrators -> Add Admin -> 搜索你的 bot）
2. 安装依赖：pip install python-telegram-bot --break-system-packages
3. 用环境变量传入 Token，不要写死在代码里（见下方说明）
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ChatMemberHandler,
    ContextTypes,
)

# ========== 基本配置 ==========

# 建议用环境变量传入，而不是写死在代码里（Railway 部署时在 Variables 里设置 BOT_TOKEN）
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8212847031:AAHZBCFwmN-SwexiXGjsWXHa5kuU2NTbmyE")

# 你的频道 ID 或 @username（比如 "@your_channel" 或者数字 ID 如 -1001234567890）
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@onehima")

# 欢迎消息配图（可以是产品/品牌 banner 图，网络 URL 或本地路径）
WELCOME_PHOTO = "https://drive.google.com/uc?export=view&id=1wI7GRD9QOP6JNp_j51ixpbAcsafiqpi4"

# 店铺链接
SHOP_LINK = "https://www.1hima.com/en-np?aff=f1bf9c1ca5"

# 多久批量发一次欢迎消息（秒），比如 3600 = 每小时汇总一次
BATCH_INTERVAL_SECONDS = 3600

# ========== 逻辑部分，一般不需要改 ==========

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# 暂存这一批新加入的成员名字
pending_new_members = []


async def on_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """监听频道成员状态变化，判断是否是"新加入" """
    result = update.chat_member
    if result is None:
        return

    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status

    # 从 "left"/"kicked"/"restricted" 变成 "member" 视为新加入
    if old_status in ("left", "kicked") and new_status == "member":
        user = result.new_chat_member.user
        name = user.full_name or user.username or f"用户{user.id}"
        pending_new_members.append(name)
        logger.info(f"检测到新成员加入：{name}")


async def send_batch_welcome(context: ContextTypes.DEFAULT_TYPE):
    """定时任务：把攒到的新成员名字批量发送一条欢迎消息"""
    global pending_new_members

    if not pending_new_members:
        return  # 这段时间没有新人，不发消息

    names = "、".join(pending_new_members)
    caption = (
        f"🎉 <b>欢迎新朋友加入！</b>\n\n"
        f"欢迎：{names}\n\n"
        f"感谢关注，这里持续更新优质 3C 电子产品，"
        f"新品、优惠信息第一时间同步给大家！"
    )

    keyboard = [[InlineKeyboardButton("🛒 去逛店铺", url=SHOP_LINK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=WELCOME_PHOTO,
        caption=caption,
        parse_mode="HTML",
        reply_markup=reply_markup,
    )

    logger.info(f"已发送批量欢迎消息，成员：{names}")
    pending_new_members = []  # 清空，等待下一批


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 注册成员状态变化监听
    app.add_handler(ChatMemberHandler(on_chat_member_update, ChatMemberHandler.CHAT_MEMBER))

    # 注册定时批量发送任务
    app.job_queue.run_repeating(
        send_batch_welcome,
        interval=BATCH_INTERVAL_SECONDS,
        first=BATCH_INTERVAL_SECONDS,
    )

    logger.info("Bot 已启动，监听频道新成员中...")
    # 关键：allowed_updates 必须包含 chat_member，否则收不到成员变化事件
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
