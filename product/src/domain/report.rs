use super::{
    AggregateView, CategoryCorrection, CategoryRule, CategoryTotal, DayReport, DayRequest,
    DomainError, Measurement, Observation, ObservationQuality, ReportInterval, SourceKind,
    SourceTotal, day_bounds, validate_text,
};
use std::collections::BTreeMap;

type SourceKey = (String, String, String, u64, SourceKind);
type Intervals = Vec<(i64, i64)>;

#[derive(Default)]
struct SourceAccumulator {
    observed: Intervals,
    unknown: Intervals,
    aggregate_count: u64,
    aggregate_duration_ms: i64,
}

fn add(left: i64, right: i64) -> Result<i64, DomainError> {
    left.checked_add(right).ok_or(DomainError::DurationOverflow)
}

/// Length of the union of half-open intervals. Ordering and duplicates do not
/// alter the result; touching intervals have no double-counted boundary.
pub fn union_duration_ms(intervals: &[(i64, i64)]) -> Result<i64, DomainError> {
    let mut ordered = Vec::with_capacity(intervals.len());
    for &(start, end) in intervals {
        if end < start {
            return Err(DomainError::InvalidInterval {
                start_ms: start,
                end_ms: end,
            });
        }
        if end > start {
            ordered.push((start, end));
        }
    }
    ordered.sort_unstable();
    let Some(&(mut start, mut end)) = ordered.first() else {
        return Ok(0);
    };
    let mut total = 0_i64;
    for &(next_start, next_end) in ordered.iter().skip(1) {
        if next_start <= end {
            end = end.max(next_end);
        } else {
            total = add(
                total,
                end.checked_sub(start)
                    .ok_or(DomainError::DurationOverflow)?,
            )?;
            (start, end) = (next_start, next_end);
        }
    }
    add(
        total,
        end.checked_sub(start)
            .ok_or(DomainError::DurationOverflow)?,
    )
}

