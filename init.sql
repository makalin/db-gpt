-- DB-GPT Database Initialization Script
-- This script creates the initial database schema and sample data

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(50) UNIQUE NOT NULL,
    task_name VARCHAR(200) NOT NULL,
    task_description TEXT,
    priority VARCHAR(20) DEFAULT 'MEDIUM',
    agent_role VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result JSONB,
    error_message TEXT
);

-- Create task_results table
CREATE TABLE IF NOT EXISTS task_results (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(50) REFERENCES tasks(task_id),
    result_type VARCHAR(50),
    result_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create queries table for storing generated SQL
CREATE TABLE IF NOT EXISTS queries (
    id SERIAL PRIMARY KEY,
    natural_language_query TEXT NOT NULL,
    generated_sql TEXT NOT NULL,
    query_type VARCHAR(20),
    tables TEXT[],
    columns TEXT[],
    confidence FLOAT,
    execution_time FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create analytics table for storing analysis results
CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    analysis_name VARCHAR(100) NOT NULL,
    analysis_type VARCHAR(50),
    input_data JSONB,
    output_data JSONB,
    insights TEXT[],
    recommendations TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_agent_role ON tasks(agent_role);
CREATE INDEX IF NOT EXISTS idx_queries_created_at ON queries(created_at);
CREATE INDEX IF NOT EXISTS idx_analytics_created_at ON analytics(created_at);

-- Insert sample data
INSERT INTO users (username, email, full_name) VALUES
    ('admin', 'admin@db-gpt.com', 'System Administrator'),
    ('analyst', 'analyst@db-gpt.com', 'Data Analyst'),
    ('engineer', 'engineer@db-gpt.com', 'Database Engineer')
ON CONFLICT (username) DO NOTHING;

-- Insert sample tasks
INSERT INTO tasks (task_id, task_name, task_description, priority, agent_role, status) VALUES
    ('task_1', 'Initial Database Analysis', 'Analyze the current database schema and provide insights', 'HIGH', 'analyst', 'completed'),
    ('task_2', 'Performance Optimization', 'Identify and optimize slow queries', 'MEDIUM', 'engineer', 'pending'),
    ('task_3', 'Data Quality Assessment', 'Check data quality and identify issues', 'HIGH', 'analyst', 'pending')
ON CONFLICT (task_id) DO NOTHING;

-- Insert sample queries
INSERT INTO queries (natural_language_query, generated_sql, query_type, tables, columns, confidence) VALUES
    ('Show me all active users', 'SELECT * FROM users WHERE is_active = true', 'SELECT', ARRAY['users'], ARRAY['*'], 0.95),
    ('Count total users', 'SELECT COUNT(*) as user_count FROM users', 'SELECT', ARRAY['users'], ARRAY['COUNT'], 0.90),
    ('Find users created this month', 'SELECT * FROM users WHERE created_at >= DATE_TRUNC(''month'', CURRENT_DATE)', 'SELECT', ARRAY['users'], ARRAY['*'], 0.85)
ON CONFLICT DO NOTHING;

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your setup)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO db_gpt_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO db_gpt_user; 