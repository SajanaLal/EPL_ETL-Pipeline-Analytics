SET NOCOUNT ON;
SET XACT_ABORT ON;

-- Change this value when loading a different season.
DECLARE @Season INT = ?;

BEGIN TRY
    BEGIN TRANSACTION;

    ------------------------------------------------------------
    -- 1. Validate staging data
    ------------------------------------------------------------

    IF NOT EXISTS (SELECT 1 FROM stg.Teams)
        THROW 50001, 'Staging teams table is empty.', 1;

    IF NOT EXISTS (SELECT 1 FROM stg.Fixtures)
        THROW 50002, 'Staging fixtures table is empty.', 1;

    IF NOT EXISTS (SELECT 1 FROM stg.Standings)
        THROW 50003, 'Staging standings table is empty.', 1;

    -- Validate unique keys.
    IF EXISTS (
        SELECT team_id
        FROM stg.Teams
        GROUP BY team_id
        HAVING team_id IS NULL OR COUNT(*) > 1
    )
        THROW 50004, 'Duplicate staging team IDs.', 1;

    IF EXISTS (
        SELECT fixture_id
        FROM stg.Fixtures
        GROUP BY fixture_id
        HAVING fixture_id IS NULL OR COUNT(*) > 1
    )
        THROW 50005, 'Duplicate staging fixture IDs.', 1;

    IF EXISTS (
        SELECT team_id
        FROM stg.Standings
        GROUP BY team_id
        HAVING team_id IS NULL OR COUNT(*) > 1
    )
        THROW 50006, 'Duplicate staging standings team IDs.', 1;

    IF EXISTS (
        SELECT position
        FROM stg.Standings
        GROUP BY position
        HAVING position IS NULL OR COUNT(*) > 1
    )
        THROW 50007, 'Duplicate staging standings positions.', 1;

    -- This project expects one standings row per staged team.
    IF (SELECT COUNT(*) FROM stg.Standings)
       <> (SELECT COUNT(*) FROM stg.Teams)
        THROW 50008, 'Standings and team counts do not match.', 1;

    -- Standings positions must be consecutive from 1 to N.
    IF (SELECT MIN(position) FROM stg.Standings) <> 1
       OR
       (SELECT MAX(position) FROM stg.Standings)
       <> (SELECT COUNT(*) FROM stg.Standings)
        THROW 50009, 'Standings positions must run from 1 to N.', 1;

    -- Validate team references.
    IF EXISTS (
        SELECT 1
        FROM stg.Fixtures f
        LEFT JOIN stg.Teams h ON h.team_id = f.home_team_id
        LEFT JOIN stg.Teams a ON a.team_id = f.away_team_id
        WHERE h.team_id IS NULL OR a.team_id IS NULL
    )
        THROW 50010, 'A fixture references an unknown team.', 1;

    IF EXISTS (
        SELECT 1
        FROM stg.Standings s
        LEFT JOIN stg.Teams t ON t.team_id = s.team_id
        WHERE t.team_id IS NULL
    )
        THROW 50011, 'Standings references an unknown team.', 1;

    -- Validate standings calculations.
    IF EXISTS (
        SELECT 1
        FROM stg.Standings
        WHERE points <> wins * 3 + draws
           OR goal_difference <> goals_scored - goals_conceded
           OR matches_played <> wins + draws + losses
    )
        THROW 50012, 'Standings calculations are invalid.', 1;

    ------------------------------------------------------------
    -- 2. Upsert the team dimension
    ------------------------------------------------------------

    UPDATE d
    SET
        d.team_name = s.team_name,
        d.team_code = s.team_code,
        d.team_country = s.team_country,
        d.team_founded = s.team_founded,
        d.venue_id = s.venue_id,
        d.venue_name = s.venue_name,
        d.venue_city = s.venue_city,
        d.venue_capacity = s.venue_capacity,
        d.venue_surface = s.venue_surface
    FROM dw.DimTeam d
    INNER JOIN stg.Teams s
        ON s.team_id = d.team_id;

    INSERT INTO dw.DimTeam (
        team_id, team_name, team_code, team_country,
        team_founded, venue_id, venue_name, venue_city,
        venue_capacity, venue_surface
    )
    SELECT
        s.team_id, s.team_name, s.team_code, s.team_country,
        s.team_founded, s.venue_id, s.venue_name, s.venue_city,
        s.venue_capacity, s.venue_surface
    FROM stg.Teams s
    WHERE NOT EXISTS (
        SELECT 1
        FROM dw.DimTeam d
        WHERE d.team_id = s.team_id
    );
    
------------------------------------------------------------
-- 3. Refresh standings for the selected season
------------------------------------------------------------

