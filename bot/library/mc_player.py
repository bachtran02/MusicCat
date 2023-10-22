import random
import typing as t

from lavalink import (DefaultPlayer, AudioTrack, DeferredAudioTrack,
                    QueueEndEvent, TrackLoadFailedEvent,TrackStartEvent,
                    TrackLoadFailedEvent, LoadError, InvalidTrack)

class MusicCatPlayer(DefaultPlayer):

    def __init__(self, guild_id: int, node: 'Node'):
        super().__init__(guild_id, node)
        self._queue : t.List[AudioTrack] = []
        self._queue_index: int = 0

    def add(self, track: t.Union[AudioTrack, 'DeferredAudioTrack', t.Dict], requester: int = 0, index: int = None):
       
        at = track
        if isinstance(track, dict):
            at = AudioTrack(track, requester)
        if requester != 0:
            at.requester = requester
        if index is None:
            self._queue.append(at)
        else:
            self._queue.insert(self._queue_index + index, at)

    async def play(self, track: t.Optional[t.Union[AudioTrack, 'DeferredAudioTrack', t.Dict]] = None, start_time: t.Optional[int] = 0,
                   end_time: t.Optional[int] = None, no_replace: t.Optional[bool] = False, volume: t.Optional[int] = None,
                   pause: t.Optional[bool] = False, **kwargs):
        
        assert track is None
        
        if no_replace and self.is_playing:
            return

        if self.loop > 0 and self.current:
            if self.loop == 1:
                track = self.current
            # TODO: 
            if self.loop == 2:
                raise NotImplementedError

        self._last_position = 0
        self.position_timestamp = 0
        self.paused = pause

        if not track:
            if self._queue_index == len(self._queue):
                self.current = None
                await self.node.update_player(self._internal_id, encoded_track=None)
                await self.client._dispatch_event(QueueEndEvent(self))
                return
            track = self._queue[self._queue_index]
            self._queue_index += 1

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

    
    async def play_backward(self):
        if not self._queue_index or self.current.is_seekable and self.position > 3000:
            await self.seek(0)
            return

        if self._queue_index == 1:
            self._queue_index = 0
        else:
            self._queue_index -= 2
        await self.play()
        
    async def skip(self):
        current = self.current
        await self.play()
        return current
        
    async def stop(self):
        await self.node.update_player(self._internal_id, encoded_track=None)
        await self.client._dispatch_event(QueueEndEvent(self))
        await self.clear()

    def shuffle_queue(self):
        queue = self.get_queue()
        random.shuffle(queue)
        self._queue[self._queue_index:] = queue
        
    async def clear(self):
        """Clear all existing configs, clear queue"""

        self.loop = self.LOOP_NONE
        self.current = None
        self._queue.clear()
        self._queue_index = 0
        await self.clear_filters()

    def get_queue(self, index: int = -1):
        
        if index == -1:
            return self._queue[self._queue_index:]
        return self._queue[self._queue_index + index]
    
    def remove_track(self, index):
        return self._queue.pop(self._queue_index + index)
    