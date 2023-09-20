import random
import typing as t
from lavalink import (DefaultPlayer, AudioTrack, DeferredAudioTrack,
                    QueueEndEvent, TrackLoadFailedEvent,TrackStartEvent,
                    TrackLoadFailedEvent, LoadError, InvalidTrack)

class CustomPlayer(DefaultPlayer):
    
    def __init__(self, guild_id: int, node: 'Node'):
        super().__init__(guild_id, node)
        self.recently_played : t.List[AudioTrack] = []
    
    async def clear(self):
        """Clear all existing configs, clear queue"""

        self.loop, self.shuffle  = 0, False
        self.current, self.previous = None, None
        self.queue.clear()
        self.recently_played.clear()
        await self.clear_filters()

    async def play(self, track=None, start_time=0, end_time=None,
                   no_replace=False, volume=None, pause=False, **kwargs):

        if no_replace and self.is_playing:
            return

        if track is not None and isinstance(track, dict):
            track = AudioTrack(track, 0)

        if self.loop > 0 and self.current:
            if self.loop == 1:
                if track is not None:
                    self.queue.insert(0, self.current)
                else:
                    track = self.current
            if self.loop == 2:
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

            pop_at = random.randrange(len(self.queue)) if self.shuffle else 0
            track = self.queue.pop(pop_at)

        if start_time is not None:
            if not isinstance(start_time, int) or not 0 <= start_time < track.duration:
                raise ValueError('start_time must be an int with a value equal to, or greater than 0, and less than the track duration')

        if end_time is not None:
            if not isinstance(end_time, int) or not 1 <= end_time <= track.duration:
                raise ValueError('end_time must be an int with a value equal to, or greater than 1, and less than, or equal to the track duration')

        self.current = track
        playable_track = track.track

        if playable_track is None:
            if not isinstance(track, DeferredAudioTrack):
                raise InvalidTrack('Cannot play the AudioTrack as \'track\' is None, and it is not a DeferredAudioTrack!')

            try:
                playable_track = await track.load(self.client)
            except LoadError as load_error:
                await self.client._dispatch_event(TrackLoadFailedEvent(self, track, load_error))

        if playable_track is None:  # This should only fire when a DeferredAudioTrack fails to yield a base64 track string.
            await self.client._dispatch_event(TrackLoadFailedEvent(self, track, None))
            return

        await self.play_track(playable_track, start_time, end_time, no_replace, volume, pause, **kwargs)
        await self.client._dispatch_event(TrackStartEvent(self, track))

    async def play_previous(self):

        if not self.recently_played or self.current.is_seekable and self.position > 3000:
            await self.seek(0)
            return
        
        previous: AudioTrack = self.recently_played.pop()
        curr_requester = self.current.extra.get('requester', 0)

        self.add(track=self.current, index=0, requester=curr_requester)
        self.add(track=previous, index=0, requester=0)
        await self.play()

    async def skip(self):

        current = self.current
        await self.play()
        return current
            
    async def stop(self):
        
        await self.node.update_player(self._internal_id, encoded_track=None)
        await self.clear()
    