-- Safety check: prevent removing existing teams
-- if they are missing from staging.
IF EXISTS (
    SELECT 1
    FROM dw.FactStandings AS d
    WHERE d.season = @Season
      AND NOT EXISTS (
          SELECT 1
          FROM stg.Standings AS s
          WHERE s.team_id = d.team_id
      )
)
BEGIN
    THROW 50013,
          'Staging is missing existing season standings. Refresh cancelled.',
          1;
END;

-- Delete only the selected season.
DELETE FROM dw.FactStandings
WHERE season = @Season;

-- Insert the latest standings for that season.
INSERT INTO dw.FactStandings (
    team_id,
    season,
    position,
    points,
    goal_difference,
    matches_played,
    wins,
    draws,
    losses,
    goals_scored,
    goals_conceded
)
SELECT
    s.team_id,
    @Season,
    s.position,
    s.points,
    s.goal_difference,
    s.matches_played,
    s.wins,
    s.draws,
    s.losses,
    s.goals_scored,
    s.goals_conceded
FROM stg.Standings AS s;

    ------------------------------------------------------------
    -- 4. Upsert match fixtures
    ------------------------------------------------------------

    UPDATE d
    SET
        d.season = @Season,
        d.fixture_date = s.fixture_date,
        d.venue_name = s.venue_name,
        d.venue_city = s.venue_city,
        d.match_status = s.match_status,
        d.league_round = s.league_round,
        d.home_team_id = s.home_team_id,
        d.away_team_id = s.away_team_id,
        d.home_goals = s.home_goals,
        d.away_goals = s.away_goals,
        d.halftime_home_goals = s.halftime_home_goals,
        d.halftime_away_goals = s.halftime_away_goals,
        d.fulltime_home_goals = s.fulltime_home_goals,
        d.fulltime_away_goals = s.fulltime_away_goals
    FROM dw.FactFixture d
    INNER JOIN stg.Fixtures s
        ON s.fixture_id = d.fixture_id;

    INSERT INTO dw.FactFixture (
        fixture_id, season, fixture_date,
        venue_name, venue_city, match_status, league_round,
        home_team_id, away_team_id,
        home_goals, away_goals,
        halftime_home_goals, halftime_away_goals,
        fulltime_home_goals, fulltime_away_goals
    )
    SELECT
        s.fixture_id, @Season, s.fixture_date,
        s.venue_name, s.venue_city, s.match_status, s.league_round,
        s.home_team_id, s.away_team_id,
        s.home_goals, s.away_goals,
        s.halftime_home_goals, s.halftime_away_goals,
        s.fulltime_home_goals, s.fulltime_away_goals
    FROM stg.Fixtures s
    WHERE NOT EXISTS (
        SELECT 1
        FROM dw.FactFixture d
        WHERE d.fixture_id = s.fixture_id
    );

    ------------------------------------------------------------
    -- 5. Verify loaded records, without fixed row counts
    ------------------------------------------------------------

    IF EXISTS (
        SELECT 1
        FROM stg.Teams s
        LEFT JOIN dw.DimTeam d
            ON d.team_id = s.team_id
        WHERE d.team_id IS NULL
    )
        THROW 50014, 'A staged team is missing from the warehouse.', 1;

    IF EXISTS (
        SELECT 1
        FROM stg.Fixtures s
        LEFT JOIN dw.FactFixture d
            ON d.fixture_id = s.fixture_id
           AND d.season = @Season
        WHERE d.fixture_id IS NULL
    )
        THROW 50015, 'A staged fixture is missing from the warehouse.', 1;

    IF EXISTS (
        SELECT 1
        FROM stg.Standings s
        LEFT JOIN dw.FactStandings d
            ON d.team_id = s.team_id
           AND d.season = @Season
        WHERE d.team_id IS NULL
    )
        THROW 50016, 'A staged standings row is missing from the warehouse.', 1;

    COMMIT TRANSACTION;

    PRINT 'Warehouse upsert completed successfully.';

    SELECT
        @Season AS season,
        (SELECT COUNT(*) FROM stg.Teams) AS staged_teams,
        (SELECT COUNT(*) FROM stg.Fixtures) AS staged_fixtures,
        (SELECT COUNT(*) FROM stg.Standings) AS staged_standings,
        (SELECT COUNT(*) FROM dw.DimTeam) AS warehouse_teams,
        (SELECT COUNT(*) FROM dw.FactFixture
         WHERE season = @Season) AS warehouse_fixtures_for_season,
        (SELECT COUNT(*) FROM dw.FactStandings
         WHERE season = @Season) AS warehouse_standings_for_season;

END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
GO
