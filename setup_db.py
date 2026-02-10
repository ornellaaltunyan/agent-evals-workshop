"""Generate synthetic NBA data and compute ground-truth values for eval."""

import sqlite3
import random
import os
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REFERENCE_DATE = datetime(2025, 1, 15)
SEASON_START = datetime(2024, 10, 22)
SEASON_END = datetime(2025, 1, 14)
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "nba.db")

random.seed(42)

# 30 real NBA teams: (team_id, name, city, abbreviation, conference, division, founded_year, arena_name)
TEAMS = [
    (1,  "Celtics",       "Boston",         "BOS", "Eastern", "Atlantic",  1946, "TD Garden"),
    (2,  "Nets",          "Brooklyn",        "BKN", "Eastern", "Atlantic",  1976, "Barclays Center"),
    (3,  "Knicks",        "New York",        "NYK", "Eastern", "Atlantic",  1946, "Madison Square Garden"),
    (4,  "76ers",         "Philadelphia",    "PHI", "Eastern", "Atlantic",  1946, "Wells Fargo Center"),
    (5,  "Raptors",       "Toronto",         "TOR", "Eastern", "Atlantic",  1995, "Scotiabank Arena"),
    (6,  "Bulls",         "Chicago",         "CHI", "Eastern", "Central",   1966, "United Center"),
    (7,  "Cavaliers",     "Cleveland",       "CLE", "Eastern", "Central",   1970, "Rocket Mortgage FieldHouse"),
    (8,  "Pistons",       "Detroit",         "DET", "Eastern", "Central",   1941, "Little Caesars Arena"),
    (9,  "Pacers",        "Indiana",         "IND", "Eastern", "Central",   1976, "Gainbridge Fieldhouse"),
    (10, "Bucks",         "Milwaukee",       "MIL", "Eastern", "Central",   1968, "Fiserv Forum"),
    (11, "Hawks",         "Atlanta",         "ATL", "Eastern", "Southeast", 1946, "State Farm Arena"),
    (12, "Hornets",       "Charlotte",       "CHA", "Eastern", "Southeast", 1988, "Spectrum Center"),
    (13, "Heat",          "Miami",           "MIA", "Eastern", "Southeast", 1988, "Kaseya Center"),
    (14, "Magic",         "Orlando",         "ORL", "Eastern", "Southeast", 1989, "Kia Center"),
    (15, "Wizards",       "Washington",      "WAS", "Eastern", "Southeast", 1961, "Capital One Arena"),
    (16, "Nuggets",       "Denver",          "DEN", "Western", "Northwest", 1976, "Ball Arena"),
    (17, "Timberwolves",  "Minnesota",       "MIN", "Western", "Northwest", 1989, "Target Center"),
    (18, "Thunder",       "Oklahoma City",   "OKC", "Western", "Northwest", 2008, "Paycom Center"),
    (19, "Trail Blazers", "Portland",        "POR", "Western", "Northwest", 1970, "Moda Center"),
    (20, "Jazz",          "Utah",            "UTA", "Western", "Northwest", 1974, "Delta Center"),
    (21, "Warriors",      "Golden State",    "GSW", "Western", "Pacific",   1946, "Chase Center"),
    (22, "Clippers",      "Los Angeles",     "LAC", "Western", "Pacific",   1970, "Crypto.com Arena"),
    (23, "Lakers",        "Los Angeles",     "LAL", "Western", "Pacific",   1948, "Crypto.com Arena"),
    (24, "Suns",          "Phoenix",         "PHX", "Western", "Pacific",   1968, "Footprint Center"),
    (25, "Kings",         "Sacramento",      "SAC", "Western", "Pacific",   1945, "Golden 1 Center"),
    (26, "Mavericks",     "Dallas",          "DAL", "Western", "Southwest", 1980, "American Airlines Center"),
    (27, "Rockets",       "Houston",         "HOU", "Western", "Southwest", 1967, "Toyota Center"),
    (28, "Grizzlies",     "Memphis",         "MEM", "Western", "Southwest", 1995, "FedExForum"),
    (29, "Pelicans",      "New Orleans",     "NOP", "Western", "Southwest", 2002, "Smoothie King Center"),
    (30, "Spurs",         "San Antonio",     "SAS", "Western", "Southwest", 1976, "Frost Bank Center"),
]

