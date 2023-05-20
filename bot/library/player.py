import random
from lavalink import (DefaultPlayer, AudioTrack, DeferredAudioTrack,
                    QueueEndEvent, TrackLoadFailedEvent,TrackStartEvent,
                    TrackLoadFailedEvent, LoadError, InvalidTrack)
from typing import Optional, Union, List, Dict

class CustomPlayer(DefaultPlayer):
    
    def __init__(self, guild_id: int, node: 'Node'):
        super().__init__(guild_id, node)

        self.is_autoplay: bool = False
        self.textchannel_id: int = None 
        self.autoqueue: List[AudioTrack] = []

    def clear_player(self):
        """Clear all existing configs, clear queue"""

        [self.loop, self.current, self.shuffle, self.is_autoplay] = [0, None, False, False]
        # clear all queues  
        self.queue.clear()
        self.autoqueue.clear()

    def add_autoqueue(self, related_tracks: List[AudioTrack]):

        for track in related_tracks:
            self.autoqueue.append(track)

    async def autoplay(self) -> Optional[AudioTrack]:

        if not (self.is_autoplay and self.autoqueue):
            return None
    
        popat = random.randrange(len(self.autoqueue))
        track = self.autoqueue.pop(popat)

        await self.play(track)
        return self.current

    async def play(self, track: Optional[Union[AudioTrack, DeferredAudioTrack, Dict]] = None, start_time: Optional[int] = 0,
                   end_time: Optional[int] = None, no_replace: Optional[bool] = False, volume: Optional[int] = None,
                   pause: Optional[bool] = False, **kwargs):

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

    async def skip(self):

        curtrack = self.current
        await self.play()
        return curtrack
            
    async def stop(self):
        
        await self.node.update_player(self._internal_id, encoded_track=None)
        self.current = None
        self.clear_player()
    
    def add(self, track: Union[AudioTrack, DeferredAudioTrack, Dict], requester: int = 0, index: int = -1):
    
        at = track

        if isinstance(track, dict):
            at = AudioTrack(track, requester)

        if requester != 0:
            at.requester = requester

        if index == -1:
            self.queue.append(at)
        else:
            self.queue.insert(index, at)