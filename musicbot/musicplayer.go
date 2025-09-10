package musicbot

import (
	"context"
	"math/rand"
	"time"

	"github.com/disgoorg/disgo/discord"
	"github.com/disgoorg/disgolink/v3/disgolink"
	"github.com/disgoorg/disgolink/v3/lavalink"
	"github.com/disgoorg/snowflake/v2"
)

type LoopMode string

const (
	LoopNone  LoopMode = "none"
	LoopTrack LoopMode = "track"
	LoopQueue LoopMode = "queue"
)

type ShuffleMode bool

const (
	ShuffleOn  ShuffleMode = true
	ShuffleOff ShuffleMode = false
)

/* Player is the central controller for a single guild's playback. */
type Player struct {
	/* The underlying library player that talks to Lavalink */
	disgoPlayer disgolink.Player

	/* Application-specific state */
	guildID          snowflake.ID
	channelID        snowflake.ID
	playerMessage    *discord.Message /* The message that contains the player controls */
	sessionMessage   *discord.Message
	current          *lavalink.Track
	tracks           []lavalink.Track
	prevtracks       []lavalink.Track
	paused           bool
	loop             LoopMode
	shuffle          ShuffleMode
	sessionStartTime time.Time
}

// NewPlayer creates our custom player controller.
func NewPlayer(guildID snowflake.ID, disgoPlayer disgolink.Player) *Player {
	return &Player{
		disgoPlayer:      disgoPlayer,
		guildID:          guildID,
		channelID:        0,
		playerMessage:    nil,
		sessionMessage:   nil,
		current:          nil,
		tracks:           make([]lavalink.Track, 0),
		prevtracks:       make([]lavalink.Track, 0),
		paused:           false,
		loop:             LoopNone,
		shuffle:          ShuffleOff,
		sessionStartTime: time.Now(),
	}
}

/* Pauses playback. */
func (p *Player) Pause(ctx context.Context) error {
	p.paused = true /* update internal state */
	return p.disgoPlayer.Update(ctx, lavalink.WithPaused(true))
}

/* Resumes playback. */
func (p *Player) Resume(ctx context.Context) error {
	p.paused = false /* update internal state */
	return p.disgoPlayer.Update(ctx, lavalink.WithPaused(false))
}

func (p *Player) IsPlaying() bool {
	/* Check if the player is currently playing a track */
	return p.current != nil
}

/* Plays a track. */
func (p *Player) Play(ctx context.Context, track lavalink.Track) error {
	p.current = &track
	return p.disgoPlayer.Update(ctx, lavalink.WithTrack(track))
}

/* StopAudio stops the audio playback and clears the current track. */
func (p *Player) StopAudio(ctx context.Context) error {
	p.current = nil
	return p.disgoPlayer.Update(ctx, lavalink.WithNullTrack())
}

/* ClearState resets the player's state (queue, loop, etc.) to default. */
func (p *Player) ClearState() {
	p.paused = false
	p.loop = LoopNone
	p.shuffle = ShuffleOff
	p.tracks = make([]lavalink.Track, 0)
	p.prevtracks = make([]lavalink.Track, 0)
}

/* PlayNext determines the next track to play and starts it. */
func (p *Player) PlayNext(ctx context.Context) error {

	// Move the old track to previous tracks
	if p.current != nil {
		p.prevtracks = append(p.prevtracks, *p.current)
	}

	// If the queue is empty and we are not looping the current track, stop.
	if len(p.tracks) == 0 && p.loop != LoopTrack {
		p.current = nil
		return p.disgoPlayer.Update(ctx, lavalink.WithNullTrack())
	}

	// If loop mode is queue, add the current track to the end of the queue.
	if p.loop == LoopQueue && p.current != nil {
		p.tracks = append(p.tracks, *p.current)
	}

	// If we are looping the current track, just play it again.
	if p.loop == LoopTrack && p.current != nil {
		return p.Play(ctx, *p.current)
	}

	var nextTrack lavalink.Track
	if p.shuffle == ShuffleOn {
		// Pick a random track from the queue
		i := rand.Intn(len(p.tracks))
		nextTrack = p.tracks[i]
		p.tracks = append(p.tracks[:i], p.tracks[i+1:]...)
	} else {
		// Pick the first track from the queue
		nextTrack = p.tracks[0]
		p.tracks = p.tracks[1:]
	}
	return p.Play(ctx, nextTrack)
}