FIRST_NAMES = [
    "James", "Marcus", "DeShawn", "Tyler", "Jordan", "Kevin", "Andre", "Jaylen",
    "Trae", "Donovan", "Devin", "Luka", "Ja", "Zion", "Paolo", "Cade",
    "Evan", "Isaiah", "Derrick", "Chris", "Paul", "Anthony", "Karl", "Damian",
    "Bradley", "Khris", "Bam", "Nikola", "Rudy", "Draymond", "Stephen", "Klay",
    "LeBron", "Kawhi", "Jimmy", "Victor", "Shai", "Jayson", "Al", "Brook",
]

LAST_NAMES = [
    "Johnson", "Williams", "Davis", "Thompson", "Smith", "Brown", "Jones", "Garcia",
    "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White",
    "Harris", "Martin", "Lee", "Walker", "Hall", "Allen", "Young", "King",
    "Wright", "Scott", "Green", "Baker", "Adams", "Nelson",
]

COLLEGES = [
    "Duke", "Kentucky", "Kansas", "North Carolina", "UCLA", "Michigan State",
    "Arizona", "Texas", "Connecticut", "Gonzaga", "Louisville", "Indiana",
    "Syracuse", "Georgetown", "Notre Dame", "Florida", "Ohio State", "Michigan",
    "Villanova", "Memphis", "LSU", "Arkansas", "Oklahoma", "USC", "Baylor",
]

# Per-36-minute base stats by position at skill_factor=1.0
POSITION_PROFILES = {
    "PG": {"pts": 22, "reb": 4,  "ast": 9,  "stl": 1.5, "blk": 0.3, "to": 3.0, "fg_pct": 0.45, "three_rate": 0.42},
    "SG": {"pts": 24, "reb": 4,  "ast": 5,  "stl": 1.5, "blk": 0.5, "to": 2.5, "fg_pct": 0.46, "three_rate": 0.40},
    "SF": {"pts": 22, "reb": 7,  "ast": 4,  "stl": 1.2, "blk": 0.8, "to": 2.0, "fg_pct": 0.47, "three_rate": 0.30},
    "PF": {"pts": 18, "reb": 10, "ast": 2.5,"stl": 0.8, "blk": 1.5, "to": 2.0, "fg_pct": 0.50, "three_rate": 0.15},
    "C":  {"pts": 16, "reb": 13, "ast": 2,  "stl": 0.7, "blk": 2.5, "to": 2.0, "fg_pct": 0.54, "three_rate": 0.05},
}

# Positions assigned in order for each team's 15 roster slots
# 3 players per position: depth 1 (starter), depth 2 (first sub), depth 3 (second sub)
ROSTER_POSITIONS = ["PG", "SG", "SF", "PF", "C"] * 3


