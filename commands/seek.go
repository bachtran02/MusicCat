package commands

import (
	"MusicCatGo/musicbot"
	"fmt"

	"github.com/disgoorg/disgo/discord"
	"github.com/disgoorg/disgo/handler"
	"github.com/disgoorg/disgolink/v3/lavalink"
	"github.com/disgoorg/json"
)

func (c *Commands) Seek(data discord.SlashCommandInteractionData, e *handler.CommandEvent) error {
	var position = data.String("position")

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

	/* invalid input time */
	h, m, s, err := musicbot.ParseTime(position)
	if err != nil {
		if sendErr := e.CreateMessage(discord.MessageCreate{
			Content: "Invalid position.",
			Flags:   discord.MessageFlagEphemeral,
		}); sendErr != nil {
			return sendErr
		}
		return err
	}

	/* deferring message */
	if err := e.DeferCreateMessage(false); err != nil {
		return err
	}
	defer musicbot.AutoRemove(e)

	if player.Current().Info.IsStream {
		if _, updateErr := e.UpdateInteractionResponse(discord.MessageUpdate{
			Content: json.Ptr("Track is unseekable."),
		}); updateErr != nil {
			return updateErr
		}
		return nil
	}

	newPosition := lavalink.Duration(s*int(lavalink.Second) + m*int(lavalink.Minute) + h*int(lavalink.Hour))
	if err := player.Seek(e.Ctx, newPosition); err != nil {
		if _, updateErr := e.UpdateInteractionResponse(discord.MessageUpdate{
			Content: json.Ptr("Failed to seek to position."),
		}); updateErr != nil {
			musicbot.LogUpdateError(updateErr, e.GuildID().String(), e.User().ID.String())
		}
		return err
	}

	if _, updateErr := e.UpdateInteractionResponse(discord.MessageUpdate{
		Embeds: &[]discord.Embed{{Description: fmt.Sprintf(
			"⏩ Player moved to `%s`", musicbot.FormatTime(newPosition))}},
	}); updateErr != nil {
		musicbot.LogUpdateError(updateErr, e.GuildID().String(), e.User().ID.String())
	}
	return nil
}
