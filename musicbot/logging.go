package musicbot

import (
	"log/slog"
)

func LogPlayerInteraction(button string, guildID string, userID string) {
	slog.Info("player interaction",
		slog.String("button", button),
		slog.String("guild_id", guildID),
		slog.String("user_id", userID),
	)
}

func LogCommand(command string, guildID string, userID string) {
	/* log a command execution */
	slog.Info("command executed",
		slog.String("command", command),
		slog.String("guild_id", guildID),
		slog.String("user_id", userID),
	)
}

func LogSendError(err error, guildID string, userID string, ephemeral bool) {
	/* log an error when a failed attempt to send a message occurs. */
	slog.Error("failed to send message",
		slog.Any("error", err),
		slog.String("guild_id", guildID),
		slog.String("user_id", userID),
		slog.Bool("ephemeral", ephemeral),
	)
}

func LogUpdateError(err error, guildID string, userID string) {
	/* log an error when a failed attempt to update a message occurs. */
	slog.Error("failed to update message",
		slog.Any("error", err),
		slog.String("guild_id", guildID),
		slog.String("user_id", userID),
	)
}

func LogCommandError(err error, command string, guildID string, userID string) {
	/* log a error when a failed attempt to run a command */
	slog.Error("failed to run command",
		slog.Any("error", err),
		slog.String("command", command),
		slog.String("guild_id", guildID),
		slog.String("user_id", userID),
	)
}

func LogDeleteError(err error, guildID string, channelID string, messageID string) {
	/* log an error when a failed attempt to delete a message occurs. */
	slog.Error("failed to delete message",
		slog.Any("error", err),
		slog.String("guild_id", guildID),
		slog.String("channel_id", channelID),
		slog.String("message_id", messageID),
	)
}
