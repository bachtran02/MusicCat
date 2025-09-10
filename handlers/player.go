package handlers

import (
	"MusicCatGo/commands"
	"MusicCatGo/musicbot"
	"context"
	"fmt"
	"sort"
	"time"

	"github.com/disgoorg/disgo/discord"
	"github.com/disgoorg/disgo/events"
	"github.com/disgoorg/disgolink/v3/lavalink"
	"github.com/disgoorg/snowflake/v2"
)

type ButtonID string

const (
	PlayPrevious ButtonID = "play_previous"
	PlayNext     ButtonID = "play_next"
	PausePlayer  ButtonID = "pause_player"
	ResumePlayer ButtonID = "resume_player"
	StopPlayer   ButtonID = "stop_player"
	LoopQueue    ButtonID = "loop_queue"
	LoopTrack    ButtonID = "loop_track"
	LoopOff      ButtonID = "loop_off"
	ShuffleOn    ButtonID = "shuffle_on"
	ShuffleOff   ButtonID = "shuffle_off"
)

func (h *Handlers) OnPlayerInteraction(event *events.ComponentInteractionCreate) {

	player, ok := h.PlayerManager.GetPlayer(*event.GuildID())
	if !ok || !player.IsPlaying() {
		/* player is not playing, player embed SHOULD HAVE BEEN deleted */
		/* deleting player embed */
		if err := h.Client.Rest().DeleteMessage(event.Message.ChannelID, event.Message.ID); err != nil {
			musicbot.LogDeleteError(err, event.GuildID().String(),
				event.Message.ChannelID.String(), event.Message.ID.String())
		}
		return
	}

	var (
		ctx, cancel      = context.WithTimeout(context.Background(), 10*time.Second)
		buttonNameString = event.ComponentInteraction.ButtonInteractionData().CustomID()
		buttonID         = ButtonID(buttonNameString)
	)
	defer cancel()
	musicbot.LogPlayerInteraction(buttonNameString, event.GuildID().String(), event.User().ID.String())

	switch buttonID {
	case PlayNext:
		player.PlayNext(ctx)
	case StopPlayer:
		player.StopAudio(ctx)
		player.ClearState()
	case ResumePlayer:
		player.Resume(ctx)
	case PausePlayer:
		player.Pause(ctx)
	case PlayPrevious:
		player.PlayPrevious(ctx)
	case ShuffleOn:
		player.SetShuffle(musicbot.ShuffleOn)
	case ShuffleOff:
		player.SetShuffle(musicbot.ShuffleOff)
	case LoopOff:
		player.SetLoop(musicbot.LoopNone)
	case LoopTrack:
		player.SetLoop(musicbot.LoopTrack)
	case LoopQueue:
		player.SetLoop(musicbot.LoopQueue)
	}

	if buttonID != PlayNext && buttonID != StopPlayer {
		updatePlayerEmbed(player.IsPaused(), player.Shuffle(), player.Loop(), event)
	}
}

func updatePlayerEmbed(paused bool, shuffle musicbot.ShuffleMode, loop musicbot.LoopMode, event *events.ComponentInteractionCreate) {
	buttons := createButtons(paused, shuffle, loop)
	messageBuilder := discord.NewMessageUpdateBuilder()
	messageBuilder.
		AddActionRow(buttons[0], buttons[1], buttons[2]).
		AddActionRow(buttons[3], buttons[4], buttons[5])

	event.UpdateMessage(messageBuilder.Build())
}

func createPlayerEmbed(track lavalink.Track, paused bool, shuffle musicbot.ShuffleMode, loop musicbot.LoopMode) discord.MessageCreate {

	embedBuilder := createEmbed(track)
	messageBuilder := discord.NewMessageCreateBuilder().SetEmbeds(embedBuilder.Build())
	return addButtonsNew(paused, shuffle, loop, messageBuilder).Build()
}

func addButtonsNew(paused bool, shuffle musicbot.ShuffleMode, loop musicbot.LoopMode, messageBuilder *discord.MessageCreateBuilder) *discord.MessageCreateBuilder {

	buttons := createButtons(paused, shuffle, loop)

	return messageBuilder.
		AddActionRow(buttons[0], buttons[1], buttons[2]).
		AddActionRow(buttons[3], buttons[4], buttons[5])
}

