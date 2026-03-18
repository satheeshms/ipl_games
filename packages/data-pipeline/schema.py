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
"""

DROP_TABLES = """
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
