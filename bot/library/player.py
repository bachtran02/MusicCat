from random import randrange

from typing import Dict, List, Optional, Union
from lavalink import DefaultPlayer, DeferredAudioTrack, QueueEndEvent, AudioTrack
from lavalink.common import MISSING

class MusicCatPlayer(DefaultPlayer):
    """Custom lavalink player for MusicCat"""

    LOOP_NONE: int = 0
    LOOP_QUEUE: int = 1
    LOOP_SINGLE: int = 2
    
    def __init__(self, guild_id: int, node):
        super().__init__(guild_id, node)
        self.recently_played: List[AudioTrack] = []
        self.message_id = None
        self.textchannel_id = None

    async def play(self,
                   track: Optional[Union[AudioTrack, 'DeferredAudioTrack', Dict[str, Union[Optional[str], bool, int]]]] = None,
                   start_time: int = 0,
                   end_time: int = MISSING,
                   no_replace: bool = MISSING,
                   volume: int = MISSING,
                   pause: bool = False,
                   index: int = MISSING,    # play track at given index bypassing shuffle mode 
                   **kwargs):
        
        if isinstance(no_replace, bool) and no_replace and self.is_playing:
            return

        if track is not None and isinstance(track, dict):
            track = AudioTrack(track, 0)

        if self.loop > 0 and self.current:
            if self.loop == self.LOOP_SINGLE:
                if track is not None:
                    self.queue.insert(0, self.current)
                else:
                    track = self.current
            elif self.loop == self.LOOP_QUEUE:
                self.queue.append(self.current)

        self._last_position = 0
        self.position_timestamp = 0
        self.paused = pause

        if not track:
            if not self.queue:
                self.current = None
                await self.node.update_player(self._internal_id, encoded_track=None)
                await self.client._dispatch_event(QueueEndEvent(self))
                return

            if index is not MISSING:
                assert isinstance(index, int) and 0 <= index < len(self.queue)
                pop_at = index
            elif self.shuffle:
                pop_at = randrange(len(self.queue))
            else:
                pop_at = 0

            track = self.queue.pop(pop_at)
            self.recently_played.append(track)

        if start_time is not MISSING:
            if not isinstance(start_time, int) or not 0 <= start_time < track.duration:
                raise ValueError('start_time must be an int with a value equal to, or greater than 0, and less than the track duration')

        if end_time is not MISSING:
            if not isinstance(end_time, int) or not 1 <= end_time <= track.duration:
                raise ValueError('end_time must be an int with a value equal to, or greater than 1, and less than, or equal to the track duration')

        await self.play_track(track, start_time, end_time, no_replace, volume, pause, **kwargs)

    async def stop(self):
        """|coro|

        Stops the player, clears queue and all existing configs.
        """
        await self.node.update_player(self._internal_id, encoded_track=None)
        await self.client._dispatch_event(QueueEndEvent(self))
        await self._clear()

    async def play_previous(self):
        """|coro|

        Plays previous track and add current track back to queue.
        """
        if not self.recently_played or self.current.is_seekable and self.position > 5000:
            await self.seek(0)
            return

        assert len(self.recently_played) >= 2

        self.queue = self.recently_played[-2:] + self.queue
        self.recently_played = self.recently_played[:-2]

        await self.play(index=0)

    async def skip(self):
        """|coro|

        Skips and return the current track.
        """
        current = self.current
        await self.play()
        return current
    
    def remove(self, index):
        """
        Removes track by index from queue.
        """
        return self.queue.pop(index)

    async def _clear(self):

        self.loop = self.LOOP_NONE
        self.current = None
        self.queue.clear()
        self.recently_played.clear()
        await self.clear_filters()
    