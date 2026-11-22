use super::*;
use crate::domain::{DEMO_DATE, DEMO_TIME_ZONE, Measurement, default_category_rules};
use tempfile::TempDir;

fn database() -> (TempDir, Storage) {
    let directory = tempfile::tempdir().unwrap();
    let storage = Storage::open(directory.path().join("synthetic.sqlite")).unwrap();
    (directory, storage)
}

fn day() -> DayRequest {
    DayRequest { date: DEMO_DATE.into(), time_zone: DEMO_TIME_ZONE.into() }
}

fn command(id: &str, observation: &str, category: &str, revision: u64) -> CorrectionRequest {
    CorrectionRequest {
        command_id: id.into(), observation_id: observation.into(), category: category.into(),
        expected_revision: revision,
    }
}

fn raw(storage: &Storage, id: &str) -> Observation {
    let (version, payload) = storage.connection.query_row(
        "SELECT record_version,payload FROM observations WHERE id = ?1", [id],
        |row| Ok((row.get::<_, i64>(0)?, row.get::<_, String>(1)?)),
    ).unwrap();
    decode_observation(version, &payload).unwrap()
}

fn count(storage: &Storage, table: &str) -> i64 {
    let sql = match table {
        "observations" => "SELECT count(*) FROM observations",
        "corrections" => "SELECT count(*) FROM category_corrections",
        _ => panic!("test table allowlist"),
    };
    storage.connection.query_row(sql, [], |row| row.get(0)).unwrap()
}

#[test]
fn file_database_has_versioned_wal_full_and_fixed_runtime_on_every_open() {
    let (directory, storage) = database();
    let diagnostics = storage.diagnostics().unwrap();
    assert_eq!(diagnostics.schema_version, SCHEMA_VERSION);
    assert_eq!(diagnostics.record_version, RECORD_VERSION);
    assert_eq!(diagnostics.application_id, APPLICATION_ID);
    assert_eq!(diagnostics.journal_mode, "wal");
    assert_eq!(diagnostics.synchronous, 2);
    assert!(diagnostics.foreign_keys);
    assert!(has_wal_reset_fix(rusqlite::version_number()));
    assert!(!diagnostics.sqlite_source_id.is_empty());
    storage.connection.pragma_update(None, "synchronous", "NORMAL").unwrap();
    drop(storage);
    let reopened = Storage::open(directory.path().join("synthetic.sqlite")).unwrap();
    assert_eq!(reopened.diagnostics().unwrap().synchronous, 2);
    assert_eq!(reopened.revision().unwrap(), 0);
}

#[test]
fn t08_identical_retry_is_noop_and_whole_payload_conflict_rolls_back_batch() {
    let (_directory, mut storage) = database();
    let fixture = demo_synthetic_fixture();
    assert_eq!(storage.insert_observations(&fixture[..2]).unwrap(), InsertSummary {
        inserted: 2, duplicates: 0, report_revision: 1,
    });
    assert_eq!(storage.insert_observations(&fixture[..2]).unwrap(), InsertSummary {
        inserted: 0, duplicates: 2, report_revision: 1,
    });
    let mut changed = fixture[0].clone();
    changed.device_id = "different-synthetic-device".into();
    let result = storage.insert_observations(&[fixture[2].clone(), changed]);
    assert!(matches!(result, Err(StorageError::ObservationConflict { .. })));
    assert_eq!(count(&storage, "observations"), 2);
    assert_eq!(storage.revision().unwrap(), 1);
    assert_eq!(raw(&storage, &fixture[0].id), fixture[0]);
    assert_eq!(storage.insert_observations(&fixture[2..3]).unwrap().inserted, 1);
}

#[test]
fn t08_changed_arrival_or_semantics_is_not_mistaken_for_same_interval_retry() {
    let (_directory, mut storage) = database();
    let original = demo_synthetic_fixture().remove(0);
    storage.insert_observations(std::slice::from_ref(&original)).unwrap();
    for change in 0..3 {
        let mut observation = original.clone();
        match change {
            0 => observation.received_at_ms += 1,
            1 => observation.category = "different-interpretation".into(),
            _ => observation.source_id = "another-source".into(),
        }
        assert!(matches!(storage.insert_observations(&[observation]), Err(StorageError::ObservationConflict { .. })));
    }
    assert_eq!(count(&storage, "observations"), 1);
    assert_eq!(storage.revision().unwrap(), 1);
}