def create_tables(conn):
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS seasons (
            season_id   INTEGER PRIMARY KEY,
            year        TEXT NOT NULL,
            start_date  TEXT NOT NULL,
            end_date    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS teams (
            team_id      INTEGER PRIMARY KEY,
            name         TEXT NOT NULL,
            city         TEXT NOT NULL,
            abbreviation TEXT NOT NULL,
            conference   TEXT NOT NULL,
            division     TEXT NOT NULL,
            founded_year INTEGER NOT NULL,
            arena_name   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS players (
            player_id   INTEGER PRIMARY KEY,
            first_name  TEXT NOT NULL,
            last_name   TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            height      TEXT NOT NULL,
            weight      INTEGER NOT NULL,
            position    TEXT NOT NULL,
            college     TEXT,
            draft_year  INTEGER,
            draft_round INTEGER,
            draft_pick  INTEGER
        );

        CREATE TABLE IF NOT EXISTS games (
            game_id          INTEGER PRIMARY KEY,
            game_date        TEXT NOT NULL,
            season           TEXT NOT NULL,
            home_team_id     INTEGER NOT NULL,
            away_team_id     INTEGER NOT NULL,
            home_score       INTEGER NOT NULL,
            away_score       INTEGER NOT NULL,
            arena            TEXT NOT NULL,
            attendance       INTEGER NOT NULL,
            overtime_periods INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
            FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
        );

        CREATE TABLE IF NOT EXISTS rosters (
            roster_id    INTEGER PRIMARY KEY,
            player_id    INTEGER NOT NULL,
            team_id      INTEGER NOT NULL,
            season       TEXT NOT NULL,
            jersey_number INTEGER NOT NULL,
            start_date   TEXT NOT NULL,
            end_date     TEXT,
            FOREIGN KEY (player_id) REFERENCES players(player_id),
            FOREIGN KEY (team_id)   REFERENCES teams(team_id)
        );

        CREATE TABLE IF NOT EXISTS player_game_stats (
            player_game_stat_id INTEGER PRIMARY KEY,
            game_id     INTEGER NOT NULL,
            player_id   INTEGER NOT NULL,
            team_id     INTEGER NOT NULL,
            minutes_played INTEGER NOT NULL,
            points      INTEGER NOT NULL,
            rebounds    INTEGER NOT NULL,
            assists     INTEGER NOT NULL,
            steals      INTEGER NOT NULL,
            blocks      INTEGER NOT NULL,
            turnovers   INTEGER NOT NULL,
            fouls       INTEGER NOT NULL,
            fg_made     INTEGER NOT NULL,
            fg_attempted INTEGER NOT NULL,
            three_made  INTEGER NOT NULL,
            three_attempted INTEGER NOT NULL,
            ft_made     INTEGER NOT NULL,
            ft_attempted INTEGER NOT NULL,
            plus_minus  INTEGER NOT NULL,
            FOREIGN KEY (game_id)   REFERENCES games(game_id),
            FOREIGN KEY (player_id) REFERENCES players(player_id),
            FOREIGN KEY (team_id)   REFERENCES teams(team_id)
        );

        CREATE TABLE IF NOT EXISTS team_game_stats (
            team_game_stat_id INTEGER PRIMARY KEY,
            game_id       INTEGER NOT NULL,
            team_id       INTEGER NOT NULL,
            points        INTEGER NOT NULL,
            rebounds      INTEGER NOT NULL,
            assists       INTEGER NOT NULL,
            turnovers     INTEGER NOT NULL,
            fg_percentage REAL NOT NULL,
            three_percentage REAL NOT NULL,
            ft_percentage REAL NOT NULL,
            FOREIGN KEY (game_id) REFERENCES games(game_id),
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
        );
    """)
    conn.commit()


def generate_seasons(conn):
    conn.execute(
        "INSERT INTO seasons VALUES (?, ?, ?, ?)",
        (1, "2024-25", SEASON_START.strftime("%Y-%m-%d"), SEASON_END.strftime("%Y-%m-%d")),
    )
    conn.commit()


def generate_teams(conn):
    conn.executemany("INSERT INTO teams VALUES (?, ?, ?, ?, ?, ?, ?, ?)", TEAMS)
    conn.commit()


def _height_str(pos):
    if pos == "C":
        feet, inches = 7, random.randint(0, 1)
    elif pos == "PF":
        feet, inches = 6, random.randint(8, 11)
    elif pos == "SF":
        feet, inches = 6, random.randint(6, 9)
    elif pos == "SG":
        feet, inches = 6, random.randint(3, 7)
    else:
        feet, inches = 6, random.randint(0, 4)
    return f"{feet}'{inches}\""


def _weight(pos):
    base = {"PG": 185, "SG": 200, "SF": 215, "PF": 225, "C": 245}
    return base[pos] + random.randint(-15, 20)


def generate_players(conn):
    players = []
    player_profiles = {}
    player_id = 1

    for team in TEAMS:
        team_id = team[0]
        used_numbers = set()

        for depth_group in range(3):
            for pos in ["PG", "SG", "SF", "PF", "C"]:
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                dob_base = datetime(1990, 1, 1)
                dob = dob_base + timedelta(days=random.randint(0, 365 * 14))
                college = random.choice(COLLEGES) if random.random() < 0.85 else None
                draft_year = random.randint(2010, 2023)
                draft_round = random.choices([1, 2], weights=[55, 45])[0]
                draft_pick = random.randint(1, 30) if draft_round == 1 else random.randint(1, 30)

                jersey = random.randint(0, 55)
                while jersey in used_numbers:
                    jersey = random.randint(0, 55)
                used_numbers.add(jersey)

                profile = POSITION_PROFILES[pos]
                # Starters (depth 0) get higher skill; bench gets lower
                if depth_group == 0:
                    skill = random.uniform(0.65, 1.0)
                elif depth_group == 1:
                    skill = random.uniform(0.40, 0.70)
                else:
                    skill = random.uniform(0.20, 0.45)

                player_profiles[player_id] = {
                    "pos": pos,
                    "team_id": team_id,
                    "depth": depth_group,
                    "skill": skill,
                    "jersey": jersey,
                    "pts_per36": profile["pts"] * skill,
                    "reb_per36": profile["reb"] * skill,
                    "ast_per36": profile["ast"] * skill,
                    "stl_per36": profile["stl"] * skill,
                    "blk_per36": profile["blk"] * skill,
                    "to_per36": profile["to"] * skill,
                    "fg_pct": profile["fg_pct"] * random.uniform(0.90, 1.08),
                    "three_rate": profile["three_rate"] * random.uniform(0.85, 1.15),
                }

                players.append((
                    player_id, first, last,
                    dob.strftime("%Y-%m-%d"),
                    _height_str(pos), _weight(pos),
                    pos, college, draft_year, draft_round, draft_pick,
                ))
                player_id += 1

    conn.executemany("INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", players)
    conn.commit()
    print(f"Generated {len(players)} players")
    return players, player_profiles


def generate_rosters(conn, player_profiles):
    rosters = []
    roster_id = 1
    season = "2024-25"
    start = SEASON_START.strftime("%Y-%m-%d")

    for player_id, profile in player_profiles.items():
        rosters.append((
            roster_id, player_id, profile["team_id"],
            season, profile["jersey"], start, None,
        ))
        roster_id += 1

    conn.executemany("INSERT INTO rosters VALUES (?, ?, ?, ?, ?, ?, ?)", rosters)
    conn.commit()
    print(f"Generated {len(rosters)} roster entries")


def generate_games(conn):
    """Generate a realistic NBA schedule from SEASON_START to SEASON_END."""
    team_ids = [t[0] for t in TEAMS]
    team_arena = {t[0]: t[7] for t in TEAMS}

    # Build candidate matchups (home, away) – each ordered pair once
    all_matchups = [(h, a) for h in team_ids for a in team_ids if h != a]
    random.shuffle(all_matchups)

    # Distribute games across dates (roughly 8-10 games per game day, ~5 days/week)
    current = SEASON_START
    game_dates = []
    while current <= SEASON_END:
        # ~75% of days have games (skip some Mondays/Tuesdays)
        if not (current.weekday() == 0 and random.random() < 0.55):
            game_dates.append(current)
        current += timedelta(days=1)

    # Assign matchups to dates, tracking games-per-team
    games_per_team = {t: 0 for t in team_ids}
    target_per_team = 40
    games_on_date = {}  # date -> list of (home, away)

    for matchup in all_matchups:
        home, away = matchup
        if games_per_team[home] >= target_per_team:
            continue
        if games_per_team[away] >= target_per_team:
            continue

        # Find a date where neither team already has a game
        placed = False
        for d in game_dates:
            teams_today = set()
            for h2, a2 in games_on_date.get(d, []):
                teams_today.add(h2)
                teams_today.add(a2)
            if home not in teams_today and away not in teams_today and len(games_on_date.get(d, [])) < 12:
                games_on_date.setdefault(d, []).append((home, away))
                games_per_team[home] += 1
                games_per_team[away] += 1
                placed = True
                break

        if not placed:
            # try to find any remaining date
            for d in random.sample(game_dates, min(20, len(game_dates))):
                teams_today = set()
                for h2, a2 in games_on_date.get(d, []):
                    teams_today.add(h2)
                    teams_today.add(a2)
                if home not in teams_today and away not in teams_today:
                    games_on_date.setdefault(d, []).append((home, away))
                    games_per_team[home] += 1
                    games_per_team[away] += 1
                    break

    # Flatten and insert
    games = []
    game_id = 1
    for d in sorted(games_on_date.keys()):
        for home, away in games_on_date[d]:
            home_score = random.randint(95, 135)
            away_score = random.randint(95, 135)

            overtime_periods = 0
            if abs(home_score - away_score) <= 3 and random.random() < 0.35:
                overtime_periods = random.choices([1, 2], weights=[75, 25])[0]
                bonus = random.randint(4, 12) * overtime_periods
                home_score += bonus
                away_score += bonus - random.randint(-3, 3)

            attendance = random.randint(14000, 21000)
            arena = team_arena[home]

            games.append((
                game_id, d.strftime("%Y-%m-%d"), "2024-25",
                home, away, home_score, away_score,
                arena, attendance, overtime_periods,
            ))
            game_id += 1

    conn.executemany("INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", games)
    conn.commit()
    print(f"Generated {len(games)} games")
    return games


def _player_game_stats(player_id, profile, minutes, game_pts_share, ot_periods):
    """Generate a single player's box score given minutes and their share of team pts."""
    if minutes == 0:
        return None

    pts = max(0, round(profile["pts_per36"] * minutes / 36 + random.gauss(0, 2.5)))
    reb = max(0, round(profile["reb_per36"] * minutes / 36 + random.gauss(0, 1.5)))
    ast = max(0, round(profile["ast_per36"] * minutes / 36 + random.gauss(0, 1.0)))
    stl = max(0, round(profile["stl_per36"] * minutes / 36 + random.gauss(0, 0.5)))
    blk = max(0, round(profile["blk_per36"] * minutes / 36 + random.gauss(0, 0.4)))
    to  = max(0, round(profile["to_per36"]  * minutes / 36 + random.gauss(0, 0.8)))
    fouls = min(6, max(0, round(random.gauss(2.5, 1.0))))

    # Shooting breakdown
    fg_pct = min(0.70, max(0.28, profile["fg_pct"] + random.gauss(0, 0.05)))
    three_rate = min(0.60, max(0, profile["three_rate"] + random.gauss(0, 0.05)))

    ft_pts = max(0, round(pts * random.uniform(0.10, 0.25)))
    field_pts = pts - ft_pts

    three_pts = max(0, round(field_pts * three_rate))
    two_pts   = max(0, field_pts - three_pts)

    three_made = max(0, round(three_pts / 3))
    three_att  = max(three_made, round(three_made / max(0.35, fg_pct * 0.95)))

    two_made  = max(0, round(two_pts / 2))
    two_att   = max(two_made, round(two_made / max(0.35, fg_pct)))

    fg_made = two_made + three_made
    fg_att  = two_att + three_att

    ft_made = ft_pts
    ft_att  = max(ft_made, round(ft_made / max(0.60, random.uniform(0.72, 0.92))))

    plus_minus = round(random.gauss(0, 8))

    return (
        player_id, minutes, pts, reb, ast, stl, blk, to, fouls,
        fg_made, fg_att, three_made, three_att, ft_made, ft_att, plus_minus,
    )


def generate_player_game_stats(conn, games, player_profiles):
    """Generate box score rows for every player in every game."""
    # Build team -> players list (sorted by depth)
    team_players = {}
    for pid, prof in player_profiles.items():
        team_players.setdefault(prof["team_id"], []).append((pid, prof))
    for tid in team_players:
        team_players[tid].sort(key=lambda x: (x[1]["depth"], x[0]))

    rows = []
    stat_id = 1

    for game in games:
        game_id, game_date, season, home_id, away_id, home_score, away_score, arena, attendance, ot_periods = game

        for team_id in (home_id, away_id):
            players_on_team = team_players.get(team_id, [])
            # Use up to 13 active players; depth-2 bench (indices 10-14) sometimes DNP
            active = []
            for pid, prof in players_on_team:
                if prof["depth"] < 2 or random.random() < 0.75:
                    active.append((pid, prof))

            total_minutes = 240 + ot_periods * 25

            # Assign minutes
            minute_budget = total_minutes
            player_minutes = []
            for i, (pid, prof) in enumerate(active):
                if prof["depth"] == 0:
                    mins = random.randint(28, 38)
                elif prof["depth"] == 1:
                    mins = random.randint(14, 24)
                else:
                    mins = random.randint(4, 12)
                player_minutes.append(mins)

            # Scale to total_minutes
            total_assigned = sum(player_minutes)
            if total_assigned > 0:
                scale = total_minutes / total_assigned
                player_minutes = [max(1, round(m * scale)) for m in player_minutes]

            for i, (pid, prof) in enumerate(active):
                mins = player_minutes[i]
                result = _player_game_stats(pid, prof, mins, None, ot_periods)
                if result is None:
                    continue
                (
                    pid2, minutes, pts, reb, ast, stl, blk, to, fouls,
                    fg_made, fg_att, three_made, three_att, ft_made, ft_att, plus_minus,
                ) = result
                rows.append((
                    stat_id, game_id, pid, team_id,
                    minutes, pts, reb, ast, stl, blk, to, fouls,
                    fg_made, fg_att, three_made, three_att, ft_made, ft_att, plus_minus,
                ))
                stat_id += 1

    conn.executemany("INSERT INTO player_game_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    print(f"Generated {len(rows)} player game stat rows")
    return rows


def generate_team_game_stats(conn, games):
    """Generate team-level game stats, aggregated from player_game_stats."""
    cur = conn.cursor()
    rows = []
    stat_id = 1

    for game in games:
        game_id, _, _, home_id, away_id, home_score, away_score, _, _, _ = game

        for team_id, team_score in ((home_id, home_score), (away_id, away_score)):
            cur.execute("""
                SELECT
                    SUM(rebounds),
                    SUM(assists),
                    SUM(turnovers),
                    SUM(fg_made), SUM(fg_attempted),
                    SUM(three_made), SUM(three_attempted),
                    SUM(ft_made), SUM(ft_attempted)
                FROM player_game_stats
                WHERE game_id = ? AND team_id = ?
            """, (game_id, team_id))
            agg = cur.fetchone()
            if agg is None or agg[0] is None:
                continue

            reb, ast, to, fg_m, fg_a, thr_m, thr_a, ft_m, ft_a = agg

            fg_pct  = round(fg_m / fg_a, 3) if fg_a > 0 else 0.0
            thr_pct = round(thr_m / thr_a, 3) if thr_a > 0 else 0.0
            ft_pct  = round(ft_m / ft_a, 3) if ft_a > 0 else 0.0

            rows.append((
                stat_id, game_id, team_id,
                team_score, reb or 0, ast or 0, to or 0,
                fg_pct, thr_pct, ft_pct,
            ))
            stat_id += 1

    conn.executemany("INSERT INTO team_game_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    print(f"Generated {len(rows)} team game stat rows")


def compute_ground_truth(conn):
    cur = conn.cursor()

    print("\n" + "=" * 60)
    print("GROUND TRUTH VALUES (for eval dataset)")
    print("=" * 60)

    # 1. Player with most total points this season
    cur.execute("""
        SELECT p.first_name || ' ' || p.last_name AS player,
               SUM(pgs.points) AS total_points
        FROM player_game_stats pgs
        JOIN players p ON pgs.player_id = p.player_id
        GROUP BY pgs.player_id
        ORDER BY total_points DESC
        LIMIT 1
    """)
    top_scorer = cur.fetchone()
    print(f"\n1. Top scorer: {top_scorer[0]} ({top_scorer[1]} points)")

    # 2. Team with most wins this season
    cur.execute("""
        SELECT t.name, COUNT(*) AS wins
        FROM games g
        JOIN teams t ON (
            (g.home_score > g.away_score AND g.home_team_id = t.team_id)
            OR (g.away_score > g.home_score AND g.away_team_id = t.team_id)
        )
        GROUP BY t.team_id
        ORDER BY wins DESC
        LIMIT 1
    """)
    top_team = cur.fetchone()
    print(f"\n2. Team with most wins: {top_team[0]} ({top_team[1]} wins)")

    # 3. Average team score per game
    cur.execute("""
        SELECT ROUND(AVG(points), 2)
        FROM team_game_stats
    """)
    avg_score = cur.fetchone()[0]
    print(f"\n3. Average team score per game: {avg_score}")

    # 4. Player with highest single-game score
    cur.execute("""
        SELECT p.first_name || ' ' || p.last_name AS player,
               pgs.points
        FROM player_game_stats pgs
        JOIN players p ON pgs.player_id = p.player_id
        ORDER BY pgs.points DESC
        LIMIT 1
    """)
    top_single = cur.fetchone()
    print(f"\n4. Highest single-game score: {top_single[0]} ({top_single[1]} pts)")

    # 5. Total games with overtime
    cur.execute("""
        SELECT COUNT(*)
        FROM games
        WHERE overtime_periods > 0
    """)
    ot_games = cur.fetchone()[0]
    print(f"\n5. Games with overtime: {ot_games}")

    # 6. Team with highest average FG% this season
    cur.execute("""
        SELECT t.name, ROUND(AVG(tgs.fg_percentage), 3) AS avg_fg
        FROM team_game_stats tgs
        JOIN teams t ON tgs.team_id = t.team_id
        GROUP BY tgs.team_id
        ORDER BY avg_fg DESC
        LIMIT 1
    """)
    top_fg = cur.fetchone()
    print(f"\n6. Best FG% team: {top_fg[0]} ({top_fg[1]})")

    # 7. Player averaging most assists per game (min 10 games)
    cur.execute("""
        SELECT p.first_name || ' ' || p.last_name AS player,
               ROUND(AVG(pgs.assists), 2) AS avg_ast,
               COUNT(*) AS games_played
        FROM player_game_stats pgs
        JOIN players p ON pgs.player_id = p.player_id
        GROUP BY pgs.player_id
        HAVING COUNT(*) >= 10
        ORDER BY avg_ast DESC
        LIMIT 1
    """)
    top_ast = cur.fetchone()
    print(f"\n7. Most assists per game: {top_ast[0]} ({top_ast[1]} apg, {top_ast[2]} games)")

    # 8. Total games played this season
    cur.execute("SELECT COUNT(*) FROM games")
    total_games = cur.fetchone()[0]
    print(f"\n8. Total games played: {total_games}")

    # 9. Conference with more combined wins
    cur.execute("""
        SELECT t.conference, COUNT(*) AS wins
        FROM games g
        JOIN teams t ON (
            (g.home_score > g.away_score AND g.home_team_id = t.team_id)
            OR (g.away_score > g.home_score AND g.away_team_id = t.team_id)
        )
        GROUP BY t.conference
        ORDER BY wins DESC
        LIMIT 1
    """)
    top_conf = cur.fetchone()
    print(f"\n9. Conference with more wins: {top_conf[0]} ({top_conf[1]} wins)")

    # 10. Player with most rebounds per game (min 10 games)
    cur.execute("""
        SELECT p.first_name || ' ' || p.last_name AS player,
               ROUND(AVG(pgs.rebounds), 2) AS avg_reb,
               COUNT(*) AS games_played
        FROM player_game_stats pgs
        JOIN players p ON pgs.player_id = p.player_id
        GROUP BY pgs.player_id
        HAVING COUNT(*) >= 10
        ORDER BY avg_reb DESC
        LIMIT 1
    """)
    top_reb = cur.fetchone()
    print(f"\n10. Most rebounds per game: {top_reb[0]} ({top_reb[1]} rpg, {top_reb[2]} games)")

    print("\n" + "=" * 60)

    return {
        "top_scorer": top_scorer,
        "top_team": top_team,
        "avg_score": avg_score,
        "top_single": top_single,
        "ot_games": ot_games,
        "top_fg": top_fg,
        "top_ast": top_ast,
        "total_games": total_games,
        "top_conf": top_conf,
        "top_reb": top_reb,
    }


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    generate_seasons(conn)
    generate_teams(conn)
    _, player_profiles = generate_players(conn)
    generate_rosters(conn, player_profiles)
    games = generate_games(conn)
    generate_player_game_stats(conn, games, player_profiles)
    generate_team_game_stats(conn, games)
    ground_truth = compute_ground_truth(conn)
    conn.close()

    print(f"\nDatabase created at: {DB_PATH}")
    return ground_truth


if __name__ == "__main__":
    main()
