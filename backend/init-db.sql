-- ArenaMind: PostgreSQL init script
-- Runs automatically on first docker-compose up

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'fan',
    preferred_language VARCHAR(10) DEFAULT 'en',
    accessibility_needs JSONB DEFAULT '[]',
    ticket_id VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    role VARCHAR(20) NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    metadata JSONB DEFAULT '{}',
    agent_used VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS ix_chat_messages_created ON chat_messages(created_at);

-- Seed a demo user for each role
INSERT INTO users (email, hashed_password, full_name, role) VALUES
    ('fan@arenamind.ai', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.TZjFWI0gQqyK4i', 'Demo Fan', 'fan'),
    ('volunteer@arenamind.ai', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.TZjFWI0gQqyK4i', 'Demo Volunteer', 'volunteer'),
    ('operator@arenamind.ai', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.TZjFWI0gQqyK4i', 'Demo Operator', 'operator'),
    ('emergency@arenamind.ai', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.TZjFWI0gQqyK4i', 'Demo Emergency', 'emergency')
ON CONFLICT (email) DO NOTHING;