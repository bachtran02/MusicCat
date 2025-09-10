package musicbot

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"github.com/disgoorg/disgolink/v3/lavalink"
	"github.com/disgoorg/snowflake/v2"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
)

type Playlist struct {
	ID        int          `db:"id"`
	Name      string       `db:"name"`
	OwnerID   snowflake.ID `db:"owner_id"`
	CreatedAt time.Time    `db:"created_at"`
}

type PlaylistTrack struct {
	ID         int            `db:"id"`
	PlaylistID int            `db:"playlist_id"`
	TrackTitle string         `db:"track_title"`
	Track      lavalink.Track `db:"track"`
	AddedAt    time.Time      `db:"added_at"`
	AddedBy    string         `db:"added_by"`
}

func (d *DB) scanPlaylists(rows pgx.Rows) ([]Playlist, error) {
	defer rows.Close()

	var playlists []Playlist
	for rows.Next() {
		var playlist Playlist
		err := rows.Scan(&playlist.ID, &playlist.Name, &playlist.OwnerID, &playlist.CreatedAt)
		if err != nil {
			slog.Error("failed to parse playlist", slog.Any("err", err))
			continue
		}
		playlists = append(playlists, playlist)
	}
	return playlists, nil
}

func (d *DB) scanTracks(rows pgx.Rows) ([]PlaylistTrack, error) {
	defer rows.Close()

	var playlistTracks []PlaylistTrack
	for rows.Next() {
		var (
			track    PlaylistTrack
			rawTrack json.RawMessage
			err      error
		)
		err = rows.Scan(&track.ID, &track.PlaylistID, &track.TrackTitle, &rawTrack, &track.AddedAt, &track.AddedBy)
		if err != nil {
			slog.Error("failed to parse playlist track from database", slog.Any("err", err))
			continue
		}
		err = json.Unmarshal(rawTrack, &track.Track)
		if err != nil {
			slog.Error("failed to decode track object", slog.Any("err", err))
			continue
		}
		playlistTracks = append(playlistTracks, track)
	}
	return playlistTracks, nil
}

func (d *DB) buildPlaylistQuery(query string, userID snowflake.ID, limit int) (string, []interface{}) {
	if query == "" {
		// return all playlists by user
		return "SELECT * FROM playlists WHERE owner_id = $1 LIMIT $2", []interface{}{userID, limit}
	} else {
		// return playlists by user that match search term
		return "SELECT * FROM playlists WHERE owner_id = $1 AND name ILIKE $2 || '%' LIMIT $3;", []interface{}{userID, query, limit}
		// TODO: add support for string distance
	}
}

func (d *DB) CreatePlaylist(ctx context.Context, userID snowflake.ID, username string, playlistName string) error {
	_, err := d.Pool.Exec(ctx, "INSERT INTO playlists (owner_id, name) VALUES ($1, $2)", userID, playlistName)
	if err != nil {
		if pgErr, ok := err.(*pgconn.PgError); ok {
			// Check if it's a unique constraint violation error
			if pgErr.Code == "23505" {
				return fmt.Errorf("playlist with name \"%s\" already exists", playlistName)
			}
		}
		return err
	}
	return nil
}

func (d *DB) DeletePlaylist(ctx context.Context, playlistId int) error {
	_, err := d.Pool.Exec(ctx, "DELETE FROM playlists WHERE id = $1", playlistId)
	return err
}

func (d *DB) SearchPlaylist(ctx context.Context, userID snowflake.ID, query string, limit int) ([]Playlist, error) {
	queryString, args := d.buildPlaylistQuery(query, userID, limit)
	rows, err := d.Pool.Query(ctx, queryString, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	return d.scanPlaylists(rows)
}

func (d *DB) GetPlaylist(ctx context.Context, userId int, playlistId int) (Playlist, []PlaylistTrack, error) {

	row := d.Pool.QueryRow(ctx, "SELECT * FROM playlists WHERE id = $1 AND owner_id = $2", playlistId, userId)

	var playlist Playlist
	if err := row.Scan(&playlist.ID, &playlist.Name, &playlist.OwnerID, &playlist.CreatedAt); err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return Playlist{}, nil, fmt.Errorf("playlist not found in database")
		}
		return Playlist{}, nil, err
	}

	rows, err := d.Pool.Query(ctx, "SELECT * FROM playlist_tracks WHERE playlist_id = $1", playlistId)
	if err != nil {
		return playlist, nil, err
	}
	defer rows.Close()

	playlistTracks, err := d.scanTracks(rows)
	if err != nil {
		return Playlist{}, nil, err
	}
	return playlist, playlistTracks, nil
}

func (d *DB) AddTracksToPlaylist(ctx context.Context, playlistId int, userId snowflake.ID, tracks []lavalink.Track) error {

	if len(tracks) == 0 {
		return nil
	}

	query := "INSERT INTO playlist_tracks (playlist_id, track_title, added_by, track) VALUES "
	values := []any{}

	for i, track := range tracks {
		if i > 0 {
			query += ", "
		}
		query += fmt.Sprintf("($1, $%d, $%d, $%d)", i*3+2, i*3+3, i*3+4)
		values = append(values, track.Info.Title, userId, track)
	}
	query += ";" // End the query

	values = append([]any{playlistId}, values...)

	_, err := d.Pool.Exec(ctx, query, values...)
	return err
}

func (d *DB) RemoveTrackFromPlaylist(ctx context.Context, trackId int, userId snowflake.ID) error {
	_, err := d.Pool.Exec(ctx, "DELETE FROM playlist_tracks WHERE id = $1 AND added_by = $2", trackId, userId)
	return err
}
