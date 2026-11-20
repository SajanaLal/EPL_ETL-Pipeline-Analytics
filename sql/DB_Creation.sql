USE master;
GO

-- Create the database only if it does not exist
IF NOT EXISTS (
    SELECT 1
    FROM sys.databases
    WHERE name = 'EPL_Analytics'
)
BEGIN
    CREATE DATABASE EPL_Analytics;
    PRINT 'EPL_Analytics database created successfully.';
END
ELSE
BEGIN
    PRINT 'EPL_Analytics database already exists. Reusing it.';
END;
GO

USE EPL_Analytics;
GO

-- Create staging schema if it does not exist
IF SCHEMA_ID('stg') IS NULL
BEGIN
    EXEC('CREATE SCHEMA stg');
    PRINT 'stg schema created successfully.';
END
ELSE
BEGIN
    PRINT 'stg schema already exists.';
END;
GO

-- Create data warehouse schema if it does not exist
IF SCHEMA_ID('dw') IS NULL
BEGIN
    EXEC('CREATE SCHEMA dw');
    PRINT 'dw schema created successfully.';
END
ELSE
BEGIN
    PRINT 'dw schema already exists.';
END;
GO
