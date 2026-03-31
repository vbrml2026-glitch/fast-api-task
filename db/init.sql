BEGIN;

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  password_hash VARCHAR(255) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at);

-- Posts table
CREATE TABLE IF NOT EXISTS posts (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- Client-supplied key used for the "upsert" endpoint.
  post_key VARCHAR(100) NOT NULL,
  title VARCHAR(200) NOT NULL,
  content TEXT NOT NULL,
  image BYTEA,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_posts_user_post_key UNIQUE (user_id, post_key)
);

CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts (user_id);
CREATE INDEX IF NOT EXISTS idx_posts_title ON posts (title);

-- Post votes (like/dislike)
CREATE TABLE IF NOT EXISTS post_votes (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,

  vote_type INT NOT NULL CHECK (vote_type IN (-1, 1)),
  voted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_post_votes_user_post UNIQUE (user_id, post_id)
);

CREATE INDEX IF NOT EXISTS idx_post_votes_post_id ON post_votes (post_id);
CREATE INDEX IF NOT EXISTS idx_post_votes_vote_type ON post_votes (vote_type);

-- Seed data
-- Password for all seeded users is: password123
-- Hash produced by this project's pbkdf2_sha256 implementation.
INSERT INTO users (id, username, email, first_name, last_name, password_hash, is_active, created_at, updated_at)
VALUES
  (1, 'alice', 'alice@example.com', 'Alice', 'A', '$pbkdf2-sha256$29000$T0mJMaYUIuQcQ8hZq5WSMg$JJ74U.DDkCifQylzXOanRNmGiV83CzIab8MYwsqzNN8', TRUE, NOW(), NOW()),
  (2, 'bob', 'bob@example.com', 'Bob', 'B', '$pbkdf2-sha256$29000$T0mJMaYUIuQcQ8hZq5WSMg$JJ74U.DDkCifQylzXOanRNmGiV83CzIab8MYwsqzNN8', TRUE, NOW(), NOW()),
  (3, 'charlie', 'charlie@example.com', 'Charlie', 'C', '$pbkdf2-sha256$29000$T0mJMaYUIuQcQ8hZq5WSMg$JJ74U.DDkCifQylzXOanRNmGiV83CzIab8MYwsqzNN8', TRUE, NOW(), NOW()),
  (4, 'dana', 'dana@example.com', 'Dana', 'D', '$pbkdf2-sha256$29000$T0mJMaYUIuQcQ8hZq5WSMg$JJ74U.DDkCifQylzXOanRNmGiV83CzIab8MYwsqzNN8', TRUE, NOW(), NOW()),
  (5, 'eve', 'eve@example.com', 'Eve', 'E', '$pbkdf2-sha256$29000$T0mJMaYUIuQcQ8hZq5WSMg$JJ74U.DDkCifQylzXOanRNmGiV83CzIab8MYwsqzNN8', TRUE, NOW(), NOW()),
  (6, 'frank', 'frank@example.com', 'Frank', 'F', '$pbkdf2-sha256$29000$T0mJMaYUIuQcQ8hZq5WSMg$JJ74U.DDkCifQylzXOanRNmGiV83CzIab8MYwsqzNN8', TRUE, NOW(), NOW()),
  (7, 'grace', 'grace@example.com', 'Grace', 'G', '$pbkdf2-sha256$29000$T0mJMaYUIuQcQ8hZq5WSMg$JJ74U.DDkCifQylzXOanRNmGiV83CzIab8MYwsqzNN8', TRUE, NOW(), NOW()),
  (8, 'heidi', 'heidi@example.com', 'Heidi', 'H', '$pbkdf2-sha256$29000$T0mJMaYUIuQcQ8hZq5WSMg$JJ74U.DDkCifQylzXOanRNmGiV83CzIab8MYwsqzNN8', TRUE, NOW(), NOW()),
  (9, 'ivan', 'ivan@example.com', 'Ivan', 'I', '$pbkdf2-sha256$29000$T0mJMaYUIuQcQ8hZq5WSMg$JJ74U.DDkCifQylzXOanRNmGiV83CzIab8MYwsqzNN8', TRUE, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO posts (id, user_id, post_key, title, content, image, created_at, updated_at)
VALUES
  (1, 1, 'post_1', 'Post title #1', 'Post content #1', NULL, NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day'),
  (2, 1, 'post_2', 'Post title #2', 'Post content #2', NULL, NOW() - INTERVAL '1 day', NOW() - INTERVAL '12 hours')
ON CONFLICT (id) DO NOTHING;

-- Likes on post_1 (6 users: bob..grace)
INSERT INTO post_votes (user_id, post_id, vote_type, voted_at)
VALUES
  (2, 1, 1, NOW() - INTERVAL '60 minutes'),
  (3, 1, 1, NOW() - INTERVAL '55 minutes'),
  (4, 1, 1, NOW() - INTERVAL '50 minutes'),
  (5, 1, 1, NOW() - INTERVAL '45 minutes'),
  (6, 1, 1, NOW() - INTERVAL '40 minutes'),
  (7, 1, 1, NOW() - INTERVAL '5 minutes')
ON CONFLICT (user_id, post_id) DO UPDATE
SET vote_type = EXCLUDED.vote_type, voted_at = EXCLUDED.voted_at;

-- Dislikes on post_1 (2 users: heidi..ivan)
INSERT INTO post_votes (user_id, post_id, vote_type, voted_at)
VALUES
  (8, 1, -1, NOW() - INTERVAL '30 minutes'),
  (9, 1, -1, NOW() - INTERVAL '2 minutes')
ON CONFLICT (user_id, post_id) DO UPDATE
SET vote_type = EXCLUDED.vote_type, voted_at = EXCLUDED.voted_at;

-- Likes on post_2 (4 users)
INSERT INTO post_votes (user_id, post_id, vote_type, voted_at)
VALUES
  (2, 2, 1, NOW() - INTERVAL '70 minutes'),
  (3, 2, 1, NOW() - INTERVAL '60 minutes'),
  (4, 2, 1, NOW() - INTERVAL '50 minutes'),
  (5, 2, 1, NOW() - INTERVAL '10 minutes')
ON CONFLICT (user_id, post_id) DO UPDATE
SET vote_type = EXCLUDED.vote_type, voted_at = EXCLUDED.voted_at;

-- Dislikes on post_2 (1 user)
INSERT INTO post_votes (user_id, post_id, vote_type, voted_at)
VALUES
  (8, 2, -1, NOW() - INTERVAL '20 minutes')
ON CONFLICT (user_id, post_id) DO UPDATE
SET vote_type = EXCLUDED.vote_type, voted_at = EXCLUDED.voted_at;

COMMIT;

