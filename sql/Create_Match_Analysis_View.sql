CREATE OR ALTER VIEW dw.vw_MatchAnalysis
AS
SELECT
    f.fixture_id,
    f.season,
    f.fixture_date,
    f.league_round,
    f.venue_name,
    f.venue_city,

    f.home_team_id,
    ht.team_name AS home_team,

    f.away_team_id,
    at.team_name AS away_team,

    f.home_goals,
    f.away_goals,

    f.home_goals + f.away_goals AS total_goals,

    CASE
        WHEN f.home_goals > f.away_goals THEN 'Home Win'
        WHEN f.home_goals < f.away_goals THEN 'Away Win'
        ELSE 'Draw'
    END AS match_result

FROM dw.FactFixture AS f
INNER JOIN dw.DimTeam AS ht
    ON f.home_team_id = ht.team_id
INNER JOIN dw.DimTeam AS at
    ON f.away_team_id = at.team_id;
GO
