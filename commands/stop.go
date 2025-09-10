package commands

import (
	"MusicCatGo/musicbot"

	"github.com/disgoorg/disgo/discord"
	"github.com/disgoorg/disgo/handler"
	"github.com/disgoorg/json"
)

func (c *Commands) Stop(_ discord.SlashCommandInteractionData, e *handler.CommandEvent) error {

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

	if err := e.DeferCreateMessage(false); err != nil {
		return err
	}
	defer musicbot.AutoRemove(e)

	player.ClearState()
	if err := player.StopAudio(e.Ctx); err != nil {
		if _, updateErr := e.UpdateInteractionResponse(discord.MessageUpdate{
			Content: json.Ptr("Failed to stop player."),
		}); updateErr != nil {
			musicbot.LogUpdateError(updateErr, e.GuildID().String(), e.User().ID.String())
		}
		return err
	}

	if _, updateErr := e.UpdateInteractionResponse(discord.MessageUpdate{
		Embeds: &[]discord.Embed{{Description: "⏹️ Stopped playing and cleared the queue."}},
	}); updateErr != nil {
		musicbot.LogUpdateError(updateErr, e.GuildID().String(), e.User().ID.String())
	}
	return nil
}
