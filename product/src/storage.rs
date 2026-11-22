//! Local, single-writer history. Observation payloads are immutable; corrections are
//! append-only. The host owns the connection and never hands database access to UI.

use std::{path::Path, time::{Duration, Instant}};

use rusqlite::{Connection, OpenFlags, OptionalExtension, TransactionBehavior, params};
use serde::Serialize;

use crate::domain::{
    CategoryCorrection, CategoryRule, CorrectionRequest, DayReport, DayRequest, DomainError,
    Observation, build_report, day_bounds, demo_synthetic_fixture,
};

pub const SCHEMA_VERSION: i64 = 1;
pub const RECORD_VERSION: i64 = 1;
pub const MAX_REPORT_OBSERVATIONS: usize = 10_000;
pub const MAX_REPORT_BYTES: usize = 2 * 1024 * 1024;
pub const MAX_OBSERVATION_BYTES: usize = 16 * 1024;
pub const MAX_INSERT_BATCH: usize = 10_000;
const APPLICATION_ID: i64 = 0x46574354; // FWCT; distinguish this database from legacy/foreign data.
const BUSY_TIMEOUT: Duration = Duration::from_millis(250);
const QUERY_TIMEOUT: Duration = Duration::from_secs(2);
const QUERY_VM_STEP_LIMIT: usize = 10_000_000;

type Result<T> = std::result::Result<T, StorageError>;

