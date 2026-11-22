use chrono::DateTime;
use focuswatch_core::domain::*;
use serde::Deserialize;

const MINUTE: i64 = 60_000;
const HOUR: i64 = 60 * MINUTE;
const DAY: i64 = 24 * HOUR;

fn utc(text: &str) -> i64 {
    DateTime::parse_from_rfc3339(text).unwrap().timestamp_millis()
}

fn request() -> DayRequest {
    DayRequest { date: DEMO_DATE.into(), time_zone: "UTC".into() }
}

fn observation(id: &str, device: &str, source: &str, start: i64, end: i64) -> Observation {
    Observation {
        id: id.into(),
        device_id: device.into(),
        source_id: source.into(),
        source_kind: SourceKind::Other,
        session_id: "test-session".into(),
        generation: 1,
        sequence: 1,
        granularity_ms: 1,
        time_uncertainty_ms: 0,
        boot_id: Some("test-boot".into()),
        monotonic_start_ms: None,
        monotonic_end_ms: None,
        clock_discontinuity: None,
        app_id: "synthetic:editor".into(),
        app_name: "Synthetic editor".into(),
        category: "unclassified".into(),
        quality: ObservationQuality::Synthetic,
        received_at_ms: end,
        measurement: Measurement::Interval { start_ms: start, end_ms: end },
    }
}

fn report(observations: &[Observation]) -> DayReport {
    build_report(&request(), observations, &[], &[], 0).unwrap()
}

#[test]
fn t01_parallel_sources_keep_independent_durations_without_splitting_attention() {
    let t = utc("2026-11-17T10:00:00Z");
    let rows = [observation("a", "pc", "foreground", t, t + HOUR), observation("b", "pc", "independent", t, t + HOUR)];
    let day = report(&rows);
    assert_eq!(day.intervals.len(), 2);
    assert_eq!(day.summed_source_ms, 2 * HOUR);
    assert_eq!(day.observed_coverage_ms, HOUR);
    assert!(day.source_totals.iter().all(|source| source.observed_duration_ms == HOUR));
    let encoded = serde_json::to_value(day).unwrap();
    assert!(encoded.get("attention_ms").is_none());
    assert!(encoded.get("working_time_ms").is_none());
}

#[test]
fn t02_presence_and_longer_independent_signal_remain_separate() {
    let t = utc("2026-11-17T10:00:00Z");
    let mut presence = observation("presence", "pc", "input", t, t + HOUR);
    presence.source_kind = SourceKind::Input;
    let other = observation("other", "pc", "source-b", t, t + 2 * HOUR);
    let day = report(&[presence, other]);
    assert_eq!(day.observed_coverage_ms, 2 * HOUR);
    assert_eq!(day.summed_source_ms, 3 * HOUR);
    assert_eq!(day.source_totals.iter().find(|s| s.source_kind == SourceKind::Input).unwrap().observed_duration_ms, HOUR);
}

#[test]
fn t03_two_devices_exact_scopes_union_to_three_hours() {
    let t = utc("2026-11-17T10:00:00Z");
    let rows = [observation("pc", "pc", "foreground", t, t + 2 * HOUR), observation("phone", "phone", "foreground", t + HOUR, t + 3 * HOUR)];
    let day = report(&rows);
    assert_eq!(day.source_totals.len(), 2);
    assert_eq!(day.summed_source_ms, 4 * HOUR);
    assert_eq!(day.observed_coverage_ms, 3 * HOUR);
}

#[test]
fn t03_delayed_day_aggregate_does_not_acquire_an_invented_timeline() {
    let day_start = utc("2026-11-17T00:00:00Z");
    let pc = observation("pc", "pc", "foreground", day_start + 9 * HOUR, day_start + 9 * HOUR + 30 * MINUTE);
    let mut phone = observation("phone", "phone", "usage-aggregate", day_start, day_start + DAY);
    phone.measurement = Measurement::Aggregate { period_start_ms: day_start, period_end_ms: day_start + DAY, duration_ms: 20 * MINUTE };
    phone.received_at_ms = day_start + 2 * DAY;
    phone.granularity_ms = DAY as u64;
    phone.time_uncertainty_ms = 5 * MINUTE as u64;
    phone.app_id = "android:synthetic.application".into();
    let original = phone.clone();
    let day = report(&[pc, phone]);
    assert_eq!(day.intervals.len(), 1);
    assert_eq!(day.aggregates.len(), 1);
    assert_eq!(day.observed_coverage_ms, 30 * MINUTE);
    assert_eq!(day.summed_source_ms, 30 * MINUTE);
    assert_eq!(day.aggregates[0].reported_duration_ms, 20 * MINUTE);
    assert!(day.aggregates[0].fully_within_day);
    assert_eq!(day.aggregates[0].period_start_ms, original.bounds().0);
    assert_eq!(day.aggregates[0].time_uncertainty_ms, original.time_uncertainty_ms);
    assert_eq!(day.aggregates[0].app_id, "android:synthetic.application");
}

