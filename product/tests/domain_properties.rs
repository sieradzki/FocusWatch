use focuswatch_core::domain::*;

#[test]
fn interval_union_matches_independent_unit_bitmap_oracle_and_is_order_invariant() {
    let mut random = 0x5eed_u64;
    for _case in 0..250 {
        let mut intervals = Vec::new();
        let mut covered = [false; 64];
        for _ in 0..12 {
            random = random.wrapping_mul(6364136223846793005).wrapping_add(1);
            let start = ((random >> 32) % 63) as usize;
            random = random.wrapping_mul(6364136223846793005).wrapping_add(1);
            let end = start + 1 + ((random >> 32) % (64 - start) as u64) as usize;
            intervals.push((start as i64, end as i64));
            covered[start..end].fill(true);
        }
        let expected = covered.iter().filter(|value| **value).count() as i64;
        assert_eq!(union_duration_ms(&intervals).unwrap(), expected);
        intervals.reverse();
        assert_eq!(union_duration_ms(&intervals).unwrap(), expected);
        intervals.rotate_left(5);
        assert_eq!(union_duration_ms(&intervals).unwrap(), expected);
        let duplicates = intervals.clone();
        intervals.extend(duplicates);
        assert_eq!(union_duration_ms(&intervals).unwrap(), expected);
    }
}

#[test]
fn splitting_any_interval_preserves_union_and_its_translation() {
    for start in -20..20 {
        for duration in 1..20 {
            let end = start + duration;
            let middle = start + duration / 2;
            assert_eq!(
                union_duration_ms(&[(start, middle), (middle, end)]).unwrap(),
                duration
            );
            assert_eq!(
                union_duration_ms(&[(start + 1000, end + 1000)]).unwrap(),
                duration
            );
        }
    }
}

#[test]
fn duplicate_event_retry_and_input_permutations_preserve_the_complete_report() {
    let rows = demo_synthetic_fixture();
    let request = DayRequest {
        date: DEMO_DATE.into(),
        time_zone: DEMO_TIME_ZONE.into(),
    };
    let rules = default_category_rules();
    let expected = build_report(&request, &rows, &[], &rules, 12).unwrap();
    let mut reordered = rows.clone();
    reordered.reverse();
    reordered.extend(rows.iter().take(12).cloned());
    assert_eq!(
        build_report(&request, &reordered, &[], &rules, 12).unwrap(),
        expected
    );
    let mut conflicting = rows.clone();
    let mut changed = rows[0].clone();
    changed.sequence += 1;
    conflicting.push(changed);
    assert!(matches!(
        build_report(&request, &conflicting, &[], &rules, 12),
        Err(DomainError::ObservationIdConflict(_))
    ));
}

#[test]
fn manual_correction_survives_rule_rebuild_and_correction_arrival_order() {
    let rows = demo_synthetic_fixture();
    let request = DayRequest {
        date: DEMO_DATE.into(),
        time_zone: DEMO_TIME_ZONE.into(),
    };
    let t = rows[554].received_at_ms;
    let first = CategoryCorrection {
        id: "manual-1".into(),
        observation_id: "synthetic-555".into(),
        category: "learning".into(),
        revision: 1,
        created_at_ms: t,
    };
    let latest = CategoryCorrection {
        id: "manual-2".into(),
        observation_id: "synthetic-555".into(),
        category: "rest".into(),
        revision: 2,
        created_at_ms: t + 1,
    };
    let rules = [CategoryRule {
        app_id: "synthetic:browser".into(),
        category: "work".into(),
    }];
    let day = build_report(
        &request,
        &rows,
        &[latest.clone(), first.clone()],
        &rules,
        42,
    )
    .unwrap();
    let fixed = day
        .intervals
        .iter()
        .find(|r| r.id == "synthetic-555")
        .unwrap();
    assert_eq!(fixed.category, "rest");
    assert_eq!(fixed.correction_revision, 2);
    assert!(fixed.corrected);
    assert_eq!(day.revision, 42);
    assert_eq!(
        build_report(&request, &rows, &[first, latest], &rules, 42).unwrap(),
        day
    );
    assert_eq!(rows[554].category, "unclassified");
}
