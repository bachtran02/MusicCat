CREATE TABLE IF NOT EXISTS playlists
(
    id          BIGSERIAL       PRIMARY KEY,
    name        VARCHAR(255)    NOT NULL,
    owner_id    BIGINT          NOT NULL,
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    UNIQUE      (name, owner_id)
);

CREATE TABLE IF NOT EXISTS playlist_tracks
(
    id          BIGSERIAL       PRIMARY KEY,
    playlist_id BIGINT          NOT NULL REFERENCES playlists (id) ON DELETE CASCADE,
    track_title VARCHAR(255)    NOT NULL,
    track       JSONB           NOT NULL,
    added_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    added_by    BIGINT          NOT NULL
);