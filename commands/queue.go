package commands

import (
	"MusicCatGo/musicbot"
	"fmt"

	"github.com/disgoorg/disgo/discord"
	"github.com/disgoorg/disgo/handler"
)

func (c *Commands) Now(data discord.SlashCommandInteractionData, e *handler.CommandEvent) error {

	player, ok := c.PlayerManager.GetPlayer(*e.GuildID())
	if !ok || !player.IsPlaying() {
		if sendErr := e.CreateMessage(discord.MessageCreate{
			Content: "Player is not playing.",
			Flags:   discord.MessageFlagEphemeral,
		}); sendErr != nil {
			musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), true)
		}
		return nil
	}

	var (
		track    = player.Current()
		queue    = player.Queue()
		paused   = player.IsPaused()
		position = player.Position()
		userData UserData
	)
	_ = track.UserData.Unmarshal(&userData)

	content := fmt.Sprintf("[%s](%s)\n%s\n%s\n\nRequested: <@!%s>\n",
		track.Info.Title, *track.Info.URI, track.Info.Author,
		musicbot.PlayerBar(paused, track, position), userData.Requester)

	if len(queue) >= 1 {
		content += "\n**Up next:**"
		nextTrack := queue[0]
		var Playtime string
		if nextTrack.Info.IsStream {
			Playtime = "`LIVE`"
		} else {
			Playtime = musicbot.FormatTime(nextTrack.Info.Length)
		}
		content += fmt.Sprintf("\n[%s](%s) `%s`",
			nextTrack.Info.Title, *nextTrack.Info.URI, Playtime)

		if nextTrack.Info.SourceName == "deezer" || nextTrack.Info.SourceName == "spotify" {
			content += " " + nextTrack.Info.Author
		}
	}

	embed := discord.NewEmbedBuilder().
		SetTitle("Current").
		SetDescription(content).
		SetThumbnail(*track.Info.ArtworkURL)

	if sendErr := e.CreateMessage(discord.MessageCreate{
		Embeds: []discord.Embed{embed.Build()},
	}); sendErr != nil {
		musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), false)
	}
	return nil
}

func (c *Commands) Queue(data discord.SlashCommandInteractionData, e *handler.CommandEvent) error {

	player, ok := c.PlayerManager.GetPlayer(*e.GuildID())
	if !ok || !player.IsPlaying() {
		if sendErr := e.CreateMessage(discord.MessageCreate{
			Content: "Player is not playing.",
			Flags:   discord.MessageFlagEphemeral,
		}); sendErr != nil {
			musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), true)
		}
		return nil
	}

	var (
		track    = player.Current()
		queue    = player.Queue()
		paused   = player.IsPaused()
		position = player.Position()
		userData UserData
	)
	_ = track.UserData.Unmarshal(&userData)

	content := fmt.Sprintf("[%s](%s)\n%s\n%s\n\nRequested: <@!%s>\n",
		track.Info.Title, *track.Info.URI, track.Info.Author,
		musicbot.PlayerBar(paused, track, position), userData.Requester)

	limit := min(10, len(queue))
	for i, track := range queue[:limit] {
		if i == 0 {
			content += fmt.Sprintf("\n**Up next:** `%d track(s)`", len(queue))
		}

		var Playtime string
		if track.Info.IsStream {
			Playtime = "`LIVE`"
		} else {
			Playtime = musicbot.FormatTime(track.Info.Length)
		}
		content += fmt.Sprintf("\n%d. [%s](%s) `%s`",
			i+1, track.Info.Title, *track.Info.URI, Playtime)

		if track.Info.SourceName == "deezer" || track.Info.SourceName == "spotify" {
			content += " " + track.Info.Author
		}
	}

	embed := discord.NewEmbedBuilder().
		SetTitle("Queue").
		SetDescription(content).
		SetThumbnail(*track.Info.ArtworkURL)

	if sendErr := e.CreateMessage(discord.MessageCreate{
		Embeds: []discord.Embed{embed.Build()},
	}); sendErr != nil {
		musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), false)
	}
	return nil
}
