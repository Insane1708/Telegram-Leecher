import logging
from PIL import Image
from asyncio import sleep
from os import path as ospath
from datetime import datetime
from pyrogram.errors import FloodWait
from colab_leecher.utility.variables import BOT, Transfer, BotTimes, Messages, MSG, Paths
from colab_leecher.utility.helper import sizeUnit, fileType, getTime, status_bar, thumbMaintainer, videoExtFix

# Import USER_STRING from main.py
try:
    from main import USER_STRING
except ImportError:
    USER_STRING = None

async def progress_bar(current, total):
    global status_msg, status_head
    upload_speed = 4 * 1024 * 1024
    elapsed_time_seconds = (datetime.now() - BotTimes.task_start).seconds
    if current > 0 and elapsed_time_seconds > 0:
        upload_speed = current / elapsed_time_seconds
    eta = (Transfer.total_down_size - current - sum(Transfer.up_bytes)) / upload_speed
    percentage = (current + sum(Transfer.up_bytes)) / Transfer.total_down_size * 100
    await status_bar(
        down_msg=Messages.status_head,
        speed=f"{sizeUnit(upload_speed)}/s",
        percentage=percentage,
        eta=getTime(eta),
        done=sizeUnit(current + sum(Transfer.up_bytes)),
        left=sizeUnit(Transfer.total_down_size),
        engine="Pyrofork 💥",
    )

async def upload_file(file_path, real_name):
    global Transfer, MSG
    BotTimes.task_start = datetime.now()
    caption = f"<{BOT.Options.caption}>{BOT.Setting.prefix} {real_name} {BOT.Setting.suffix}</{BOT.Options.caption}>"
    type_ = fileType(file_path)

    f_type = type_ if BOT.Options.stream_upload else "document"

    # Upload the file
    try:
        if USER_STRING:
            # Use USER_STRING for uploading
            from pyrogram import Client
            user_client = Client("user_session", api_id=BOT.Options.api_id, api_hash=BOT.Options.api_hash, session_string=USER_STRING)
            await user_client.start()

            if f_type == "video":
                file_path = videoExtFix(file_path) if not BOT.Options.stream_upload else file_path
                thmb_path, seconds = thumbMaintainer(file_path)
                with Image.open(thmb_path) as img:
                    width, height = img.size

                MSG.sent_msg = await user_client.send_video(
                    chat_id=MSG.sent_msg.chat.id,
                    video=file_path,
                    supports_streaming=True,
                    width=width,
                    height=height,
                    caption=caption,
                    thumb=thmb_path,
                    duration=int(seconds),
                    progress=progress_bar,
                )

            elif f_type == "audio":
                thmb_path = None if not ospath.exists(Paths.THMB_PATH) else Paths.THMB_PATH
                MSG.sent_msg = await user_client.send_audio(
                    chat_id=MSG.sent_msg.chat.id,
                    audio=file_path,
                    caption=caption,
                    thumb=thmb_path,
                    progress=progress_bar,
                )

            elif f_type == "document":
                thmb_path = Paths.THMB_PATH if ospath.exists(Paths.THMB_PATH) else (thumbMaintainer(file_path)[0] if type_ == "video" else None)
                MSG.sent_msg = await user_client.send_document(
                    chat_id=MSG.sent_msg.chat.id,
                    document=file_path,
                    caption=caption,
                    thumb=thmb_path,
                    progress=progress_bar,
                )

            elif f_type == "photo":
                MSG.sent_msg = await user_client.send_photo(
                    chat_id=MSG.sent_msg.chat.id,
                    photo=file_path,
                    caption=caption,
                    progress=progress_bar,
                )

            await user_client.stop()

        else:
            # Default way to upload
            if f_type == "video":
                file_path = videoExtFix(file_path) if not BOT.Options.stream_upload else file_path
                thmb_path, seconds = thumbMaintainer(file_path)
                with Image.open(thmb_path) as img:
                    width, height = img.size

                MSG.sent_msg = await MSG.sent_msg.reply_video(
                    video=file_path,
                    supports_streaming=True,
                    width=width,
                    height=height,
                    caption=caption,
                    thumb=thmb_path,
                    duration=int(seconds),
                    progress=progress_bar,
                    reply_to_message_id=MSG.sent_msg.id,
                )

            elif f_type == "audio":
                thmb_path = None if not ospath.exists(Paths.THMB_PATH) else Paths.THMB_PATH
                MSG.sent_msg = await MSG.sent_msg.reply_audio(
                    audio=file_path,
                    caption=caption,
                    thumb=thmb_path,
                    progress=progress_bar,
                    reply_to_message_id=MSG.sent_msg.id,
                )

            elif f_type == "document":
                thmb_path = Paths.THMB_PATH if ospath.exists(Paths.THMB_PATH) else (thumbMaintainer(file_path)[0] if type_ == "video" else None)
                MSG.sent_msg = await MSG.sent_msg.reply_document(
                    document=file_path,
                    caption=caption,
                    thumb=thmb_path,
                    progress=progress_bar,
                    reply_to_message_id=MSG.sent_msg.id,
                )

            elif f_type == "photo":
                MSG.sent_msg = await MSG.sent_msg.reply_photo(
                    photo=file_path,
                    caption=caption,
                    progress=progress_bar,
                    reply_to_message_id=MSG.sent_msg.id,
                )

        Transfer.sent_file.append(MSG.sent_msg)
        Transfer.sent_file_names.append(real_name)

    except FloodWait as e:
        await sleep(e.x)  # Wait for the specified time before trying again
        await upload_file(file_path, real_name)
    except Exception as e:
        logging.error(f"Error When Uploading : {e}")