#[test]
fn t10_correction_survives_rebuild_changed_rules_and_file_reopen() {
    let (directory, mut storage) = database();
    assert_eq!(storage.seed_synthetic_fixture().unwrap().inserted, 1440);
    let original = raw(&storage, "synthetic-555");
    let result = storage.apply_correction(&command("edit-555", "synthetic-555", "manual-learning", 0), 1_700_000_000_000).unwrap();
    assert_eq!(result.correction.revision, 1);
    assert_eq!(result.report_revision, 2);
    let changed_rules = vec![CategoryRule { app_id: "synthetic:browser".into(), category: "rule-reclassified".into() }];
    let report = storage.day_report(&day(), &changed_rules).unwrap();
    let chosen = report.intervals.iter().find(|row| row.id == "synthetic-555").unwrap();
    assert_eq!(chosen.category, "manual-learning");
    assert!(chosen.corrected);
    assert_eq!(chosen.correction_revision, 1);
    assert_eq!(report.intervals.iter().find(|row| row.id == "synthetic-554").unwrap().category, "rule-reclassified");
    assert_eq!(raw(&storage, "synthetic-555"), original);
    drop(storage);
    let mut reopened = Storage::open(directory.path().join("synthetic.sqlite")).unwrap();
    assert_eq!(reopened.day_report(&day(), &changed_rules).unwrap(), report);
    assert_eq!(raw(&reopened, "synthetic-555"), original);
    assert_eq!(reopened.seed_synthetic_fixture().unwrap(), InsertSummary {
        inserted: 0, duplicates: 1440, report_revision: 2,
    });
    assert_eq!(count(&reopened, "corrections"), 1);
}

#[test]
fn retry_ignores_new_server_timestamp_preserves_original_even_after_later_edit() {
    let (_directory, mut storage) = database();
    storage.seed_synthetic_fixture().unwrap();
    let first = command("first-command", "synthetic-555", "first", 0);
    let first_result = storage.apply_correction(&first, 100).unwrap();
    let retry = storage.apply_correction(&first, 999).unwrap();
    assert!(retry.replayed);
    assert_eq!(retry.correction, first_result.correction);
    assert_eq!(retry.report_revision, first_result.report_revision);
    storage.apply_correction(&command("second-command", "synthetic-555", "latest", 1), 200).unwrap();
    let retry = storage.apply_correction(&first, i64::MAX).unwrap();
    assert!(retry.replayed);
    assert_eq!(retry.correction.created_at_ms, 100);
    assert_eq!(retry.correction.revision, 1);
    assert_eq!(retry.report_revision, 3);
    let report = storage.day_report(&day(), &[]).unwrap();
    let chosen = report.intervals.iter().find(|row| row.id == "synthetic-555").unwrap();
    assert_eq!(chosen.category, "latest");
    assert_eq!(chosen.correction_revision, 2);
    assert_eq!(count(&storage, "corrections"), 2);
}

#[test]
fn correction_command_conflict_and_stale_revision_never_overwrite() {
    let (_directory, mut storage) = database();
    storage.seed_synthetic_fixture().unwrap();
    storage.apply_correction(&command("command-1", "synthetic-555", "learning", 0), 100).unwrap();
    assert!(matches!(storage.apply_correction(&command("command-1", "synthetic-555", "other", 0), 200),
        Err(StorageError::CommandConflict { .. })));
    assert!(matches!(storage.apply_correction(&command("command-2", "synthetic-555", "other", 0), 200),
        Err(StorageError::RevisionConflict { expected: 0, actual: 1, .. })));
    assert_eq!(storage.revision().unwrap(), 2);
    assert_eq!(count(&storage, "corrections"), 1);
    // A correction to another observation is independent of the report's generation.
    assert_eq!(storage.apply_correction(&command("command-3", "synthetic-554", "independent", 0), 300).unwrap().correction.revision, 1);
}

#[test]
fn missing_observation_or_invalid_timestamp_does_not_commit_a_correction() {
    let (_directory, mut storage) = database();
    assert!(matches!(storage.apply_correction(&command("missing", "nonexistent", "learning", 0), 100),
        Err(StorageError::ObservationNotFound { .. })));
    storage.insert_observations(&demo_synthetic_fixture()[..1]).unwrap();
    assert!(matches!(storage.apply_correction(&command("invalid-time", "synthetic-1", "learning", 0), i64::MAX),
        Err(StorageError::Domain(_))));
    assert_eq!(count(&storage, "corrections"), 0);
    assert_eq!(storage.revision().unwrap(), 1);
}

#[test]
fn future_schema_and_foreign_database_are_rejected_without_persistent_changes() {
    let directory = tempfile::tempdir().unwrap();
    for (name, setup, future) in [
        ("future.sqlite", "PRAGMA user_version=99; CREATE TABLE future_data(value TEXT); INSERT INTO future_data VALUES ('synthetic');", true),
        ("foreign.sqlite", "CREATE TABLE unrelated(value TEXT); INSERT INTO unrelated VALUES ('synthetic');", false),
    ] {
        let path = directory.path().join(name);
        let connection = Connection::open(&path).unwrap();
        connection.execute_batch(setup).unwrap();
        drop(connection);
        let original = std::fs::read(&path).unwrap();
        let error = match Storage::open(&path) { Ok(_) => panic!("foreign/future database accepted"), Err(error) => error };
        if future { assert!(matches!(error, StorageError::UnsupportedSchema { found: 99, .. })); }
        else { assert!(matches!(error, StorageError::UnrecognizedDatabase)); }
        assert_eq!(std::fs::read(path).unwrap(), original);
    }
}