func (p *Player) PlayPrevious(ctx context.Context) error {
	if !p.IsPlaying() {
		/* player is not playing */
		return nil
	}

	if len(p.prevtracks) == 0 || p.Position() > lavalink.Second*10 {
		/* empty recently played or more than 10 seconds have past of current track */
		return p.Seek(ctx, 0)
	}
	// Get the last played track
	lastTrack := p.prevtracks[len(p.prevtracks)-1]
	p.prevtracks = p.prevtracks[:len(p.prevtracks)-1]
	return p.Play(ctx, lastTrack)
}

func (p *Player) Seek(ctx context.Context, position lavalink.Duration) error {
	if !p.IsPlaying() {
		return nil
	}
	return p.disgoPlayer.Update(ctx, lavalink.WithPosition(position))
}

func (p *Player) AddToPrevious(track lavalink.Track) {
	p.prevtracks = append(p.prevtracks, track)
}

func (p *Player) AddToQueue(tracks ...lavalink.Track) {
	p.tracks = append(p.tracks, tracks...)
}

func (p *Player) AddToQueueNext(tracks ...lavalink.Track) {
	p.tracks = append(tracks, p.tracks...)
}

func (p *Player) Current() lavalink.Track {
	return *p.current
}

func (p *Player) Queue() []lavalink.Track {
	copiedTracks := make([]lavalink.Track, len(p.tracks))
	copy(copiedTracks, p.tracks)
	return copiedTracks
}

func (p *Player) RemoveFromQueue(index int) (lavalink.Track, bool) {
	if index < 0 || index >= len(p.tracks) {
		return lavalink.Track{}, false
	}
	track := p.tracks[index]
	p.tracks = append(p.tracks[:index], p.tracks[index+1:]...)
	return track, true
}

func (p *Player) IsPaused() bool {
	return p.paused
}

func (p *Player) Position() lavalink.Duration {
	if !p.IsPlaying() {
		return 0
	}
	return p.disgoPlayer.Position()
}

func (p *Player) Loop() LoopMode {
	return p.loop
}

func (p *Player) SetLoop(loop LoopMode) {
	p.loop = loop
}

func (p *Player) Shuffle() ShuffleMode {
	return p.shuffle
}

func (p *Player) SetShuffle(shuffle ShuffleMode) {
	p.shuffle = shuffle
}

func (p *Player) PlayerMessage() *discord.Message {
	return p.playerMessage
}

func (p *Player) SetMessage(message *discord.Message) {
	p.playerMessage = message
}

func (p *Player) ChannelID() snowflake.ID {
	return p.channelID
}

func (p *Player) SetChannelID(channelID snowflake.ID) {
	p.channelID = channelID
}

func (p *Player) SessionMessage() *discord.Message {
	return p.sessionMessage
}

func (p *Player) SetSessionMessage(message *discord.Message) {
	p.sessionMessage = message
}

func (p *Player) SessionStartTime() time.Time {
	return p.sessionStartTime
}

func (p *Player) PreviousTracks() []lavalink.Track {
	numTracks := len(p.prevtracks)
	if numTracks == 0 {
		return []lavalink.Track{}
	}
	reversedTracks := make([]lavalink.Track, numTracks)
	for i, track := range p.prevtracks {
		reversedTracks[len(p.prevtracks)-1-i] = track
	}
	return reversedTracks
}