/// Build a deterministic day view. Arrival order is not source time, aggregates
/// never acquire invented positions, and corrections outrank re-evaluated rules.
/// `revision` is the storage snapshot generation, not a correction revision.
pub fn build_report(
    request: &DayRequest,
    observations: &[Observation],
    corrections: &[CategoryCorrection],
    rules: &[CategoryRule],
    revision: u64,
) -> Result<DayReport, DomainError> {
    let bounds = day_bounds(&request.date, &request.time_zone)?;
    let mut rule_map = BTreeMap::new();
    for rule in rules {
        validate_text("rule app_id", &rule.app_id, 512)?;
        validate_text("rule category", &rule.category, 128)?;
        if let Some(previous) = rule_map.insert(rule.app_id.as_str(), rule.category.as_str()) {
            if previous != rule.category {
                return Err(DomainError::RuleConflict(rule.app_id.clone()));
            }
        }
    }
    let mut correction_map: BTreeMap<&str, &CategoryCorrection> = BTreeMap::new();
    let mut correction_versions: BTreeMap<(&str, u64), &CategoryCorrection> = BTreeMap::new();
    for correction in corrections {
        correction.validate()?;
        let key = (correction.observation_id.as_str(), correction.revision);
        if let Some(previous) = correction_versions.insert(key, correction) {
            if previous != correction {
                return Err(DomainError::CorrectionRevisionConflict {
                    observation_id: correction.observation_id.clone(),
                    revision: correction.revision,
                });
            }
        }
        let latest = correction_map
            .entry(&correction.observation_id)
            .or_insert(correction);
        if correction.revision > latest.revision {
            *latest = correction;
        }
    }
    let mut unique = BTreeMap::new();
    for observation in observations {
        observation.validate()?;
        if let Some(previous) = unique.insert(observation.id.as_str(), observation) {
            if previous != observation {
                return Err(DomainError::ObservationIdConflict(observation.id.clone()));
            }
        }
    }

    let mut intervals = Vec::new();
    let mut aggregates = Vec::new();
    let mut all_observed = Vec::new();
    let mut all_unknown = Vec::new();
    let mut all_scoped = Vec::new();
    let mut sources: BTreeMap<SourceKey, SourceAccumulator> = BTreeMap::new();
    let mut categories: BTreeMap<(String, SourceKey), Intervals> = BTreeMap::new();
    for observation in unique.into_values() {
        let (scope_start, scope_end) = observation.bounds();
        let open_point = matches!(observation.measurement, Measurement::OpenInterval { .. })
            && scope_start == scope_end;
        let overlaps = if open_point {
            scope_start >= bounds.start_ms && scope_start < bounds.end_ms
        } else {
            scope_end > bounds.start_ms && scope_start < bounds.end_ms
        };
        if !overlaps {
            continue;
        }
        let correction = correction_map.get(observation.id.as_str()).copied();
        let category = correction
            .map(|value| value.category.as_str())
            .or_else(|| rule_map.get(observation.app_id.as_str()).copied())
            .unwrap_or(&observation.category)
            .to_owned();
        let correction_revision = correction.map_or(0, |value| value.revision);
        let source_key = (
            observation.device_id.clone(),
            observation.source_id.clone(),
            observation.session_id.clone(),
            observation.generation,
            observation.source_kind.clone(),
        );
        let source = sources.entry(source_key.clone()).or_default();
        match observation.measurement {
            Measurement::Interval { start_ms, end_ms }
            | Measurement::OpenInterval {
                start_ms,
                last_observed_ms: end_ms,
            } => {
                let open = matches!(observation.measurement, Measurement::OpenInterval { .. });
                let start = start_ms.max(bounds.start_ms);
                let end = end_ms.min(bounds.end_ms);
                let duration_ms = end
                    .checked_sub(start)
                    .ok_or(DomainError::DurationOverflow)?;
                all_scoped.push((start, end));
                if observation.quality == ObservationQuality::Unknown {
                    all_unknown.push((start, end));
                    source.unknown.push((start, end));
                } else {
                    all_observed.push((start, end));
                    source.observed.push((start, end));
                    categories
                        .entry((category.clone(), source_key))
                        .or_default()
                        .push((start, end));
                }
                intervals.push(ReportInterval {
                    id: observation.id.clone(),
                    device_id: observation.device_id.clone(),
                    source_id: observation.source_id.clone(),
                    source_kind: observation.source_kind.clone(),
                    session_id: observation.session_id.clone(),
                    generation: observation.generation,
                    sequence: observation.sequence,
                    granularity_ms: observation.granularity_ms,
                    time_uncertainty_ms: observation.time_uncertainty_ms,
                    boot_id: observation.boot_id.clone(),
                    monotonic_start_ms: observation.monotonic_start_ms,
                    monotonic_end_ms: observation.monotonic_end_ms,
                    clock_discontinuity: observation.clock_discontinuity.clone(),
                    received_at_ms: observation.received_at_ms,
                    app_id: observation.app_id.clone(),
                    app_name: observation.app_name.clone(),
                    category,
                    start_ms: start,
                    end_ms: end,
                    duration_ms,
                    quality: observation.quality.clone(),
                    corrected: correction.is_some(),
                    correction_revision,
                    open,
                });
            }
            Measurement::Aggregate {
                period_start_ms,
                period_end_ms,
                duration_ms,
            } => {
                source.aggregate_count = source
                    .aggregate_count
                    .checked_add(1)
                    .ok_or(DomainError::DurationOverflow)?;
                source.aggregate_duration_ms = add(source.aggregate_duration_ms, duration_ms)?;
                aggregates.push(AggregateView {
                    id: observation.id.clone(),
                    device_id: observation.device_id.clone(),
                    source_id: observation.source_id.clone(),
                    source_kind: observation.source_kind.clone(),
                    session_id: observation.session_id.clone(),
                    generation: observation.generation,
                    sequence: observation.sequence,
                    granularity_ms: observation.granularity_ms,
                    time_uncertainty_ms: observation.time_uncertainty_ms,
                    boot_id: observation.boot_id.clone(),
                    monotonic_start_ms: observation.monotonic_start_ms,
                    monotonic_end_ms: observation.monotonic_end_ms,
                    clock_discontinuity: observation.clock_discontinuity.clone(),
                    received_at_ms: observation.received_at_ms,
                    app_id: observation.app_id.clone(),
                    app_name: observation.app_name.clone(),
                    category,
                    period_start_ms,
                    period_end_ms,
                    reported_duration_ms: duration_ms,
                    quality: observation.quality.clone(),
                    corrected: correction.is_some(),
                    correction_revision,
                    fully_within_day: period_start_ms >= bounds.start_ms
                        && period_end_ms <= bounds.end_ms,
                });
            }
        }
    }
    intervals.sort_by(|a, b| {
        (a.start_ms, a.end_ms, &a.device_id, &a.source_id, &a.id).cmp(&(
            b.start_ms,
            b.end_ms,
            &b.device_id,
            &b.source_id,
            &b.id,
        ))
    });
    aggregates.sort_by(|a, b| {
        (a.period_start_ms, a.period_end_ms, &a.id).cmp(&(
            b.period_start_ms,
            b.period_end_ms,
            &b.id,
        ))
    });
    let mut source_totals = Vec::new();
    let mut summed_source_ms = 0_i64;
    for ((device_id, source_id, session_id, generation, source_kind), source) in sources {
        let observed_duration_ms = union_duration_ms(&source.observed)?;
        summed_source_ms = add(summed_source_ms, observed_duration_ms)?;
        source_totals.push(SourceTotal {
            device_id,
            source_id,
            source_kind,
            session_id,
            generation,
            observed_duration_ms,
            unknown_duration_ms: union_duration_ms(&source.unknown)?,
            aggregate_count: source.aggregate_count,
            reported_aggregate_duration_ms: source.aggregate_duration_ms,
        });
    }
    let mut category_map: BTreeMap<String, i64> = BTreeMap::new();
    for ((category, _source), scopes) in categories {
        let total = category_map.entry(category).or_default();
        *total = add(*total, union_duration_ms(&scopes)?)?;
    }
    let category_totals = category_map
        .into_iter()
        .map(|(category, duration_ms)| CategoryTotal {
            category,
            duration_ms,
        })
        .collect();
    Ok(DayReport {
        revision,
        date: bounds.date,
        time_zone: bounds.time_zone,
        start_ms: bounds.start_ms,
        end_ms: bounds.end_ms,
        day_duration_ms: bounds.duration_ms,
        observed_coverage_ms: union_duration_ms(&all_observed)?,
        summed_source_ms,
        unknown_coverage_ms: union_duration_ms(&all_unknown)?,
        unobserved_ms: bounds.duration_ms - union_duration_ms(&all_scoped)?,
        intervals,
        aggregates,
        source_totals,
        category_totals,
    })
}
