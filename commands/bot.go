package commands

import (
	"MusicCatGo/musicbot"
	"context"
	"fmt"

	"github.com/disgoorg/disgo/discord"
	"github.com/disgoorg/disgo/handler"
)

var bot = discord.SlashCommandCreate{
	Name:        "bot",
	Description: "bot commands",
	Options: []discord.ApplicationCommandOption{
		discord.ApplicationCommandOptionSubCommand{
			Name:        "ping",
			Description: "[test] Ping command",
		},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "join",
			Description: "Joins voice chat channel",
		},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "leave",
			Description: "Leaves voice chat channel",
		},
	}}

func (c *Commands) Connect(data discord.SlashCommandInteractionData, e *handler.CommandEvent) error {

	voiceState, ok := c.Client.Caches().VoiceState(*e.GuildID(), e.User().ID)

	if !ok {
		if sendErr := e.CreateMessage(discord.MessageCreate{
			Content: "You need to be in a voice channel to use this command.",
			Flags:   discord.MessageFlagEphemeral,
		}); sendErr != nil {
			musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), true)
		}
		return nil
	}

	if err := c.Client.UpdateVoiceState(context.Background(), *e.GuildID(), voiceState.ChannelID, false, true); err != nil {
		if sendErr := e.CreateMessage(discord.MessageCreate{
			Content: "Failed to join voice channel.",
			Flags:   discord.MessageFlagEphemeral,
		}); sendErr != nil {
			musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), true)
		}
		return err
	}

	if sendErr := e.CreateMessage(discord.MessageCreate{
		Content: fmt.Sprint("Joined <#", voiceState.ChannelID, ">."),
	}); sendErr != nil {
		musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), false)
		return nil
	}

	musicbot.AutoRemove(e)
	return nil
}

func (c *Commands) Disconnect(data discord.SlashCommandInteractionData, e *handler.CommandEvent) error {

	if err := c.Client.UpdateVoiceState(context.Background(), *e.GuildID(), nil, false, true); err != nil {
		if sendErr := e.CreateMessage(discord.MessageCreate{
			Content: "Failed to leave voice channel.",
			Flags:   discord.MessageFlagEphemeral,
		}); sendErr != nil {
			musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), true)
		}
		return err
	}

	if sendErr := e.CreateMessage(discord.MessageCreate{
		Content: "Left voice channel.",
	}); sendErr != nil {
		musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), false)
	}
	musicbot.AutoRemove(e)
	return nil
}

func (c *Commands) Ping(data discord.SlashCommandInteractionData, e *handler.CommandEvent) error {
	if sendErr := e.CreateMessage(discord.MessageCreate{
		Content: "Pong!",
	}); sendErr != nil {
		musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), false)
	}
	return nil
}
