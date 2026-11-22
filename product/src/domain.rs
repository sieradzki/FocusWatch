//! Portable observation semantics. No OS, database, network or wall-clock reads.
//! Exact coverage is not a claim about a person's attention or working time.

mod report;
mod time;

pub use report::{build_report, union_duration_ms};
pub use time::{day_bounds, DayBounds};

use serde::{Deserialize, Serialize};
use std::fmt;

pub const DEMO_DATE: &str = "2026-11-17";
pub const DEMO_TIME_ZONE: &str = "UTC";

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SourceKind {
    Foreground,
    Input,
    Lock,
    Media,
    Other,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ObservationQuality {
    Observed,
    Synthetic,
    Unknown,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ClockDiscontinuity {
    WallClockReversed,
    SourceRestart,
    SuspendResume,
    Unknown,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Measurement {
    Interval {
        start_ms: i64,
        end_ms: i64,
    },
    /// Confirmed through the last checkpoint only; no fabricated crash tail.
    OpenInterval {
        start_ms: i64,
        last_observed_ms: i64,
    },
    Aggregate {
        period_start_ms: i64,
        period_end_ms: i64,
        duration_ms: i64,
    },
}

impl Measurement {
    pub fn bounds(&self) -> (i64, i64) {
        match *self {
            Self::Interval { start_ms, end_ms } => (start_ms, end_ms),
            Self::OpenInterval { start_ms, last_observed_ms } => (start_ms, last_observed_ms),
            Self::Aggregate {
                period_start_ms,
                period_end_ms,
                ..
            } => (period_start_ms, period_end_ms),
        }
    }

    pub fn validate(&self) -> Result<(), DomainError> {
        let (start, end) = self.bounds();
        validate_timestamp(start)?;
        validate_timestamp(end)?;
        let open = matches!(self, Self::OpenInterval { .. });
        let span = end
            .checked_sub(start)
            .filter(|duration| *duration > 0 || (open && *duration == 0))
            .ok_or(DomainError::InvalidInterval {
                start_ms: start,
                end_ms: end,
            })?;
        if let Self::Aggregate { duration_ms, .. } = self {
            if *duration_ms < 0 || *duration_ms > span {
                return Err(DomainError::InvalidAggregateDuration(*duration_ms));
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Observation {
    pub id: String,
    pub device_id: String,
    pub source_id: String,
    pub source_kind: SourceKind,
    pub session_id: String,
    pub generation: u64,
    pub sequence: u64,
    pub granularity_ms: u64,
    pub time_uncertainty_ms: u64,
    pub boot_id: Option<String>,
    pub monotonic_start_ms: Option<u64>,
    pub monotonic_end_ms: Option<u64>,
    pub clock_discontinuity: Option<ClockDiscontinuity>,
    /// Namespaced identity, for example `synthetic:editor`, never a display label.
    pub app_id: String,
    pub app_name: String,
    /// Baseline interpretation; a rule or durable manual correction may override it.
    pub category: String,
    pub quality: ObservationQuality,
    /// Arrival time is distinct from the source's measured scope and may be delayed.
    pub received_at_ms: i64,
    pub measurement: Measurement,
}

impl Observation {
    pub fn bounds(&self) -> (i64, i64) {
        self.measurement.bounds()
    }

    pub fn validate(&self) -> Result<(), DomainError> {
        validate_text("id", &self.id, 256)?;
        validate_text("device_id", &self.device_id, 256)?;
        validate_text("source_id", &self.source_id, 256)?;
        validate_text("session_id", &self.session_id, 256)?;
        if self.granularity_ms == 0 {
            return Err(DomainError::InvalidField("granularity_ms"));
        }
        if let Some(boot) = &self.boot_id {
            validate_text("boot_id", boot, 256)?;
        } else if self.monotonic_start_ms.is_some() || self.monotonic_end_ms.is_some() {
            return Err(DomainError::InvalidField("boot_id for monotonic timestamps"));
        }
        if let (Some(start), Some(end)) = (self.monotonic_start_ms, self.monotonic_end_ms) {
            if end < start {
                return Err(DomainError::InvalidField("monotonic time interval"));
            }
        }
        validate_text("app_id", &self.app_id, 512)?;
        validate_text("app_name", &self.app_name, 512)?;
        validate_text("category", &self.category, 128)?;
        validate_timestamp(self.received_at_ms)?;
        self.measurement.validate()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CategoryRule {
    pub app_id: String,
    pub category: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CategoryCorrection {
    pub id: String,
    pub observation_id: String,
    pub category: String,
    /// Per-observation revision. It is not the report's global snapshot revision.
    pub revision: u64,
    pub created_at_ms: i64,
}

impl CategoryCorrection {
    pub fn validate(&self) -> Result<(), DomainError> {
        validate_text("correction id", &self.id, 256)?;
        validate_text("observation_id", &self.observation_id, 256)?;
        validate_text("category", &self.category, 128)?;
        if self.revision == 0 {
            return Err(DomainError::InvalidCorrectionRevision);
        }
        validate_timestamp(self.created_at_ms)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CorrectionRequest {
    pub command_id: String,
    pub observation_id: String,
    pub category: String,
    pub expected_revision: u64,
}

impl CorrectionRequest {
    pub fn validate(&self) -> Result<(), DomainError> {
        validate_text("command_id", &self.command_id, 256)?;
        validate_text("observation_id", &self.observation_id, 256)?;
        validate_text("category", &self.category, 128)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DayRequest {
    pub date: String,
    pub time_zone: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportInterval {
    pub id: String,
    pub device_id: String,
    pub source_id: String,
    pub source_kind: SourceKind,
    pub session_id: String,
    pub generation: u64,
    pub sequence: u64,
    pub granularity_ms: u64,
    pub time_uncertainty_ms: u64,
    pub boot_id: Option<String>,
    pub monotonic_start_ms: Option<u64>,
    pub monotonic_end_ms: Option<u64>,
    pub clock_discontinuity: Option<ClockDiscontinuity>,
    pub app_id: String,
    pub app_name: String,
    pub category: String,
    pub start_ms: i64,
    pub end_ms: i64,
    pub duration_ms: i64,
    pub quality: ObservationQuality,
    pub corrected: bool,
    pub correction_revision: u64,
    pub open: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AggregateView {
    pub id: String,
    pub device_id: String,
    pub source_id: String,
    pub source_kind: SourceKind,
    pub session_id: String,
    pub generation: u64,
    pub sequence: u64,
    pub granularity_ms: u64,
    pub time_uncertainty_ms: u64,
    pub boot_id: Option<String>,
    pub monotonic_start_ms: Option<u64>,
    pub monotonic_end_ms: Option<u64>,
    pub clock_discontinuity: Option<ClockDiscontinuity>,
    pub app_id: String,
    pub app_name: String,
    pub category: String,
    pub period_start_ms: i64,
    pub period_end_ms: i64,
    pub reported_duration_ms: i64,
    pub quality: ObservationQuality,
    pub corrected: bool,
    pub correction_revision: u64,
    /// False means the value cannot be allocated to this particular day.
    pub fully_within_day: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SourceTotal {
    pub device_id: String,
    pub source_id: String,
    pub source_kind: SourceKind,
    pub session_id: String,
    pub generation: u64,
    pub observed_duration_ms: i64,
    pub unknown_duration_ms: i64,
    pub aggregate_count: u64,
    /// Reported for the original scopes, not added to the day's exact coverage.
    pub reported_aggregate_duration_ms: i64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CategoryTotal {
    pub category: String,
    /// Sum of exact per-source/category interval unions, not human attention.
    pub duration_ms: i64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DayReport {
    pub revision: u64,
    pub date: String,
    pub time_zone: String,
    pub start_ms: i64,
    pub end_ms: i64,
    pub day_duration_ms: i64,
    pub observed_coverage_ms: i64,
    pub summed_source_ms: i64,
    pub unknown_coverage_ms: i64,
    /// No exact observation, including an explicitly unknown one, covered this scope.
    pub unobserved_ms: i64,
    pub intervals: Vec<ReportInterval>,
    pub aggregates: Vec<AggregateView>,
    pub source_totals: Vec<SourceTotal>,
    pub category_totals: Vec<CategoryTotal>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DomainError {
    InvalidDate(String),
    InvalidTimeZone(String),
    UnrepresentableLocalDay(String),
    InvalidTimestamp(i64),
    InvalidInterval { start_ms: i64, end_ms: i64 },
    InvalidAggregateDuration(i64),
    InvalidField(&'static str),
    InvalidCorrectionRevision,
    ObservationIdConflict(String),
    RuleConflict(String),
    CorrectionRevisionConflict { observation_id: String, revision: u64 },
    DurationOverflow,
}

impl fmt::Display for DomainError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidDate(date) => write!(f, "invalid ISO date: {date}"),
            Self::InvalidTimeZone(zone) => write!(f, "invalid IANA time zone: {zone}"),
            Self::UnrepresentableLocalDay(date) => write!(f, "local date has no representable day: {date}"),
            Self::InvalidTimestamp(value) => write!(f, "timestamp outside supported UTC range: {value}"),
            Self::InvalidInterval { start_ms, end_ms } => write!(f, "invalid half-open interval [{start_ms}, {end_ms})"),
            Self::InvalidAggregateDuration(value) => write!(f, "aggregate duration outside its source period: {value}"),
            Self::InvalidField(field) => write!(f, "invalid or oversized {field}"),
            Self::InvalidCorrectionRevision => f.write_str("correction revision must be positive"),
            Self::ObservationIdConflict(id) => write!(f, "observation ID has conflicting payloads: {id}"),
            Self::RuleConflict(app) => write!(f, "conflicting category rules for {app}"),
            Self::CorrectionRevisionConflict { observation_id, revision } => write!(f, "conflicting correction for {observation_id} at revision {revision}"),
            Self::DurationOverflow => f.write_str("duration arithmetic overflow"),
        }
    }
}

impl std::error::Error for DomainError {}

pub(crate) fn validate_text(field: &'static str, text: &str, max_bytes: usize) -> Result<(), DomainError> {
    if text.trim().is_empty() || text.len() > max_bytes || text.contains('\0') {
        Err(DomainError::InvalidField(field))
    } else {
        Ok(())
    }
}

fn validate_timestamp(value: i64) -> Result<(), DomainError> {
    chrono::DateTime::<chrono::Utc>::from_timestamp_millis(value)
        .map(|_| ())
        .ok_or(DomainError::InvalidTimestamp(value))
}

/// Editable initial rules, independent of the immutable synthetic observations.
pub fn default_category_rules() -> Vec<CategoryRule> {
    [("synthetic:editor", "work"), ("synthetic:reader", "learning"), ("synthetic:player", "leisure")]
        .into_iter()
        .map(|(app_id, category)| CategoryRule { app_id: app_id.into(), category: category.into() })
        .collect()
}

/// Committed artificial minute-by-minute day. No real tracker or private history.
pub fn demo_synthetic_fixture() -> Vec<Observation> {
    let start = day_bounds(DEMO_DATE, DEMO_TIME_ZONE).expect("constant demo date is valid").start_ms;
    include_str!("../fixtures/day-2026-11-17.tsv")
        .lines()
        .skip(1)
        .map(|line| {
            let columns: Vec<&str> = line.split('\t').collect();
            assert_eq!(columns.len(), 5, "committed synthetic fixture columns");
            let start_ms = start + columns[1].parse::<i64>().expect("synthetic start seconds") * 1_000;
            let end_ms = start + columns[2].parse::<i64>().expect("synthetic end seconds") * 1_000;
            Observation {
                id: format!("synthetic-{}", columns[0]),
                device_id: "synthetic-desktop".into(),
                source_id: "synthetic-foreground".into(),
                source_kind: SourceKind::Foreground,
                session_id: "synthetic-session-1".into(),
                generation: 1,
                sequence: columns[0].parse().expect("synthetic sequence"),
                granularity_ms: 60_000,
                time_uncertainty_ms: 0,
                boot_id: Some("synthetic-boot-1".into()),
                monotonic_start_ms: Some((start_ms - start) as u64),
                monotonic_end_ms: Some((end_ms - start) as u64),
                clock_discontinuity: None,
                app_id: format!("synthetic:{}", columns[3]),
                app_name: columns[3].into(),
                category: columns[4].into(),
                quality: ObservationQuality::Synthetic,
                received_at_ms: end_ms,
                measurement: Measurement::Interval { start_ms, end_ms },
            }
        })
        .collect()
}
