package commands

import (
	"MusicCatGo/musicbot"
	"fmt"

	"github.com/disgoorg/disgo/discord"
	"github.com/disgoorg/disgo/handler"
	"github.com/disgoorg/disgolink/v3/lavalink"
	"github.com/disgoorg/json"
	"github.com/disgoorg/lavasrc-plugin"
)

var playlist = discord.SlashCommandCreate{
	Name:        "list",
	Description: "playlist commands",
	Options: []discord.ApplicationCommandOption{
		discord.ApplicationCommandOptionSubCommand{
			Name:        "create",
			Description: "Create new playlist",
			Options: []discord.ApplicationCommandOption{
				discord.ApplicationCommandOptionString{
					Name:        "playlist_name",
					Description: "Playlist name",
					Required:    true,
				},
			}},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "delete",
			Description: "Delete playlist",
			Options: []discord.ApplicationCommandOption{
				discord.ApplicationCommandOptionInt{
					Name:         "playlist",
					Description:  "Playlist name",
					Required:     true,
					Autocomplete: true,
				},
			}},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "list",
			Description: "List playlist",
		},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "add",
			Description: "Add track(s) to playlist",
			Options: []discord.ApplicationCommandOption{
				discord.ApplicationCommandOptionString{
					Name:         "query",
					Description:  "Search query",
					Required:     true,
					Autocomplete: true,
				},
				discord.ApplicationCommandOptionInt{
					Name:         "playlist",
					Description:  "Playlist name",
					Required:     true,
					Autocomplete: true,
				},
				discord.ApplicationCommandOptionString{
					Name:        "source",
					Description: "Source to search from",
					Required:    false,
					Choices:     searchSourceChoices,
				},
				discord.ApplicationCommandOptionString{
					Name:        "type",
					Description: "Type of search",
					Required:    false,
					Choices:     searchTypeChoices,
				},
			}},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "remove",
			Description: "Remove track from playlist",
			Options: []discord.ApplicationCommandOption{
				discord.ApplicationCommandOptionInt{
					Name:         "playlist",
					Description:  "Playlist to remove track from",
					Required:     true,
					Autocomplete: true,
				},
				discord.ApplicationCommandOptionInt{
					Name:         "track",
					Description:  "Track to remove",
					Required:     true,
					Autocomplete: true,
				},
			},
		},
	}}

func (c *Commands) PlaylistAutocomplete(e *handler.AutocompleteEvent) error {
	var (
		limit = 10
		query = e.Data.String("playlist")
	)

	playlists, err := c.Db.SearchPlaylist(e.Ctx, e.User().ID, query, limit)
	if err != nil {
		return e.AutocompleteResult(nil)
	}

	choices := make([]discord.AutocompleteChoice, 0)
	for _, playlist := range playlists {
		choices = append(choices, discord.AutocompleteChoiceInt{
			Name:  playlist.Name,
			Value: playlist.ID,
		})
	}
	return e.AutocompleteResult(choices)
}

func (c *Commands) PlaylistTrackAutocomplete(e *handler.AutocompleteEvent) error {
	var (
		trackLimit = 10
		playlistId = e.Data.Int("playlist")
	)

	/* playlist not selected yet or invalid */
	if playlistId <= 0 {
		return e.AutocompleteResult(nil)
	}

	// Fetch playlist info
	_, playlistTracks, err := c.Db.GetPlaylist(e.Ctx, int(e.User().ID), playlistId)
	if err != nil || len(playlistTracks) == 0 {
		return e.AutocompleteResult(nil)
	}

	choices := make([]discord.AutocompleteChoice, 0)
	numChoices := min(len(playlistTracks), trackLimit)
	for _, playlistTrack := range playlistTracks[:numChoices] {
		choices = append(choices, discord.AutocompleteChoiceInt{
			Name:  playlistTrack.TrackTitle,
			Value: playlistTrack.ID,
		})
	}
	return e.AutocompleteResult(choices)
}

func (c *Commands) AddPlaylistTrackAutocomplete(e *handler.AutocompleteEvent) error {

	focusedOption := e.Data.Focused()
	switch focusedOption.Name {
	case "playlist":
		return c.PlaylistAutocomplete(e)
	case "query":
		return c.SearchAutocomplete(e)
	}
	return nil
}

