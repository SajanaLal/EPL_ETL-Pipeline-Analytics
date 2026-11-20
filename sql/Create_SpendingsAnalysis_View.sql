CREATE OR ALTER VIEW dw.vw_StandingsAnalysis
AS
SELECT
    s.season,
    s.position,
    t.team_id,
    t.team_name,

    s.matches_played,
    s.wins,
    s.draws,
    s.losses,
    s.points,

    s.goals_scored,
    s.goals_conceded,
    s.goal_difference,

    CAST(
        100.0 * s.wins / NULLIF(s.matches_played, 0)
        AS DECIMAL(5,2)
    ) AS win_percentage,

    CAST(
        1.0 * s.points / NULLIF(s.matches_played, 0)
        AS DECIMAL(5,2)
    ) AS points_per_match,

    CAST(
        1.0 * s.goals_scored / NULLIF(s.matches_played, 0)
        AS DECIMAL(5,2)
    ) AS goals_scored_per_match,

    CAST(
        1.0 * s.goals_conceded / NULLIF(s.matches_played, 0)
        AS DECIMAL(5,2)
    ) AS goals_conceded_per_match,

    CAST(
        100.0 * s.points /
        NULLIF(3.0 * s.matches_played, 0)
        AS DECIMAL(5,2)
    ) AS points_efficiency_percentage

FROM dw.FactStandings AS s
INNER JOIN dw.DimTeam AS t
    ON s.team_id = t.team_id;
GO