#[derive(Debug, thiserror::Error)]
pub enum StorageError {
    #[error(transparent)]
    Sqlite(#[from] rusqlite::Error),
    #[error(transparent)]
    Json(#[from] serde_json::Error),
    #[error(transparent)]
    Domain(#[from] DomainError),
    #[error("database schema {found} is unsupported (supported: {supported})")]
    UnsupportedSchema { found: i64, supported: i64 },
    #[error("this is not an initialized FocusWatch product database")]
    UnrecognizedDatabase,
    #[error("SQLite {version} does not contain the required WAL-reset fix")]
    IncompatibleEngine { version: String },
    #[error("a file-backed WAL database is required; actual journal mode: {actual}")]
    JournalModeRequired { actual: String },
    #[error("report exceeds its safety limit ({limit}); narrow the query")]
    ReportTooLarge { limit: usize },
    #[error("report query exhausted its work or time budget")]
    QueryBudgetExceeded,
    #[error("observation ID has a different immutable payload: {id}")]
    ObservationConflict { id: String },
    #[error("correction command ID has a different semantic payload: {command_id}")]
    CommandConflict { command_id: String },
    #[error("correction revision conflict for {observation_id}: expected {expected}, actual {actual}")]
    RevisionConflict { observation_id: String, expected: u64, actual: u64 },
    #[error("observation does not exist: {id}")]
    ObservationNotFound { id: String },
    #[error("invalid storage input: {0}")]
    InvalidInput(&'static str),
    #[error("invalid stored data: {0}")]
    CorruptData(&'static str),
    #[error("revision counter exhausted")]
    RevisionExhausted,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct InsertSummary {
    pub inserted: usize,
    pub duplicates: usize,
    pub report_revision: u64,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct CorrectionResult {
    pub correction: CategoryCorrection,
    pub report_revision: u64,
    pub replayed: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct StorageDiagnostics {
    pub schema_version: i64,
    pub record_version: i64,
    pub application_id: i64,
    pub sqlite_version: String,
    pub sqlite_source_id: String,
    pub journal_mode: String,
    pub synchronous: i64,
    pub foreign_keys: bool,
    pub report_revision: u64,
}

pub struct Storage {
    connection: Connection,
}

impl Storage {
    /// Opens only the explicit path supplied by the host. No default personal
    /// directory, legacy import, repair, deletion or fallback is performed.
    pub fn open(path: impl AsRef<Path>) -> Result<Self> {
        if !has_wal_reset_fix(rusqlite::version_number()) {
            return Err(StorageError::IncompatibleEngine { version: rusqlite::version().into() });
        }
        let flags = OpenFlags::SQLITE_OPEN_READ_WRITE
            | OpenFlags::SQLITE_OPEN_CREATE
            | OpenFlags::SQLITE_OPEN_NO_MUTEX;
        let mut connection = Connection::open_with_flags(path, flags)?;
        connection.busy_timeout(BUSY_TIMEOUT)?;
        let schema: i64 = connection.pragma_query_value(None, "user_version", |r| r.get(0))?;
        let app: i64 = connection.pragma_query_value(None, "application_id", |r| r.get(0))?;
        if schema > SCHEMA_VERSION || schema < 0 {
            return Err(StorageError::UnsupportedSchema { found: schema, supported: SCHEMA_VERSION });
        }
        if schema == 0 {
            let tables: i64 = connection.query_row(
                "SELECT count(*) FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%'",
                [], |row| row.get(0),
            )?;
            if app != 0 || tables != 0 {
                return Err(StorageError::UnrecognizedDatabase);
            }
        } else if app != APPLICATION_ID {
            return Err(StorageError::UnrecognizedDatabase);
        }
        connection.pragma_update(None, "foreign_keys", "ON")?;
        connection.pragma_update(None, "trusted_schema", "OFF")?;
        let journal: String = connection.pragma_update_and_check(None, "journal_mode", "WAL", |r| r.get(0))?;
        if !journal.eq_ignore_ascii_case("wal") {
            return Err(StorageError::JournalModeRequired { actual: journal });
        }
        // FULL is a per-connection setting. Set and verify it on every open;
        // process restart tests do not pretend to test power-loss guarantees.
        connection.pragma_update(None, "synchronous", "FULL")?;
        let synchronous: i64 = connection.pragma_query_value(None, "synchronous", |r| r.get(0))?;
        if synchronous != 2 {
            return Err(StorageError::CorruptData("synchronous=FULL was not applied"));
        }
        if schema == 0 {
            let tx = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
            tx.execute_batch(
                "CREATE TABLE storage_metadata (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    report_revision INTEGER NOT NULL CHECK(report_revision >= 0)
                 ) STRICT;
                 INSERT INTO storage_metadata VALUES (1, 0);
                 CREATE TABLE observations (
                    id TEXT PRIMARY KEY NOT NULL,
                    record_version INTEGER NOT NULL CHECK(record_version = 1),
                    scope_start_ms INTEGER NOT NULL,
                    scope_end_ms INTEGER NOT NULL CHECK(scope_end_ms >= scope_start_ms),
                    payload TEXT NOT NULL CHECK(length(CAST(payload AS BLOB)) <= 16384)
                 ) STRICT;
                 CREATE INDEX observations_scope ON observations(scope_start_ms, scope_end_ms, id);
                 CREATE TABLE category_corrections (
                    id TEXT PRIMARY KEY NOT NULL,
                    observation_id TEXT NOT NULL REFERENCES observations(id),
                    category TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK(revision > 0),
                    created_at_ms INTEGER NOT NULL,
                    UNIQUE(observation_id, revision)
                 ) STRICT;
                 CREATE INDEX correction_latest ON category_corrections(observation_id, revision DESC);",
            )?;
            tx.pragma_update(None, "application_id", APPLICATION_ID)?;
            tx.pragma_update(None, "user_version", SCHEMA_VERSION)?;
            tx.commit()?;
        }
        let storage = Self { connection };
        storage.revision()?; // Fail closed if a purported v1 database lacks its metadata.
        Ok(storage)
    }

    pub fn seed_synthetic_fixture(&mut self) -> Result<InsertSummary> {
        self.insert_observations(&demo_synthetic_fixture())
    }

    /// An entire batch, including its generation counter, commits or rolls back.
    /// Retrying an ID is a no-op only when the complete typed observation agrees.
    pub fn insert_observations(&mut self, observations: &[Observation]) -> Result<InsertSummary> {
        if observations.len() > MAX_INSERT_BATCH {
            return Err(StorageError::InvalidInput("observation batch exceeds limit"));
        }
        let mut payloads = Vec::with_capacity(observations.len());
        for observation in observations {
            observation.validate()?;
            let payload = serde_json::to_string(observation)?;
            if payload.len() > MAX_OBSERVATION_BYTES {
                return Err(StorageError::InvalidInput("observation payload exceeds limit"));
            }
            payloads.push(payload);
        }
        let tx = self.connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let mut inserted = 0;
        let mut duplicates = 0;
        for (observation, payload) in observations.iter().zip(payloads) {
            let existing: Option<(i64, String)> = tx.query_row(
                "SELECT record_version, payload FROM observations WHERE id = ?1",
                [&observation.id], |r| Ok((r.get(0)?, r.get(1)?)),
            ).optional()?;
            if let Some((version, previous)) = existing {
                let previous = decode_observation(version, &previous)?;
                if previous != *observation {
                    return Err(StorageError::ObservationConflict { id: observation.id.clone() });
                }
                duplicates += 1;
            } else {
                let (start, end) = observation.bounds();
                tx.execute(
                    "INSERT INTO observations (id,record_version,scope_start_ms,scope_end_ms,payload)
                     VALUES (?1,?2,?3,?4,?5)",
                    params![observation.id, RECORD_VERSION, start, end, payload],
                )?;
                inserted += 1;
            }
        }
        let report_revision = if inserted != 0 { bump_revision(&tx)? } else { read_revision(&tx)? };
        tx.commit()?;
        Ok(InsertSummary { inserted, duplicates, report_revision })
    }

    pub fn apply_correction(&mut self, request: &CorrectionRequest, created_at_ms: i64) -> Result<CorrectionResult> {
        request.validate()?;
        let tx = self.connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let previous = tx.query_row(
            "SELECT id,observation_id,category,revision,created_at_ms FROM category_corrections WHERE id = ?1",
            [&request.command_id], correction_from_row,
        ).optional()?;
        if let Some(previous) = previous {
            // created_at_ms is server-stamped and deliberately excluded from
            // command identity. A retry preserves the first committed timestamp.
            if previous.observation_id != request.observation_id
                || previous.category != request.category
                || previous.revision.checked_sub(1) != Some(request.expected_revision)
            {
                return Err(StorageError::CommandConflict { command_id: request.command_id.clone() });
            }
            let report_revision = read_revision(&tx)?;
            tx.commit()?;
            return Ok(CorrectionResult { correction: previous, report_revision, replayed: true });
        }
        let exists: bool = tx.query_row(
            "SELECT EXISTS(SELECT 1 FROM observations WHERE id = ?1)",
            [&request.observation_id], |r| r.get(0),
        )?;
        if !exists {
            return Err(StorageError::ObservationNotFound { id: request.observation_id.clone() });
        }
        let actual: i64 = tx.query_row(
            "SELECT COALESCE(MAX(revision),0) FROM category_corrections WHERE observation_id = ?1",
            [&request.observation_id], |r| r.get(0),
        )?;
        let actual = u64::try_from(actual).map_err(|_| StorageError::CorruptData("negative correction revision"))?;
        if actual != request.expected_revision {
            return Err(StorageError::RevisionConflict {
                observation_id: request.observation_id.clone(), expected: request.expected_revision, actual,
            });
        }
        let revision = next_revision(actual)?;
        let correction = CategoryCorrection {
            id: request.command_id.clone(), observation_id: request.observation_id.clone(),
            category: request.category.clone(), revision, created_at_ms,
        };
        correction.validate()?;
        tx.execute(
            "INSERT INTO category_corrections (id,observation_id,category,revision,created_at_ms)
             VALUES (?1,?2,?3,?4,?5)",
            params![correction.id,correction.observation_id,correction.category,sqlite_revision(correction.revision)?,correction.created_at_ms],
        )?;
        let report_revision = bump_revision(&tx)?;
        tx.commit()?;
        Ok(CorrectionResult { correction, report_revision, replayed: false })
    }

    pub fn day_report(&mut self, request: &DayRequest, rules: &[CategoryRule]) -> Result<DayReport> {
        self.report_with_budget(request, rules, QUERY_VM_STEP_LIMIT, QUERY_TIMEOUT)
    }

    fn report_with_budget(&mut self, request: &DayRequest, rules: &[CategoryRule], step_limit: usize, timeout: Duration) -> Result<DayReport> {
        let deadline = Instant::now() + timeout;
        let mut steps = 0usize;
        self.connection.progress_handler(1_000, Some(move || {
            steps += 1_000;
            steps >= step_limit || Instant::now() >= deadline
        }))?;
        let result = self.report_with_limits(request, rules, MAX_REPORT_OBSERVATIONS, MAX_REPORT_BYTES);
        self.connection.progress_handler(0, None::<fn() -> bool>)?;
        match result {
            Err(StorageError::Sqlite(rusqlite::Error::SqliteFailure(error, _)))
                if error.code == rusqlite::ErrorCode::OperationInterrupted => Err(StorageError::QueryBudgetExceeded),
            Ok(_) if Instant::now() >= deadline => Err(StorageError::QueryBudgetExceeded),
            other => other,
        }
    }

    fn report_with_limits(&mut self, request: &DayRequest, rules: &[CategoryRule], limit: usize, byte_limit: usize) -> Result<DayReport> {
        let bounds = day_bounds(&request.date, &request.time_zone)?;
        // The initial metadata read fixes this transaction's snapshot before any
        // observation/correction reads. No UI gets a mixed-generation report.
        let tx = self.connection.transaction()?;
        let revision = read_revision(&tx)?;
        let mut observations = Vec::new();
        {
            let mut stmt = tx.prepare(
                "SELECT id,record_version,scope_start_ms,scope_end_ms,payload FROM observations
                 WHERE scope_start_ms < ?1 AND (scope_end_ms > ?2 OR (scope_end_ms = scope_start_ms AND scope_start_ms >= ?2))
                 ORDER BY scope_start_ms,id LIMIT ?3",
            )?;
            let mut rows = stmt.query(params![bounds.end_ms,bounds.start_ms,(limit + 1) as i64])?;
            let mut payload_bytes = 0usize;
            while let Some(row) = rows.next()? {
                if observations.len() == limit {
                    return Err(StorageError::ReportTooLarge { limit });
                }
                let payload: String = row.get(4)?;
                payload_bytes = payload_bytes.checked_add(payload.len()).ok_or(StorageError::ReportTooLarge { limit: byte_limit })?;
                if payload_bytes > byte_limit {
                    return Err(StorageError::ReportTooLarge { limit: byte_limit });
                }
                let observation = decode_observation(row.get(1)?, &payload)?;
                let id: String = row.get(0)?;
                let bounds: (i64, i64) = (row.get(2)?, row.get(3)?);
                if observation.id != id || observation.bounds() != bounds {
                    return Err(StorageError::CorruptData("observation index disagrees with immutable payload"));
                }
                observations.push(observation);
            }
        }
        let corrections = {
            let mut stmt = tx.prepare(
                "SELECT c.id,c.observation_id,c.category,c.revision,c.created_at_ms
                 FROM category_corrections c JOIN observations o ON o.id = c.observation_id
                 WHERE o.scope_start_ms < ?1 AND (o.scope_end_ms > ?2 OR (o.scope_end_ms = o.scope_start_ms AND o.scope_start_ms >= ?2))
                   AND c.revision = (SELECT MAX(latest.revision) FROM category_corrections latest WHERE latest.observation_id = c.observation_id)
                 ORDER BY c.observation_id LIMIT ?3",
            )?;
            stmt.query_map(params![bounds.end_ms,bounds.start_ms,(limit + 1) as i64], correction_from_row)?
                .collect::<std::result::Result<Vec<_>, _>>()?
        };
        if corrections.len() > limit {
            return Err(StorageError::ReportTooLarge { limit });
        }
        let report = build_report(request, &observations, &corrections, rules, revision)?;
        if serde_json::to_vec(&report)?.len() > byte_limit {
            return Err(StorageError::ReportTooLarge { limit: byte_limit });
        }
        tx.commit()?;
        Ok(report)
    }

    pub fn revision(&self) -> Result<u64> {
        read_revision(&self.connection)
    }

    pub fn diagnostics(&self) -> Result<StorageDiagnostics> {
        let pragma = |name| self.connection.pragma_query_value(None, name, |r| r.get::<_, i64>(0));
        Ok(StorageDiagnostics {
            schema_version: pragma("user_version")?, record_version: RECORD_VERSION,
            application_id: pragma("application_id")?, sqlite_version: rusqlite::version().into(),
            sqlite_source_id: self.connection.query_row("SELECT sqlite_source_id()", [], |r| r.get(0))?,
            journal_mode: self.connection.pragma_query_value(None, "journal_mode", |r| r.get(0))?,
            synchronous: pragma("synchronous")?, foreign_keys: pragma("foreign_keys")? == 1,
            report_revision: self.revision()?,
        })
    }
}

fn decode_observation(version: i64, payload: &str) -> Result<Observation> {
    if version != RECORD_VERSION {
        return Err(StorageError::CorruptData("unsupported observation record version"));
    }
    if payload.len() > MAX_OBSERVATION_BYTES {
        return Err(StorageError::CorruptData("observation payload exceeds limit"));
    }
    let observation: Observation = serde_json::from_str(payload)?;
    observation.validate()?;
    Ok(observation)
}

fn correction_from_row(row: &rusqlite::Row<'_>) -> rusqlite::Result<CategoryCorrection> {
    let revision: i64 = row.get(3)?;
    let revision = u64::try_from(revision).map_err(|error| {
        rusqlite::Error::FromSqlConversionFailure(3, rusqlite::types::Type::Integer, Box::new(error))
    })?;
    Ok(CategoryCorrection {
        id: row.get(0)?, observation_id: row.get(1)?, category: row.get(2)?,
        revision, created_at_ms: row.get(4)?,
    })
}

fn read_revision(connection: &Connection) -> Result<u64> {
    let revision: i64 = connection.query_row("SELECT report_revision FROM storage_metadata WHERE singleton = 1", [], |r| r.get(0))?;
    u64::try_from(revision).map_err(|_| StorageError::CorruptData("negative report revision"))
}

fn sqlite_revision(revision: u64) -> Result<i64> {
    i64::try_from(revision).map_err(|_| StorageError::RevisionExhausted)
}

fn next_revision(current: u64) -> Result<u64> {
    current.checked_add(1).filter(|next| *next <= i64::MAX as u64).ok_or(StorageError::RevisionExhausted)
}

fn bump_revision(connection: &Connection) -> Result<u64> {
    let next = next_revision(read_revision(connection)?)?;
    if connection.execute("UPDATE storage_metadata SET report_revision = ?1 WHERE singleton = 1", [sqlite_revision(next)?])? != 1 {
        return Err(StorageError::CorruptData("missing generation counter"));
    }
    Ok(next)
}

fn has_wal_reset_fix(version: i32) -> bool {
    version >= 3_051_003
        || (3_050_007..3_051_000).contains(&version)
        || (3_044_006..3_045_000).contains(&version)
}

#[cfg(test)]
mod tests;
