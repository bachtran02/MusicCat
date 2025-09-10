package commands

import (
	"MusicCatGo/musicbot"

	"github.com/disgoorg/disgo/discord"
	"github.com/disgoorg/disgo/handler"
)

func (c *Commands) Loop(data discord.SlashCommandInteractionData, e *handler.CommandEvent) error {
	var (
		body string
		mode string = data.String("mode")
	)

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

	if mode == string(musicbot.LoopNone) {
		player.SetLoop(musicbot.LoopNone)
		body = "⏭️ Disable loop"
	} else if mode == string(musicbot.LoopTrack) {
		player.SetLoop(musicbot.LoopTrack)
		body = "🔂 Enabled Track loop"
	} else {
		player.SetLoop(musicbot.LoopQueue)
		body = "🔁 Enabled Queue loop"
	}

	if sendErr := e.CreateMessage(discord.MessageCreate{
		Embeds: []discord.Embed{{Description: body}},
	}); sendErr != nil {
		musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), false)
	}

	musicbot.AutoRemove(e)
	return nil
}
