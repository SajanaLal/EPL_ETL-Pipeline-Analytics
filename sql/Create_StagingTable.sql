USE EPL_Analytics;
GO

-- 1. Teams staging table
IF OBJECT_ID('stg.Teams', 'U') IS NULL
BEGIN
    CREATE TABLE stg.Teams (
        team_id         INT            NOT NULL PRIMARY KEY,
        team_name       NVARCHAR(100)  NOT NULL,
        team_code       NVARCHAR(10)   NULL,
        team_country    NVARCHAR(100)  NULL,
        team_founded    INT            NULL,
        venue_id        INT            NULL,
        venue_name      NVARCHAR(150)  NULL,
        venue_city      NVARCHAR(100)  NULL,
        venue_capacity  INT            NULL,
        venue_surface   NVARCHAR(50)   NULL
    );

    PRINT 'stg.Teams created.';
END;
GO

-- 2. Standings staging table
IF OBJECT_ID('stg.Standings', 'U') IS NULL
BEGIN
    CREATE TABLE stg.Standings (
        position          INT            NOT NULL,
        team_id           INT            NOT NULL PRIMARY KEY,
        team_name         NVARCHAR(100)  NOT NULL,
        points            INT            NOT NULL,
        goal_difference   INT            NOT NULL,
        matches_played    INT            NOT NULL,
        wins              INT            NOT NULL,
        draws             INT            NOT NULL,
        losses            INT            NOT NULL,
        goals_scored      INT            NOT NULL,
        goals_conceded    INT            NOT NULL
    );

    PRINT 'stg.Standings created.';
END;
GO

-- 3. Fixtures staging table
IF OBJECT_ID('stg.Fixtures', 'U') IS NULL
BEGIN
    CREATE TABLE stg.Fixtures (
        fixture_id           INT             NOT NULL PRIMARY KEY,
        fixture_date         DATETIMEOFFSET  NOT NULL,
        fixture_timestamp    BIGINT          NULL,
        venue_name           NVARCHAR(150)   NULL,
        venue_city           NVARCHAR(100)   NULL,
        match_status         NVARCHAR(10)    NOT NULL,
        league_round         NVARCHAR(100)   NULL,
        home_team_id         INT             NOT NULL,
        home_team_name       NVARCHAR(100)   NOT NULL,
        away_team_id         INT             NOT NULL,
        away_team_name       NVARCHAR(100)   NOT NULL,
        home_goals           INT             NULL,
        away_goals           INT             NULL,
        halftime_home_goals  INT             NULL,
        halftime_away_goals  INT             NULL,
        fulltime_home_goals  INT             NULL,
        fulltime_away_goals  INT             NULL
    );

    PRINT 'stg.Fixtures created.';
END;
GO
