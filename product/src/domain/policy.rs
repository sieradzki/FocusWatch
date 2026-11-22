use super::{DayReport, DomainError, ObservationQuality, union_duration_ms, validate_text};
use serde::{Deserialize, Serialize};

/// An explicitly selected intersection of two named sources on one device.
///
/// This is a policy input, not an inferred measure of attention or working time.
/// Source kinds do not choose the policy automatically. It uses only the known
/// interval/checkpoint windows already present in the requested day report;
/// unknown windows and period aggregates cannot establish coincident coverage.
/// Nominal UTC overlap does not remove the report's source-clock uncertainty.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SourceOverlapPolicy {
    pub device_id: String,
    pub left_source_id: String,
    pub right_source_id: String,
}

impl SourceOverlapPolicy {
    pub fn evaluate_ms(&self, report: &DayReport) -> Result<i64, DomainError> {
        validate_text("overlap device_id", &self.device_id, 256)?;
        validate_text("overlap left_source_id", &self.left_source_id, 256)?;
        validate_text("overlap right_source_id", &self.right_source_id, 256)?;

        let observed_windows = |source_id: &str| {
            report
                .intervals
                .iter()
                .filter(|row| {
                    row.device_id == self.device_id
                        && row.source_id == source_id
                        && row.quality != ObservationQuality::Unknown
                })
                .map(|row| (row.start_ms, row.end_ms))
                .collect::<Vec<_>>()
        };
        let mut left = observed_windows(&self.left_source_id);
        let right = observed_windows(&self.right_source_id);
        let separate = union_duration_ms(&left)?
            .checked_add(union_duration_ms(&right)?)
            .ok_or(DomainError::DurationOverflow)?;
        left.extend(right);
        // |A intersect B| = |A| + |B| - |A union B|. Union each source first,
        // so overlapping records or restarted epochs never multiply the result.
        separate
            .checked_sub(union_duration_ms(&left)?)
            .ok_or(DomainError::DurationOverflow)
    }
}
