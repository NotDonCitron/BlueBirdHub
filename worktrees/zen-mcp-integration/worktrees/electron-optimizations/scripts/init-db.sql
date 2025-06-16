-- OrdnungsHub Production Database Initialization
-- This script is run when the PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For indexing

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for better performance
-- (These will be created by SQLAlchemy models, but we can add custom ones here)

-- Create a database function for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant permissions to the ordnungshub user
GRANT ALL PRIVILEGES ON DATABASE ordnungshub_prod TO ordnungshub;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ordnungshub;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ordnungshub;

-- Enable logging for monitoring
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries > 1 second
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';

SELECT pg_reload_conf();