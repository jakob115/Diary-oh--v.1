-- These SQL commands are for SQLite database engine
-- For MySQL, PostgreSQL etc. they might be different 

CREATE TABLE IF NOT EXISTS 'user' (
  'id' INTEGER NOT NULL PRIMARY KEY,
  'firstname' VARCHAR NOT NULL,
  'lastname' VARCHAR NOT NULL,
  'username' VARCHAR NOT NULL,
  'password' VARCHAR NOT NULL,
  'admin' BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS 'blogpost' (
  'id' INTEGER NOT NULL PRIMARY KEY,
  'created' DATETIME NOT NULL,
  'updated' DATETIME NOT NULL,
  'title' VARCHAR NOT NULL,
  'summary' VARCHAR NOT NULL,
  'content' VARCHAR NOT NULL,
  'author_id' INTEGER FOREIGN KEY REFERENCES user(id)
);