#[test]
fn aggregate_spanning_multiple_days_is_not_prorated_or_included_in_exact_totals() {
    let t = utc("2026-11-17T00:00:00Z");
    let mut row = observation("aggregate", "phone", "coarse", t - DAY, t + DAY);
    row.measurement = Measurement::Aggregate { period_start_ms: t - DAY, period_end_ms: t + DAY, duration_ms: HOUR };
    let day = report(&[row]);
    assert_eq!(day.aggregates[0].reported_duration_ms, HOUR);
    assert!(!day.aggregates[0].fully_within_day);
    assert_eq!(day.summed_source_ms, 0);
    assert_eq!(day.observed_coverage_ms, 0);
    assert_eq!(day.unobserved_ms, DAY);
    assert!(day.category_totals.is_empty());
}

#[test]
fn t04_half_open_adjacency_and_duplicate_intervals_have_no_double_boundary() {
    assert_eq!(union_duration_ms(&[(0, HOUR), (HOUR, 2 * HOUR)]).unwrap(), 2 * HOUR);
    assert_eq!(union_duration_ms(&[(0, HOUR), (0, HOUR), (HOUR, HOUR)]).unwrap(), HOUR);
    assert_eq!(union_duration_ms(&[]).unwrap(), 0);
}

#[test]
fn t05_midnight_clipping_conserves_the_original_duration() {
    let start = utc("2026-11-17T22:30:00Z");
    let end = utc("2026-11-18T00:30:00Z");
    let row = observation("cross-midnight", "pc", "fg", start, end);
    let original = row.clone();
    let first = build_report(&DayRequest { date: "2026-11-17".into(), time_zone: "Europe/Warsaw".into() }, std::slice::from_ref(&row), &[], &[], 0).unwrap();
    let second = build_report(&DayRequest { date: "2026-11-18".into(), time_zone: "Europe/Warsaw".into() }, std::slice::from_ref(&row), &[], &[], 0).unwrap();
    assert_eq!(first.observed_coverage_ms, 30 * MINUTE);
    assert_eq!(second.observed_coverage_ms, 90 * MINUTE);
    assert_eq!(first.observed_coverage_ms + second.observed_coverage_ms, end - start);
    assert_eq!(row, original);
}

#[derive(Deserialize)]
struct CivilCase {
    case: String,
    date: String,
    time_zone: String,
    expected_start: String,
    expected_end: String,
    expected_duration_ms: i64,
}

#[test]
fn t06_local_day_uses_independent_committed_23_24_25_hour_vectors() {
    let vectors: Vec<CivilCase> = serde_json::from_str(include_str!("../fixtures/civil-days.json")).unwrap();
    for case in vectors {
        let day = day_bounds(&case.date, &case.time_zone).unwrap();
        assert_eq!(day.start_ms, utc(&case.expected_start), "{} start", case.case);
        assert_eq!(day.end_ms, utc(&case.expected_end), "{} end", case.case);
        assert_eq!(day.duration_ms, case.expected_duration_ms, "{} duration", case.case);
    }
}

#[test]
fn t07_reversed_wall_clock_is_not_repaired_using_a_different_boot_monotonic_clock() {
    let t = utc("2026-11-17T09:00:00Z");
    let mut first = observation("old", "pc", "fg", t, t + HOUR);
    first.monotonic_start_ms = Some(0);
    first.monotonic_end_ms = Some(HOUR as u64);
    let mut next = observation("restarted", "pc", "fg", t + 30 * MINUTE, t + HOUR);
    next.session_id = "restarted-session".into();
    next.generation = 2;
    next.sequence = 0;
    next.boot_id = Some("different-boot".into());
    next.monotonic_start_ms = Some(0);
    next.monotonic_end_ms = Some(30 * MINUTE as u64);
    next.clock_discontinuity = Some(ClockDiscontinuity::WallClockReversed);
    next.time_uncertainty_ms = 30 * MINUTE as u64;
    let day = report(&[first, next]);
    assert_eq!(day.observed_coverage_ms, HOUR);
    assert_eq!(day.source_totals.len(), 2);
    assert_eq!(day.summed_source_ms, 90 * MINUTE);
    let restarted = day.intervals.iter().find(|r| r.id == "restarted").unwrap();
    assert_eq!(restarted.start_ms, t + 30 * MINUTE);
    assert_eq!(restarted.generation, 2);
    assert_eq!(restarted.sequence, 0);
    assert_eq!(restarted.clock_discontinuity, Some(ClockDiscontinuity::WallClockReversed));
    assert!(observation("negative", "pc", "fg", t + HOUR, t).validate().is_err());
}

#[test]
fn t07_crashed_open_interval_stops_at_last_confirmed_checkpoint_not_now_or_day_end() {
    let t = utc("2026-11-17T09:00:00Z");
    let mut open = observation("open", "pc", "fg", t, t + 10 * MINUTE);
    open.measurement = Measurement::OpenInterval { start_ms: t, last_observed_ms: t + 10 * MINUTE };
    open.clock_discontinuity = Some(ClockDiscontinuity::SourceRestart);
    let day = report(&[open]);
    assert_eq!(day.intervals[0].end_ms, t + 10 * MINUTE);
    assert!(day.intervals[0].open);
    assert_eq!(day.observed_coverage_ms, 10 * MINUTE);
    assert_eq!(day.unobserved_ms, DAY - 10 * MINUTE);
}

