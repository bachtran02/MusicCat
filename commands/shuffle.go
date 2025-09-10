package commands

import (
	"MusicCatGo/musicbot"

	"github.com/disgoorg/disgo/discord"
	"github.com/disgoorg/disgo/handler"
)

func (c *Commands) Shuffle(_ discord.SlashCommandInteractionData, e *handler.CommandEvent) error {
	var body string

	player, ok := c.PlayerManager.GetPlayer(*e.GuildID())
	if !ok || !player.IsPlaying() {
		sendErr := e.CreateMessage(discord.MessageCreate{
			Content: "Player is not playing.",
			Flags:   discord.MessageFlagEphemeral,
		})
		if sendErr != nil {
			musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), true)
		}
		return nil
	}

	if player.Shuffle() {
		player.SetShuffle(false)
		body = "🔀 Shuffle off"
	} else {
		player.SetShuffle(true)
		body = "🔀 Shuffle on"
	}

	if sendErr := e.CreateMessage(discord.MessageCreate{
		Embeds: []discord.Embed{{Description: body}},
	}); sendErr != nil {
		musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), false)
	}
	musicbot.AutoRemove(e)
	return nil
}