func createButtons(paused bool, shuffle musicbot.ShuffleMode, loop musicbot.LoopMode) []discord.ButtonComponent {
	var (
		playPauseButton discord.ButtonComponent
		repeatButton    discord.ButtonComponent
		shuffleButton   discord.ButtonComponent

		playPreviousButton = discord.NewSecondaryButton("", string(PlayPrevious)).WithEmoji(discord.ComponentEmoji{ID: snowflake.ID(musicbot.PLAYER_PREVIOUS_EMOJI_ID)})
		playNextButton     = discord.NewSecondaryButton("", string(PlayNext)).WithEmoji(discord.ComponentEmoji{ID: snowflake.ID(musicbot.PLAYER_NEXT_EMOJI_ID)})
		stopButton         = discord.NewSecondaryButton("", string(StopPlayer)).WithEmoji(discord.ComponentEmoji{ID: snowflake.ID(musicbot.STOP_PLAYER_EMOJI_ID)})
	)

	if paused {
		playPauseButton = discord.NewSecondaryButton("", string(ResumePlayer)).WithEmoji(discord.ComponentEmoji{ID: snowflake.ID(musicbot.RESUME_PLAYER_EMOJI_ID)})
	} else {
		playPauseButton = discord.NewSecondaryButton("", string(PausePlayer)).WithEmoji(discord.ComponentEmoji{ID: snowflake.ID(musicbot.PAUSE_PLAYER_EMOJI_ID)})
	}

	switch loop {
	case musicbot.LoopNone:
		repeatButton = discord.NewSecondaryButton("", string(LoopQueue)).WithEmoji(discord.ComponentEmoji{ID: snowflake.ID(musicbot.LOOP_OFF_EMOJI_ID)})
	case musicbot.LoopQueue:
		repeatButton = discord.NewSecondaryButton("", string(LoopTrack)).WithEmoji(discord.ComponentEmoji{ID: snowflake.ID(musicbot.LOOP_QUEUE_EMOJI_ID)})
	case musicbot.LoopTrack:
		repeatButton = discord.NewSecondaryButton("", string(LoopOff)).WithEmoji(discord.ComponentEmoji{ID: snowflake.ID(musicbot.LOOP_TRACK_EMOJI_ID)})
	}

	if shuffle {
		shuffleButton = discord.NewSecondaryButton("", string(ShuffleOff)).WithEmoji(discord.ComponentEmoji{ID: snowflake.ID(musicbot.SHUFFLE_ON_EMOJI_ID)})
	} else {
		shuffleButton = discord.NewSecondaryButton("", string(ShuffleOn)).WithEmoji(discord.ComponentEmoji{ID: snowflake.ID(musicbot.SHUFFLE_OFF_EMOJI_ID)})
	}

	return []discord.ButtonComponent{
		playPreviousButton, playPauseButton, playNextButton,
		stopButton, repeatButton, shuffleButton,
	}
}

func createEmbed(track lavalink.Track) discord.EmbedBuilder {
	var (
		playtime string
		userData commands.UserData
	)

	_ = track.UserData.Unmarshal(&userData)

	if track.Info.IsStream {
		playtime = "LIVE"
	} else {
		playtime = musicbot.FormatTime(track.Info.Length)
	}

	return *discord.NewEmbedBuilder().
		SetDescriptionf("[%s](%s)\n%s `%s`\n\n<@%s>",
			track.Info.Title, *track.Info.URI, track.Info.Author,
			playtime, userData.Requester).
		SetThumbnail(*track.Info.ArtworkURL)
}

func createRecentlyPlayedEmbed(prevTracks []lavalink.Track, startTime time.Time) discord.MessageCreate {

	var (
		boolTrue            = true
		numTracks           = len(prevTracks)
		requesterMap        = make(map[snowflake.ID]int)
		lastTrack           = prevTracks[0]
		userData            commands.UserData
		recentlyPlayedField string
		requesterField      string
	)

	for i := range numTracks {
		var (
			track = prevTracks[i]
			_     = track.UserData.Unmarshal(&userData)
		)

		if i < 5 {
			recentlyPlayedField += fmt.Sprintf("\n%d. [%s](%s)",
				i+1, track.Info.Title, *track.Info.URI)
		}
		requesterMap[snowflake.ID(userData.Requester)]++
	}

	/* sort requester */
	keys := make([]snowflake.ID, 0, len(requesterMap))
	for k := range requesterMap {
		keys = append(keys, k)
	}
	sort.Slice(keys, func(i, j int) bool {
		return requesterMap[keys[i]] > requesterMap[keys[j]] // descending by key
	})

	for i := 0; i < min(5, len(keys)); i++ {
		requesterField += fmt.Sprintf("%d. <@%s>\n", i+1, keys[i])
	}

	return discord.NewMessageCreateBuilder().
		SetEmbeds(discord.NewEmbedBuilder().
			SetTitle("Current Session").
			SetDescription(fmt.Sprintf("**Started:** <t:%d:R>", startTime.Unix())).
			SetFields(
				discord.EmbedField{
					Name:   "Recent Tracks",
					Value:  recentlyPlayedField,
					Inline: &boolTrue,
				},
				discord.EmbedField{
					Name:   "Top Requesters",
					Value:  requesterField,
					Inline: &boolTrue,
				},
			).SetThumbnail(*lastTrack.Info.ArtworkURL).Build()).Build()
}
