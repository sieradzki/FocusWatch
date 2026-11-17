PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
PRAGMA wal_autocheckpoint=1000;
CREATE TABLE observations (
 id INTEGER PRIMARY KEY,
 start_s INTEGER NOT NULL,
 end_s INTEGER NOT NULL,
 app TEXT NOT NULL,
 category TEXT NOT NULL
);
CREATE INDEX observations_start_id ON observations(start_s,id);
