
import os
import asyncio
from collections import defaultdict, deque

from pyrogram import Client, filters
from pyrogram.types import Message

from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream


# =========================================================
# Telegram Client
# =========================================================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "music_session")

app = Client(
    SESSION_NAME,
    api_id=API_ID,
    api_hash=API_HASH,
)

# Voice Chat client
voice = PyTgCalls(app)


# =========================================================
# Music Queue
# =========================================================

queues = defaultdict(deque)
current_track = {}


def get_queue(chat_id):
    return queues[chat_id]


# =========================================================
# PLAY
# =========================================================

async def play_file(chat_id: int, file_path: str, title: str = "Unknown"):
    queue = get_queue(chat_id)

    # If another song is playing, add this one to queue
    if chat_id in current_track:
        queue.append((file_path, title))
        return False

    current_track[chat_id] = {
        "file": file_path,
        "title": title,
    }

    try:
        await voice.play(
            chat_id,
            MediaStream(
                file_path,
                video_flags=MediaStream.Flags.IGNORE,
            ),
        )
        return True

    except Exception:
        current_track.pop(chat_id, None)
        raise


# =========================================================
# /play
# Reply to an audio file
# =========================================================

@app.on_message(filters.command("play") & filters.group)
async def play_command(client: Client, message: Message):

    if not message.reply_to_message:
        await message.reply(
            "🎵 تکایە `/play` لەسەر فایلێکی موزیک Reply بکە."
        )
        return

    replied = message.reply_to_message

    if not replied.audio and not replied.document:
        await message.reply(
            "❌ تکایە Reply لەسەر فایلێکی Audio/Music بکە."
        )
        return

    status = await message.reply("⏳ موزیکەکە ئامادە دەکەم...")

    try:

        os.makedirs("downloads", exist_ok=True)

        file_name = (
            replied.audio.file_name
            if replied.audio
            else replied.document.file_name
        )

        if not file_name:
            file_name = f"{message.chat.id}_{replied.id}.mp3"

        safe_name = os.path.basename(file_name)
        file_path = os.path.join(
            "downloads",
            f"{message.chat.id}_{replied.id}_{safe_name}"
        )

        await client.download_media(
            replied,
            file_name=file_path
        )

        title = safe_name

        started = await play_file(
            message.chat.id,
            file_path,
            title
        )

        if started:
            await status.edit_text(
                f"🎵 **ئێستا پڵەی دەکرێت:**\n\n"
                f"🎶 {title}"
            )
        else:
            await status.edit_text(
                f"➕ زیادکرا بۆ Queue:\n\n🎶 {title}"
            )

    except Exception as e:

        await status.edit_text(
            "❌ نەتوانرا موزیکەکە پڵەی بکرێت.\n\n"
            f"`{str(e)[:500]}`"
        )


# =========================================================
# /pause
# =========================================================

@app.on_message(filters.command("pause") & filters.group)
async def pause_command(client, message):

    try:
        await voice.pause(message.chat.id)

        await message.reply("⏸ موزیک وەستا.")

    except Exception as e:
        await message.reply(
            f"❌ نەتوانرا pause بکرێت.\n`{str(e)[:300]}`"
        )


# =========================================================
# /resume
# =========================================================

@app.on_message(filters.command("resume") & filters.group)
async def resume_command(client, message):

    try:
        await voice.resume(message.chat.id)

        await message.reply("▶️ موزیک بەردەوام بوو.")

    except Exception as e:
        await message.reply(
            f"❌ نەتوانرا resume بکرێت.\n`{str(e)[:300]}`"
        )


# =========================================================
# /skip
# =========================================================

@app.on_message(filters.command("skip") & filters.group)
async def skip_command(client, message):

    chat_id = message.chat.id
    queue = get_queue(chat_id)

    try:
        if queue:

            next_file, next_title = queue.popleft()

            current_track[chat_id] = {
                "file": next_file,
                "title": next_title,
            }

            await voice.play(
                chat_id,
                MediaStream(
                    next_file,
                    video_flags=MediaStream.Flags.IGNORE,
                ),
            )

            await message.reply(
                f"⏭ گۆڕدرا بۆ:\n🎵 {next_title}"
            )

        else:

            await voice.leave_call(chat_id)

            current_track.pop(chat_id, None)

            await message.reply(
                "⏭ Queue بەتاڵە."
            )

    except Exception as e:

        await message.reply(
            f"❌ Skip error:\n`{str(e)[:300]}`"
        )


# =========================================================
# /stop
# =========================================================

@app.on_message(filters.command("stop") & filters.group)
async def stop_command(client, message):

    chat_id = message.chat.id

    try:

        await voice.leave_call(chat_id)

        queues[chat_id].clear()
        current_track.pop(chat_id, None)

        await message.reply(
            "⏹ موزیک و Voice Chat وەستاندرا."
        )

    except Exception as e:

        await message.reply(
            f"❌ نەتوانرا وەستێندرێت.\n`{str(e)[:300]}`"
        )


# =========================================================
# /queue
# =========================================================

@app.on_message(filters.command("queue") & filters.group)
async def queue_command(client, message):

    queue = get_queue(message.chat.id)

    if not queue:
        await message.reply("📭 Queue بەتاڵە.")
        return

    text = "🎵 **Music Queue**\n\n"

    for index, (_, title) in enumerate(queue, start=1):
        text += f"{index}. {title}\n"

    await message.reply(text)


# =========================================================
# /nowplaying
# =========================================================

@app.on_message(filters.command("nowplaying") & filters.group)
async def nowplaying_command(client, message):

    track = current_track.get(message.chat.id)

    if not track:
        await message.reply("🎵 هیچ موزیکێک لە ئێستا پڵەی ناکرێت.")
        return

    await message.reply(
        f"🎶 **Now Playing**\n\n"
        f"{track['title']}"
    )


# =========================================================
# /volume
# =========================================================

@app.on_message(filters.command("volume") & filters.group)
async def volume_command(client, message):

    if len(message.command) < 2:
        await message.reply(
            "🔊 نموونە:\n`/volume 80`\n\n"
            "نێوان 0 تا 200."
        )
        return

    try:
        volume = int(message.command[1])

        if volume < 0 or volume > 200:
            raise ValueError()

        await voice.change_volume_call(
            message.chat.id,
            volume
        )

        await message.reply(
            f"🔊 Volume: {volume}%"
        )

    except Exception:
        await message.reply(
            "❌ Volume دەبێت ژمارەیەک لە 0 تا 200 بێت."
        )


# =========================================================
# Start
# =========================================================

async def start_music_system():

    await app.start()
    await voice.start()

    print("🎵 Music / Voice Chat system started.")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(start_music_system())
