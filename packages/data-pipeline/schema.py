"""
schema.py — SQLite schema definitions and shared DB helpers for the IPL data pipeline.
"""

import sqlite3

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS players (
    id             INTEGER PRIMARY KEY,
    name           TEXT    UNIQUE,
    nicknames      TEXT,
    nationality    TEXT,
    batting_hand   TEXT,
    bowling_hand   TEXT
);

CREATE TABLE IF NOT EXISTS teams (
    id           INTEGER PRIMARY KEY,
    name         TEXT    UNIQUE,
    short_name   TEXT,
    city         TEXT,
    home_venue   TEXT,
    active_from  INTEGER,
    active_to    INTEGER
);

CREATE TABLE IF NOT EXISTS player_teams (
    player_id  INTEGER,
    team_id    INTEGER,
    season     INTEGER,
    PRIMARY KEY (player_id, team_id, season)
);

CREATE TABLE IF NOT EXISTS awards (
    type       TEXT,
    player_id  INTEGER,
    season     INTEGER,
    PRIMARY KEY (type, season)
);

CREATE TABLE IF NOT EXISTS ipl_wins (
    team_id     INTEGER,
    season      INTEGER,
    captain_id  INTEGER,
    PRIMARY KEY (season)
);

CREATE TABLE IF NOT EXISTS venues (
    id       INTEGER PRIMARY KEY,
    name     TEXT    UNIQUE,
    city     TEXT,
    aliases  TEXT
);

CREATE TABLE IF NOT EXISTS coaches (
    id       INTEGER PRIMARY KEY,
    team_id  INTEGER REFERENCES teams(id),
    season   INTEGER,
    role     TEXT NOT NULL DEFAULT 'head',
    name     TEXT,
    UNIQUE (team_id, season, role)
);

CREATE TABLE IF NOT EXISTS five_wicket_hauls (
    player_id    INTEGER PRIMARY KEY REFERENCES players(id),
    matches      INTEGER,
    innings      INTEGER,
    balls        INTEGER,
    runs         INTEGER,
    wickets      INTEGER,
    bbi          TEXT,
    average      REAL,
    economy      REAL,
    strike_rate  REAL,
    four_w       INTEGER,
    five_w       INTEGER,
    ten_w        INTEGER
);

CREATE TABLE IF NOT EXISTS batting_career_stats (
    player_id    INTEGER PRIMARY KEY REFERENCES players(id),
    matches      INTEGER,
    innings      INTEGER,
    not_out      INTEGER,
    runs         INTEGER,
    hs           TEXT,
    average      REAL,
    balls_faced  INTEGER,
    strike_rate  REAL,
    hundreds     INTEGER,
    fifties      INTEGER,
    ducks        INTEGER,
    fours        INTEGER,
    sixes        INTEGER
);

CREATE TABLE IF NOT EXISTS bowling_career_stats (
    player_id    INTEGER PRIMARY KEY REFERENCES players(id),
    matches      INTEGER,
    innings      INTEGER,
    balls        INTEGER,
    runs         INTEGER,
    wickets      INTEGER,
    bbi          TEXT,
    average      REAL,
    economy      REAL,
    strike_rate  REAL,
    four_w       INTEGER,
    five_w       INTEGER
);

CREATE TABLE IF NOT EXISTS multi_team_players (
    player_id   INTEGER PRIMARY KEY REFERENCES players(id),
    team_count  INTEGER,
    teams       TEXT
);

CREATE TABLE IF NOT EXISTS most_ducks (
    player_id    INTEGER PRIMARY KEY REFERENCES players(id),
    matches      INTEGER,
    innings      INTEGER,
    not_out      INTEGER,
    runs         INTEGER,
    hs           TEXT,
    average      REAL,
    balls_faced  INTEGER,
    strike_rate  REAL,
    hundreds     INTEGER,
    fifties      INTEGER,
    ducks        INTEGER,
    fours        INTEGER,
    sixes        INTEGER
);

CREATE TABLE IF NOT EXISTS batting_strike_rate (
    player_id    INTEGER PRIMARY KEY REFERENCES players(id),
    rank         INTEGER,
    matches      INTEGER,
    innings      INTEGER,
    not_out      INTEGER,
    runs         INTEGER,
    hs           TEXT,
    average      REAL,
    balls_faced  INTEGER,
    strike_rate  REAL,
    hundreds     INTEGER,
    fifties      INTEGER,
    ducks        INTEGER,
    fours        INTEGER,
    sixes        INTEGER,
    teams        TEXT,
    span         TEXT
);

CREATE TABLE IF NOT EXISTS highest_batting_avg (
    player_id    INTEGER PRIMARY KEY REFERENCES players(id),
    rank         INTEGER,
    matches      INTEGER,
    innings      INTEGER,
    not_out      INTEGER,
    runs         INTEGER,
    hs           TEXT,
    average      REAL,
    balls_faced  INTEGER,
    strike_rate  REAL,
    hundreds     INTEGER,
    fifties      INTEGER,
    ducks        INTEGER,
    fours        INTEGER,
    sixes        INTEGER,
    teams        TEXT,
    span         TEXT
);

CREATE TABLE IF NOT EXISTS catches_by_fielder (
    player_id              INTEGER PRIMARY KEY REFERENCES players(id),
    rank                   INTEGER,
    matches                INTEGER,
    innings                INTEGER,
    catches                INTEGER,
    max_catches_in_innings INTEGER,
    catches_per_inning     REAL,
    teams                  TEXT,
    span                   TEXT
);

CREATE TABLE IF NOT EXISTS dismissals_by_keeper (
    player_id                  INTEGER PRIMARY KEY REFERENCES players(id),
    rank                       INTEGER,
    matches                    INTEGER,
    innings                    INTEGER,
    dismissed                  INTEGER,
    catches                    INTEGER,
    stumpings                  INTEGER,
    max_dismissals_in_innings  INTEGER,
    dismissals_per_inning      REAL,
    teams                      TEXT,
    span                       TEXT
);
"""

DROP_TABLES = """
DROP TABLE IF EXISTS dismissals_by_keeper;
DROP TABLE IF EXISTS catches_by_fielder;
DROP TABLE IF EXISTS highest_batting_avg;
DROP TABLE IF EXISTS batting_strike_rate;
DROP TABLE IF EXISTS most_ducks;
DROP TABLE IF EXISTS multi_team_players;
DROP TABLE IF EXISTS bowling_career_stats;
DROP TABLE IF EXISTS batting_career_stats;
DROP TABLE IF EXISTS five_wicket_hauls;
DROP TABLE IF EXISTS coaches;
DROP TABLE IF EXISTS awards;
DROP TABLE IF EXISTS ipl_wins;
DROP TABLE IF EXISTS player_teams;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS venues;
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    """Return a SQLite connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Execute CREATE TABLE statements against the given connection."""
    conn.executescript(CREATE_TABLES)
    conn.commit()


def drop_schema(conn: sqlite3.Connection) -> None:
    """Drop all managed tables (used by --reset)."""
    conn.executescript(DROP_TABLES)
    conn.commit()