#[test]
fn open_point_at_exact_day_start_is_visible_but_contributes_zero_duration() {
    let t = utc("2026-11-17T00:00:00Z");
    let mut row = observation("open-point", "pc", "fg", t, t);
    row.measurement = Measurement::OpenInterval { start_ms: t, last_observed_ms: t };
    let day = report(&[row]);
    assert_eq!(day.intervals.len(), 1);
    assert!(day.intervals[0].open);
    assert_eq!(day.intervals[0].duration_ms, 0);
    assert_eq!(day.observed_coverage_ms, 0);
    assert_eq!(day.unobserved_ms, DAY);
}

#[test]
fn t25_report_zone_changes_clipping_not_source_time_or_provenance() {
    let t = utc("2026-11-17T22:30:00Z");
    let mut row = observation("uncertain", "pc", "fg", t, t + 2 * HOUR);
    row.granularity_ms = 60_000;
    row.time_uncertainty_ms = 15_000;
    row.sequence = 44;
    let original = row.clone();
    let utc_day = report(std::slice::from_ref(&row));
    let warsaw = build_report(&DayRequest { date: DEMO_DATE.into(), time_zone: "Europe/Warsaw".into() }, std::slice::from_ref(&row), &[], &[], 0).unwrap();
    assert_eq!(utc_day.observed_coverage_ms, 90 * MINUTE);
    assert_eq!(warsaw.observed_coverage_ms, 30 * MINUTE);
    assert_eq!(warsaw.intervals[0].granularity_ms, 60_000);
    assert_eq!(warsaw.intervals[0].time_uncertainty_ms, 15_000);
    assert_eq!(warsaw.intervals[0].sequence, 44);
    assert_eq!(row, original);
}

#[test]
fn unknown_source_coverage_and_no_data_do_not_turn_into_idle_or_work() {
    let t = utc("2026-11-17T10:00:00Z");
    let mut unknown = observation("unknown", "pc", "fg", t, t + HOUR);
    unknown.quality = ObservationQuality::Unknown;
    let day = report(&[unknown]);
    assert_eq!(day.observed_coverage_ms, 0);
    assert_eq!(day.unknown_coverage_ms, HOUR);
    assert_eq!(day.unobserved_ms, DAY - HOUR);
    assert!(day.category_totals.is_empty());
    let empty = report(&[]);
    assert_eq!(empty.observed_coverage_ms, 0);
    assert_eq!(empty.unknown_coverage_ms, 0);
    assert_eq!(empty.unobserved_ms, DAY);
}

#[test]
fn fixture_is_synthetic_complete_and_stable_for_the_desktop_correction_demo() {
    let observations = demo_synthetic_fixture();
    assert_eq!(observations.len(), 1440);
    assert!(observations.iter().all(|r| r.quality == ObservationQuality::Synthetic && r.validate().is_ok()));
    let row = observations.iter().find(|r| r.id == "synthetic-555").unwrap();
    assert_eq!(row.app_id, "synthetic:browser");
    assert_eq!(row.category, "unclassified");
    assert_eq!(row.sequence, 555);
    let day = build_report(&request(), &observations, &[], &default_category_rules(), 0).unwrap();
    assert_eq!(day.observed_coverage_ms, DAY);
    assert_eq!(day.summed_source_ms, DAY);
    assert_eq!(day.intervals.len(), 1440);
}

#[test]
fn invalid_dates_zones_measurements_and_clock_provenance_return_typed_errors() {
    assert!(matches!(day_bounds("2026-1-1", "UTC"), Err(DomainError::InvalidDate(_))));
    assert!(day_bounds("2026-02-30", "UTC").is_err());
    assert!(matches!(day_bounds(DEMO_DATE, "Invalid/TimeZone"), Err(DomainError::InvalidTimeZone(_))));
    assert!(day_bounds("2011-12-30", "Pacific/Apia").is_err());
    let t = utc("2026-11-17T10:00:00Z");
    let mut row = observation("x", "pc", "fg", t, t + HOUR);
    row.measurement = Measurement::Aggregate { period_start_ms: t, period_end_ms: t + HOUR, duration_ms: HOUR + 1 };
    assert!(row.validate().is_err());
    row.measurement = Measurement::Interval { start_ms: t, end_ms: t + HOUR };
    row.granularity_ms = 0;
    assert!(row.validate().is_err());
    row.granularity_ms = 1;
    row.monotonic_start_ms = Some(2);
    row.monotonic_end_ms = Some(1);
    assert!(row.validate().is_err());
    row.monotonic_end_ms = Some(3);
    row.boot_id = None;
    assert!(row.validate().is_err());
    assert!(matches!(union_duration_ms(&[(i64::MIN, i64::MAX)]), Err(DomainError::DurationOverflow)));
}