#[test]
fn bounded_query_rejects_excess_rows_and_payload_without_partial_success() {
    let (_directory, mut storage) = database();
    storage.insert_observations(&demo_synthetic_fixture()[..3]).unwrap();
    assert!(matches!(storage.report_with_limits(&day(), &[], 2, MAX_REPORT_BYTES),
        Err(StorageError::ReportTooLarge { limit: 2 })));
    assert!(matches!(storage.report_with_limits(&day(), &[], 3, 1),
        Err(StorageError::ReportTooLarge { limit: 1 })));
    assert_eq!(storage.day_report(&day(), &[]).unwrap().intervals.len(), 3);
    assert_eq!(storage.revision().unwrap(), 1);
}

#[test]
fn day_filter_is_half_open_and_does_not_pull_adjacent_day_records() {
    let (_directory, mut storage) = database();
    let bounds = day_bounds(DEMO_DATE, DEMO_TIME_ZONE).unwrap();
    let template = demo_synthetic_fixture().remove(0);
    let observations: Vec<_> = [
        ("prior", bounds.start_ms - 60_000, bounds.start_ms),
        ("carry", bounds.start_ms - 60_000, bounds.start_ms + 60_000),
        ("inside", bounds.start_ms + 60_000, bounds.start_ms + 120_000),
        ("next", bounds.end_ms, bounds.end_ms + 60_000),
    ].into_iter().map(|(id, start_ms, end_ms)| {
        let mut observation = template.clone();
        observation.id = id.into();
        observation.measurement = Measurement::Interval { start_ms, end_ms };
        observation
    }).collect();
    storage.insert_observations(&observations).unwrap();
    let report = storage.day_report(&day(), &[]).unwrap();
    assert_eq!(report.intervals.iter().map(|row| row.id.as_str()).collect::<Vec<_>>(), ["carry", "inside"]);
    assert_eq!(report.intervals[0].start_ms, bounds.start_ms);
    assert_eq!(report.observed_coverage_ms, 120_000);
    assert_eq!(count(&storage, "observations"), 4);
}

#[test]
fn aggregate_payload_is_preserved_without_sql_prorating_or_exact_union() {
    let (_directory, mut storage) = database();
    let bounds = day_bounds(DEMO_DATE, DEMO_TIME_ZONE).unwrap();
    let mut observation = demo_synthetic_fixture().remove(0);
    observation.id = "delayed-aggregate".into();
    observation.device_id = "synthetic-phone".into();
    observation.measurement = Measurement::Aggregate {
        period_start_ms: bounds.start_ms - 60_000, period_end_ms: bounds.end_ms + 60_000, duration_ms: 3_600_000,
    };
    storage.insert_observations(std::slice::from_ref(&observation)).unwrap();
    assert_eq!(raw(&storage, &observation.id), observation);
    let report = storage.day_report(&day(), &[]).unwrap();
    assert!(report.intervals.is_empty());
    assert_eq!(report.aggregates.len(), 1);
    assert_eq!(report.observed_coverage_ms, 0);
    assert_eq!(report.unobserved_ms, report.day_duration_ms);
}

#[test]
fn exhausted_generation_rolls_back_inserted_payload_and_correction_together() {
    let (_directory, mut storage) = database();
    storage.insert_observations(&demo_synthetic_fixture()[..1]).unwrap();
    storage.connection.execute("UPDATE storage_metadata SET report_revision=?1", [i64::MAX]).unwrap();
    assert!(matches!(storage.insert_observations(&demo_synthetic_fixture()[1..2]), Err(StorageError::RevisionExhausted)));
    assert_eq!(count(&storage, "observations"), 1);
    assert!(matches!(storage.apply_correction(&command("overflow", "synthetic-1", "learning", 0), 100), Err(StorageError::RevisionExhausted)));
    assert_eq!(count(&storage, "corrections"), 0);
    assert_eq!(storage.revision().unwrap(), i64::MAX as u64);
}

#[test]
fn corrupted_index_and_record_version_fail_closed() {
    let (_directory, mut storage) = database();
    storage.insert_observations(&demo_synthetic_fixture()[..1]).unwrap();
    storage.connection.execute("UPDATE observations SET scope_start_ms=scope_start_ms-1", []).unwrap();
    assert!(matches!(storage.day_report(&day(), &[]), Err(StorageError::CorruptData(_))));
    assert!(matches!(decode_observation(99, "{}"), Err(StorageError::CorruptData(_))));
}

#[test]
fn invalid_batch_is_rejected_before_any_record_is_written() {
    let (_directory, mut storage) = database();
    let mut rows = demo_synthetic_fixture()[..2].to_vec();
    rows[1].category.clear();
    assert!(matches!(storage.insert_observations(&rows), Err(StorageError::Domain(_))));
    assert_eq!(count(&storage, "observations"), 0);
    assert_eq!(storage.revision().unwrap(), 0);
    assert_eq!(storage.day_report(&day(), &default_category_rules()).unwrap().intervals.len(), 0);
}
