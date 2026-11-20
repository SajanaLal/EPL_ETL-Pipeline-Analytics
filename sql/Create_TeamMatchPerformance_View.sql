CREATE OR ALTER VIEW dw.vw_TeamMatchPerformance
AS
WITH TeamMatchRows AS
(
    -- Home appearances
    SELECT
        season,
        home_team_id AS team_id,
        home_goals AS goals_scored,
        away_goals AS goals_conceded,

        CASE WHEN home_goals > away_goals THEN 1 ELSE 0 END AS wins,
        CASE WHEN home_goals = away_goals THEN 1 ELSE 0 END AS draws,
        CASE WHEN home_goals < away_goals THEN 1 ELSE 0 END AS losses,

        CASE WHEN home_goals > away_goals THEN 1 ELSE 0 END AS home_wins,
        0 AS away_wins,

        1 AS home_matches,
        0 AS away_matches
    FROM dw.FactFixture
    WHERE home_goals IS NOT NULL
      AND away_goals IS NOT NULL

    UNION ALL

    -- Away appearances
    SELECT
        season,
        away_team_id AS team_id,
        away_goals AS goals_scored,
        home_goals AS goals_conceded,

        CASE WHEN away_goals > home_goals THEN 1 ELSE 0 END AS wins,
        CASE WHEN away_goals = home_goals THEN 1 ELSE 0 END AS draws,
        CASE WHEN away_goals < home_goals THEN 1 ELSE 0 END AS losses,

        0 AS home_wins,
        CASE WHEN away_goals > home_goals THEN 1 ELSE 0 END AS away_wins,

        0 AS home_matches,
        1 AS away_matches
    FROM dw.FactFixture
    WHERE home_goals IS NOT NULL
      AND away_goals IS NOT NULL
)
SELECT
    m.season,
    t.team_id,
    t.team_name,

    COUNT(*) AS matches_played,
    SUM(m.home_matches) AS home_matches,
    SUM(m.away_matches) AS away_matches,

    SUM(m.wins) AS wins,
    SUM(m.draws) AS draws,
    SUM(m.losses) AS losses,

    SUM(m.home_wins) AS home_wins,
    SUM(m.away_wins) AS away_wins,

    SUM(m.goals_scored) AS goals_scored,
    SUM(m.goals_conceded) AS goals_conceded,

    SUM(m.goals_scored) - SUM(m.goals_conceded)
        AS goal_difference,

    SUM(m.wins) * 3 + SUM(m.draws) AS points,

    CAST(
        1.0 * SUM(m.goals_scored) / NULLIF(COUNT(*), 0)
        AS DECIMAL(5,2)
    ) AS goals_scored_per_match,

    CAST(
        1.0 * SUM(m.goals_conceded) / NULLIF(COUNT(*), 0)
        AS DECIMAL(5,2)
    ) AS goals_conceded_per_match

FROM TeamMatchRows AS m
INNER JOIN dw.DimTeam AS t
    ON m.team_id = t.team_id

GROUP BY
    m.season,
    t.team_id,
    t.team_name;
GO
