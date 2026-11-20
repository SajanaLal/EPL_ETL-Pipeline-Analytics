USE EPL_Analytics;
GO

IF OBJECT_ID('dw.DimTeam', 'U') IS NULL
BEGIN
    CREATE TABLE dw.DimTeam (
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

    PRINT 'dw.DimTeam created.';
END
ELSE
BEGIN
    PRINT 'dw.DimTeam already exists.';
END;
GO


IF OBJECT_ID('dw.FactStandings', 'U') IS NULL
BEGIN
    CREATE TABLE dw.FactStandings (
        team_id           INT           NOT NULL,
        season            INT           NOT NULL,
        position          INT           NOT NULL,
        points            INT           NOT NULL,
        goal_difference   INT           NOT NULL,
        matches_played    INT           NOT NULL,
        wins              INT           NOT NULL,
        draws             INT           NOT NULL,
        losses            INT           NOT NULL,
        goals_scored      INT           NOT NULL,
        goals_conceded    INT           NOT NULL,

        CONSTRAINT PK_FactStandings
            PRIMARY KEY (team_id, season),

        CONSTRAINT FK_FactStandings_DimTeam
            FOREIGN KEY (team_id)
            REFERENCES dw.DimTeam(team_id),

        CONSTRAINT CK_FactStandings_Season
            CHECK (season >= 1888),

        CONSTRAINT CK_FactStandings_Position
            CHECK (position BETWEEN 1 AND 20),

        CONSTRAINT CK_FactStandings_Results
            CHECK (
                matches_played = wins + draws + losses
            ),

        CONSTRAINT CK_FactStandings_Points
            CHECK (points = wins * 3 + draws),

        CONSTRAINT CK_FactStandings_GoalDifference
            CHECK (
                goal_difference = goals_scored - goals_conceded
            )
    );

    PRINT 'dw.FactStandings created.';
END
ELSE
BEGIN
    PRINT 'dw.FactStandings already exists.';
END;

GO

IF OBJECT_ID('dw.FactFixture', 'U') IS NULL
BEGIN
    CREATE TABLE dw.FactFixture (
        fixture_id           INT             NOT NULL PRIMARY KEY,
        season               INT             NOT NULL,
        fixture_date         DATETIMEOFFSET  NOT NULL,
        venue_name           NVARCHAR(150)   NULL,
        venue_city           NVARCHAR(100)   NULL,
        match_status         NVARCHAR(10)    NOT NULL,
        league_round         NVARCHAR(100)   NULL,

        home_team_id         INT             NOT NULL,
        away_team_id         INT             NOT NULL,

        home_goals           INT             NULL,
        away_goals           INT             NULL,
        halftime_home_goals  INT             NULL,
        halftime_away_goals  INT             NULL,
        fulltime_home_goals  INT             NULL,
        fulltime_away_goals  INT             NULL,

        CONSTRAINT FK_FactFixture_HomeTeam
            FOREIGN KEY (home_team_id)
            REFERENCES dw.DimTeam(team_id),

        CONSTRAINT FK_FactFixture_AwayTeam
            FOREIGN KEY (away_team_id)
            REFERENCES dw.DimTeam(team_id),

        CONSTRAINT CK_FactFixture_DifferentTeams
            CHECK (home_team_id <> away_team_id),

        CONSTRAINT CK_FactFixture_NonNegativeGoals
            CHECK (
                (home_goals IS NULL OR home_goals >= 0)
                AND (away_goals IS NULL OR away_goals >= 0)
                AND (halftime_home_goals IS NULL OR halftime_home_goals >= 0)
                AND (halftime_away_goals IS NULL OR halftime_away_goals >= 0)
                AND (fulltime_home_goals IS NULL OR fulltime_home_goals >= 0)
                AND (fulltime_away_goals IS NULL OR fulltime_away_goals >= 0)
            )
    );

    PRINT 'dw.FactFixture created.';
END
ELSE
BEGIN
    PRINT 'dw.FactFixture already exists.';
END;
GO
