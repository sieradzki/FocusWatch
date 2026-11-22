use super::DomainError;
use chrono::{Duration, LocalResult, NaiveDate, TimeZone};
use chrono_tz::Tz;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DayBounds {
    pub date: String,
    pub time_zone: String,
    pub start_ms: i64,
    pub end_ms: i64,
    pub duration_ms: i64,
}

/// The first real instant of a civil date, including a skipped/ambiguous midnight.
/// IANA offsets and transitions have integer-second precision. A completely
/// skipped civil date is rejected by `day_bounds`, never silently renamed.
fn civil_boundary(date: NaiveDate, zone: Tz) -> Result<i64, DomainError> {
    let midnight = date
        .and_hms_opt(0, 0, 0)
        .ok_or_else(|| DomainError::UnrepresentableLocalDay(date.to_string()))?;
    for seconds in 0_i64..=172_800 {
        let candidate = midnight
            .checked_add_signed(Duration::seconds(seconds))
            .ok_or_else(|| DomainError::UnrepresentableLocalDay(date.to_string()))?;
        let instant = match zone.from_local_datetime(&candidate) {
            LocalResult::Single(value) => Some(value),
            LocalResult::Ambiguous(first, second) => Some(first.min(second)),
            LocalResult::None => None,
        };
        if let Some(value) = instant {
            return Ok(value.timestamp_millis());
        }
    }
    Err(DomainError::UnrepresentableLocalDay(date.to_string()))
}

pub fn day_bounds(date: &str, time_zone: &str) -> Result<DayBounds, DomainError> {
    let parsed = NaiveDate::parse_from_str(date, "%Y-%m-%d")
        .map_err(|_| DomainError::InvalidDate(date.into()))?;
    // The public contract is an ISO calendar date, not a permissive date parser.
    if date.len() != 10 || parsed.format("%Y-%m-%d").to_string() != date {
        return Err(DomainError::InvalidDate(date.into()));
    }
    let zone: Tz = time_zone
        .parse()
        .map_err(|_| DomainError::InvalidTimeZone(time_zone.into()))?;
    let next = parsed
        .succ_opt()
        .ok_or_else(|| DomainError::UnrepresentableLocalDay(date.into()))?;
    let start_ms = civil_boundary(parsed, zone)?;
    let end_ms = civil_boundary(next, zone)?;
    let duration_ms = end_ms
        .checked_sub(start_ms)
        .filter(|value| *value > 0)
        .ok_or_else(|| DomainError::UnrepresentableLocalDay(date.into()))?;
    Ok(DayBounds {
        date: date.into(),
        time_zone: zone.name().into(),
        start_ms,
        end_ms,
        duration_ms,
    })
}