func (c *Commands) RemovePlaylistTrackAutocomplete(e *handler.AutocompleteEvent) error {
	focusedOption := e.Data.Focused()
	switch focusedOption.Name {
	case "playlist":
		return c.PlaylistAutocomplete(e)
	case "track":
		return c.PlaylistTrackAutocomplete(e)
	}
	return nil
}

func (c *Commands) CreatePlaylist(data discord.SlashCommandInteractionData, e *handler.CommandEvent) error {
	var (
		playlistName = data.String("playlist_name")
	)

	/* deferring message */
	if err := e.DeferCreateMessage(false); err != nil {
		return err
	}

	err := c.Db.CreatePlaylist(e.Ctx, e.User().ID, e.User().Username, playlistName)
	if err != nil {
		if _, updateError := e.UpdateInteractionResponse(discord.MessageUpdate{
			Content: json.Ptr("Failed to create playlist."),
		}); updateError != nil {
			musicbot.LogUpdateError(updateError, e.GuildID().String(), e.User().ID.String())
		}
		return err
	}
	if _, updateErr := e.UpdateInteractionResponse(discord.MessageUpdate{
		Embeds: &[]discord.Embed{{Description: fmt.Sprintf("📋 Playlist `%s` created", playlistName)}},
	}); updateErr != nil {
		musicbot.LogUpdateError(updateErr, e.GuildID().String(), e.User().ID.String())
	}
	musicbot.AutoRemove(e)
	return nil
}

func (c *Commands) DeletePlaylist(data discord.SlashCommandInteractionData, e *handler.CommandEvent) error {
	var (
		playlistId = data.Int("playlist")
	)

	/* deferring message */
	if err := e.DeferCreateMessage(false); err != nil {
		return err
	}

	err := c.Db.DeletePlaylist(e.Ctx, playlistId)
	if err != nil {
		if _, updateError := e.UpdateInteractionResponse(discord.MessageUpdate{
			Content: json.Ptr("Failed to remove playlist."),
		}); updateError != nil {
			musicbot.LogUpdateError(updateError, e.GuildID().String(), e.User().ID.String())
		}
		return err
	}
	if _, updateError := e.UpdateInteractionResponse(discord.MessageUpdate{
		Embeds: &[]discord.Embed{{Description: "📋 Playlist deleted"}},
	}); updateError != nil {
		musicbot.LogUpdateError(updateError, e.GuildID().String(), e.User().ID.String())
	}
	musicbot.AutoRemove(e)
	return nil
}

func (c *Commands) ListPlaylists(data discord.SlashCommandInteractionData, e *handler.CommandEvent) error {
	var (
		playlistSearchLimit = 10
	)

	/* deferring message */
	if err := e.DeferCreateMessage(false); err != nil {
		return err
	}

	playlists, err := c.Db.SearchPlaylist(e.Ctx, e.User().ID, "", playlistSearchLimit)
	if err != nil {
		if _, updateErr := e.UpdateInteractionResponse(discord.MessageUpdate{
			Content: json.Ptr("Failed to retrieve user playlists."),
		}); updateErr != nil {
			musicbot.LogUpdateError(updateErr, e.GuildID().String(), e.User().ID.String())
		}
		return err
	}

	if len(playlists) == 0 {
		if _, updateErr := e.UpdateInteractionResponse(discord.MessageUpdate{
			Content: json.Ptr("You don't have any playlist."),
		}); updateErr != nil {
			musicbot.LogUpdateError(updateErr, e.GuildID().String(), e.User().ID.String())
		}
		return nil
	}

	content := fmt.Sprintf("<@%s>'s playlists\n", e.User().ID)
	for _, playlist := range playlists {
		content += fmt.Sprintf(
			"- `%s` <t:%d:R>\n", playlist.Name, playlist.CreatedAt.Unix())
	}

	embed := discord.NewEmbedBuilder().
		SetTitle("Playlists").
		SetDescription(content)

	if _, updateErr := e.UpdateInteractionResponse(discord.MessageUpdate{
		Embeds: &[]discord.Embed{embed.Build()},
	}); updateErr != nil {
		musicbot.LogUpdateError(updateErr, e.GuildID().String(), e.User().ID.String())
	}
	return nil
}

