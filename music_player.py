import logging
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

log = logging.getLogger("music-player")


class MusicPlayer:
    """کۆنترۆڵکردنی لێدانی گۆرانی لە کۆڵی دەنگی (Voice Chat) گروپەکان."""

    def __init__(self, app):
        self.call_py = PyTgCalls(app)

    def start(self):
        # پێویستە بە شێوازی هاوسەنگ (sync) بانگ بکرێت، هاوشێوەی app.start()
        self.call_py.start()

    async def play(self, chat_id: int, file_path: str):
        await self.call_py.play(chat_id, MediaStream(file_path))

    async def stop(self, chat_id: int):
        await self.call_py.leave_call(chat_id)
