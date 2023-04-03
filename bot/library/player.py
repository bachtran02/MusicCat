import random
from lavalink.models import DefaultPlayer, AudioTrack, DeferredAudioTrack
from lavalink.events import (NodeChangedEvent, QueueEndEvent, TrackEndEvent,
                     TrackExceptionEvent, TrackLoadFailedEvent,
                     TrackStartEvent, TrackStuckEvent)
from typing import Optional, Union, List, Dict

class CustomPlayer(DefaultPlayer):
    
    def __init__(self, guild_id: int, node: 'Node'):
        super().__init__(guild_id, node)

        self.is_autoplay = False
        self.textchannel_id = None 
        self.autoqueue: List[AudioTrack] = []

    def clear_player(self):
        """Clear all existing configs, clear queue"""

        self.current = None
        self.shuffle = False
        self.loop = 0

        # clear all queues
        self.queue.clear()
        self.autoqueue.clear()

    def add_autoplay(self, related_tracks: List[AudioTrack]):

        for track in related_tracks:
            self.autoqueue.append(track)
        # print(self.autoqueue)

    async def autoplay(self, botid=None) -> Optional[AudioTrack]:

        if not (self.is_autoplay and self.autoqueue):
            return None
    
        popat = random.randrange(len(self.autoqueue))
        track = self.autoqueue.pop(popat)
        track.requester = botid

        await self.play(track)
        return self.current

    async def play(self, track: Optional[Union[AudioTrack, DeferredAudioTrack, Dict]] = None, start_time: Optional[int] = 0,
                   end_time: Optional[int] = None, no_replace: Optional[bool] = False, volume: Optional[int] = None,
                   pause: Optional[bool] = False):

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
                await self.node._send(op='stop', guildId=self._internal_id)
                await self.node._dispatch_event(QueueEndEvent(self))
                return

            pop_at = randrange(len(self.queue)) if self.shuffle else 0
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
                playable_track = await track.load(self.node._manager._lavalink)
            except LoadError as load_error:
                await self.node._dispatch_event(TrackLoadFailedEvent(self, track, load_error))

        if playable_track is None:  # This should only fire when a DeferredAudioTrack fails to yield a base64 track string.
            await self.node._dispatch_event(TrackLoadFailedEvent(self, track, None))
            return

        await self.play_track(playable_track, start_time, end_time, no_replace, volume, pause)
        await self.node._dispatch_event(TrackStartEvent(self, track))

    async def skip(self):

        curtrack = self.current
        await self.play()
        return curtrack

    async def leave(self):

        channel_id = self.channel_id
        self.clear_player()
        self.channel_id = None
        return channel_id
            
    async def stop(self):
        
        await self.node._send(op='stop', guildId=self._internal_id)
        self.clear_player()
        