func (c *Commands) AddPlaylistTrack(data discord.SlashCommandInteractionData, e *handler.CommandEvent) error {
	var (
		playlistID = data.Int("playlist")
		query      = data.String("query")
	)

	if !urlPattern.MatchString(query) {
		if sendErr := e.CreateMessage(discord.MessageCreate{
			Content: "Please enter a valid URL or use search autocomplete to add to playlist.",
			Flags:   discord.MessageFlagEphemeral,
		}); sendErr != nil {
			musicbot.LogSendError(sendErr, e.GuildID().String(), e.User().ID.String(), true)
		}
		return nil
	}

	/* deferring message */
	if err := e.DeferCreateMessage(false); err != nil {
		return err
	}

	result, err := c.Lavalink.BestNode().LoadTracks(e.Ctx, query)
	if err != nil {
		return fmt.Errorf("failed to load tracks from Lavalink for query '%s': %w", query, err)
	}

	playlist, _, err := c.Db.GetPlaylist(e.Ctx, int(e.User().ID), playlistID)
	if err != nil {
		if _, updateErr := e.UpdateInteractionResponse(discord.MessageUpdate{
			Content: json.Ptr("Failed to retrieve playlist."),
		}); updateErr != nil {
			musicbot.LogUpdateError(updateErr, e.GuildID().String(), e.User().ID.String())
		}
		return err
	}

	switch loadData := result.Data.(type) {
	case lavalink.Track:
		if err := c.Db.AddTracksToPlaylist(e.Ctx, playlistID, e.User().ID, []lavalink.Track{loadData}); err != nil {
			return err
		}
		if _, updateErr := e.UpdateInteractionResponse(discord.MessageUpdate{
			Embeds: &[]discord.Embed{{
				Description: fmt.Sprintf("[%s](%s) added to playlist `%s`",
					loadData.Info.Title, *loadData.Info.URI, playlist.Name)}},
		}); updateErr != nil {
			musicbot.LogUpdateError(updateErr, e.GuildID().String(), e.User().ID.String())
		}

	case lavalink.Playlist:
		if err := c.Db.AddTracksToPlaylist(e.Ctx, playlistID, e.User().ID, loadData.Tracks); err != nil {
			return err
		}

		var (
			playlistInfo lavasrc.PlaylistInfo
			description  string
		)

		err = loadData.PluginInfo.Unmarshal(&playlistInfo)
		if err != nil {
			/* playlistInfo is extractable */
			description = fmt.Sprintf("Playlist %s `%d tracks` added to playlist `%s`",
				loadData.Info.Name, len(loadData.Tracks), playlist.Name)
		} else {
			/* use primitive playlist data */
			description = fmt.Sprintf("Playlist [%s](%s) `%d tracks` added to playlist `%s`",
				loadData.Info.Name, playlistInfo.URL, len(loadData.Tracks), playlist.Name)
		}

		if _, updateErr := e.UpdateInteractionResponse(discord.MessageUpdate{
			Embeds: &[]discord.Embed{{Description: description}},
		}); updateErr != nil {
			musicbot.LogUpdateError(updateErr, e.GuildID().String(), e.User().ID.String())
		}
	}

	musicbot.AutoRemove(e)
	return nil
}

func (c *Commands) RemovePlaylistTrack(data discord.SlashCommandInteractionData, e *handler.CommandEvent) error {
	var (
		trackId = data.Int("track")
	)

	/* deferring message */
	if err := e.DeferCreateMessage(false); err != nil {
		return err
	}
	defer musicbot.AutoRemove(e)

	err := c.Db.RemoveTrackFromPlaylist(e.Ctx, trackId, e.User().ID)
	if err != nil {
		return err
	}

	if _, updateErr := e.UpdateInteractionResponse(discord.MessageUpdate{
		Embeds: &[]discord.Embed{{
			Description: "Track removed from playlist."}},
	}); updateErr != nil {
		musicbot.LogUpdateError(updateErr, e.GuildID().String(), e.User().ID.String())
	}
	return nil
}
