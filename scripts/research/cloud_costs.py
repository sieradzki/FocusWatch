#!/usr/bin/env python3
"""Offline, deterministic sensitivity model. Not a capacity or performance forecast.

Run from any directory: python scripts/research/cloud_costs.py [--input PATH]
All assumptions and frozen public prices live in the adjacent research input JSON.
Only the selected output file is written. No cloud SDK, network or credentials.
"""

import argparse
import copy
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "docs/research/2026-09/cloud-cost-inputs.json"
DEFAULT_OUTPUT = ROOT / "docs/research/2026-09/cloud-cost-results.json"
GIB = 2**30
GB = 10**9


def over(quantity, included):
    return max(0, quantity - included)


def tier_cost(quantity, tiers):
    total = previous = 0
    for end, rate in tiers:
        stop = quantity if end is None else min(quantity, end)
        total += max(0, stop - previous) * rate
        previous = stop
        if stop >= quantity:
            break
    return total


def volumes(a, users, privacy):
    days = a["month_days"]
    daily_events = a["observations_user_day"]
    history_days = a["history_years"] * 365
    ingest = users * a["active_device_equivalents"] * a["active_hours_day"] * 3600 / a["batch_seconds"] * days
    reports = users * a["report_requests_user_day"] * days
    downloads = ingest * a["download_requests_per_ingest"]
    events = users * daily_events * days
    wire = events * a["wire_bytes_event"]
    hot = users * daily_events * a["hot_days"] * a["hot_physical_bytes_event"]
    is_blind = privacy.startswith("blind_sync")
    if is_blind:
        hot = users * a["control_db_bytes_user"]
        if privacy == "blind_sync_pg_staging":
            hot += users * daily_events * a["blind_transient_days"] * a["hot_physical_bytes_event"]
    archive_days = history_days if is_blind else max(0, history_days - a["hot_days"])
    archive = users * daily_events * archive_days * a["archive_bytes_event"]
    # One archived bundle per active device per day. Blind sync adds transient
    # minute-sized objects: one PUT and one GET per other registered device.
    archive_puts = users * a["active_device_equivalents"] * days
    transient_puts = ingest if privacy == "blind_sync" else 0
    transient_gets = transient_puts * (a["registered_devices"] - 1)
    transient_bytes = (users * daily_events * a["blind_transient_days"] * a["archive_bytes_event"] if privacy == "blind_sync" else 0)
    reads = users * a["archive_gets_user_month"] + transient_gets
    egress = (
        wire * a["sync_download_copies"]
        + reports * a["report_response_bytes"]
        + ingest * a["ack_response_bytes"]
        + archive * a["archive_export_fraction_month"]
    )
    requests = ingest + reports + downloads
    cpu_seconds = requests * a["cpu_ms_request"] / 1000
    # Amortized billed instance-time is a sensitivity parameter, not measured
    # latency. At low traffic the caller must use isolated-request billing.
    effective_ms = (math.ceil(a["wall_ms_request"] / 100) * 100 if users == 1
                    else a["wall_ms_request"] / a["effective_request_overlap"])
    billed_seconds = max(requests * effective_ms / 1000, cpu_seconds / a["target_cpu_utilization"])
    return {
        "users": users, "privacy": privacy, "events_month": events,
        "events_hot": users * daily_events * a["hot_days"],
        "events_five_years": users * daily_events * history_days,
        "logical_payload_bytes_month": events * a["payload_bytes_event"],
        "wire_bytes_month": wire, "ingest_requests_month": ingest,
        "report_requests_month": reports, "requests_month": requests,
        "download_requests_month": downloads,
        "hot_physical_bytes": hot, "backup_retained_bytes": hot * a["backup_storage_multiple"],
        "archive_bytes": archive, "transient_object_bytes": transient_bytes,
        "object_puts_month": archive_puts + transient_puts,
        "object_gets_month": reads, "internet_egress_bytes_month": egress,
        "cpu_seconds_assumed": cpu_seconds,
        "container_billed_seconds_assumed": billed_seconds,
        "event_rate_average_second": users * daily_events / 86400,
        "event_rate_active_window_second": users * daily_events / (a["active_hours_day"] * 3600),
    }


def estimate(data, users, profile, privacy):
    a, p = data["assumptions"], data["prices"]
    v = volumes(a, users, privacy)
    hours = a["month_days"] * 24
    ha = profile == "commercial_reference"
    hot = v["hot_physical_bytes"]
    backup = v["backup_retained_bytes"]
    obj = v["archive_bytes"] + v["transient_object_bytes"]
    put, get = v["object_puts_month"], v["object_gets_month"]
    req, cpu, billed = v["requests_month"], v["cpu_seconds_assumed"], v["container_billed_seconds_assumed"]
    egress = v["internet_egress_bytes_month"]
    euro_per_usd = 1 / data["fx"]["usd_per_eur"]
    rows = []

    def add(name, currency, parts, caveats=(), extra_eur=0, capacity="unvalidated"):
        native = sum(parts.values())
        eur = native * (euro_per_usd if currency == "USD" else 1) + extra_eur
        rows.append({
            "provider": name, "profile": profile, "privacy": privacy, "users": users,
            "currency": currency, "components_native": parts, "subtotal_native": native,
            "external_postgres_eur": extra_eur,
            "subtotal_eur_at_reference_fx": eur,
            "scope": "PARTIAL infrastructure reference; not an invoice or capacity guarantee",
            "capacity_status": capacity, "caveats": list(caveats),
            "with_illustrative_ops_eur": {str(h): eur + h * a["ops_eur_hour"] for h in a["ops_hours_sensitivity"]},
        })

    q = p["gcp"]
    disk_gib = math.ceil(max(q["minimum_disk_gib"], hot / GIB * a["disk_headroom_factor"]))
    db_hour = q["ha_db_hour"] if ha else q["dev_db_hour"]
    add("gcp", "USD", {
        "api_cpu": over(billed, q["free_cpu_seconds"]) * q["cpu_second"],
        "api_memory": over(billed * a["container_memory_gib"], q["free_memory_gib_seconds"]) * q["memory_gib_second"],
        "api_requests": over(req, q["free_requests"]) / 1e6 * q["requests_million"],
        "postgres_compute": hours * db_hour,
        "postgres_storage": disk_gib * (q["ha_disk_gib_month"] if ha else q["disk_gib_month"]),
        "postgres_backups": backup / GIB * q["backup_gib_month"],
        "object_storage": obj / GIB * q["object_gib_month"],
        "object_operations": put / 1000 * q["put_thousand"] + get / 1000 * q["get_thousand"],
        "internet_egress": tier_cost(egress / GIB, q["egress_tiers_gib"]),
    }, ["Cloud SQL Enterprise regional HA in commercial profile; shared-core dev has no Cloud SQL SLA", "No GCS US-only free storage allocation applied to Belgium", "Additional cross-zone/private networking, logs and archival job CPU omitted"])

    q = p["scaleway"]
    disk_gb = math.ceil(max(q["minimum_disk_gb"], hot / GB * a["disk_headroom_factor"]))
    scw_db = {
        "postgres_compute": hours * (q["commercial_primary_hour"] + q["commercial_standby_hour"] if ha else q["dev_db_hour"]),
        "postgres_storage": disk_gb * q["disk_gb_month"] * (a["scaleway_ha_storage_copies"] if ha else 1),
        "postgres_backups": backup / GB * q["backup_gb_month"],
    }
    add("scaleway", "EUR", {
        "api_cpu": over(billed, q["free_cpu_seconds"]) * q["cpu_second"],
        "api_memory": over(billed * a["container_memory_gib"], q["free_memory_gb_seconds"]) * q["memory_gb_second"],
        **scw_db,
        "object_storage": math.ceil(obj / GB) * q["object_gb_month"],
        "object_operations": 0,
        "object_egress": over(v["archive_bytes"] * a["archive_export_fraction_month"] / GB, q["free_object_egress_gb"]) * q["object_egress_gb"],
    }, ["Commercial HA is same data center / separate racks, NOT automatic cross-AZ failover", "Two billed HA storage copies assumed; verify exact volume invoice semantics", "Container ingress/egress is free per official FAQ; external PostgreSQL egress remains unpriced"])

    q = p["aws"]
    disk_gib = math.ceil(max(q["minimum_disk_gib"], hot / GIB * a["disk_headroom_factor"]))
    floor_tasks = 2 if ha else 1
    active_hours = a["month_days"] * a["active_hours_day"]
    idle_hours = hours - active_hours
    task_hours = (idle_hours * floor_tasks
                  + max(active_hours * floor_tasks, cpu / 3600 / a["target_cpu_utilization"]))
    # 1 vCPU/2 GiB Linux x86 tasks. Demand term is an assumed CPU budget;
    # peak autoscaling headroom and database capacity require load tests.
    lcu_hours = max(req * a["new_connections_per_request"] / 90000, (v["wire_bytes_month"] + egress) / GB)
    add("aws", "USD", {
        "fargate": task_hours * (q["cpu_hour"] + 2 * q["memory_gib_hour"]),
        "load_balancer": hours * q["alb_hour"] + lcu_hours * q["lcu_hour"],
        "public_ipv4": (task_hours + 2 * hours) * q["ipv4_hour"],
        "postgres_compute": hours * (q["ha_db_hour"] if ha else q["dev_db_hour"]),
        "postgres_storage": disk_gib * (q["ha_disk_gib_month"] if ha else q["disk_gib_month"]),
        "postgres_backups": over(backup / GIB, disk_gib) * q["backup_gib_month"],
        "object_storage": tier_cost(obj / GIB, q["object_storage_tiers_gib"]),
        "object_operations": put * q["put"] + get * q["get"],
        "internet_egress": tier_cost(over(egress / GIB, q["free_egress_gib"]), q["egress_tiers_gib"]),
    }, ["RDS Multi-AZ one standby in commercial profile", "Fargate public-subnet design behind ALB, private DB, no NAT; adding NAT/private endpoints changes cost", "ALB LCU estimate covers bytes/new connections only; active connections/rules/TLS sizes need measurement", "Inter-AZ traffic, logs, gp3 extra IOPS/throughput and archival job CPU omitted"])

    q = p["cloudflare"]
    r2 = {
        "r2_storage": math.ceil(over(obj / GB, q["r2_free_gb"])) * q["r2_gb_month"],
        "r2_operations": math.ceil(over(put, q["r2_free_put"]) / 1e6) * q["r2_put_million"] + math.ceil(over(get, q["r2_free_get"]) / 1e6) * q["r2_get_million"],
    }
    worker = {
        "workers_plan": q["base_month"],
        "workers_requests": over(req, q["free_requests"]) / 1e6 * q["requests_million"],
        "workers_cpu": over(cpu * 1000, q["free_cpu_ms"]) / 1e6 * q["cpu_ms_million"],
    }
    external_db = sum(scw_db.values())
    add("cloudflare_workers_scw_pg", "USD", {**worker, **r2}, ["External PostgreSQL is the SAME Scaleway profile used above, billed separately in EUR", "Global Workers execution is not an EU compute-residency guarantee; R2 EU jurisdiction is separate", "PG network, Hyperdrive compatibility/ACLs/latency and archive job compute need validation", "Rust here means workers-rs/Wasm, not a native Axum container"], external_db)
    floor_instances = 2 if ha else 1
    active_hours = a["month_days"] * a["active_hours_day"]
    sleep_tail_hours = a["month_days"] * a["cf_sleep_tail_minutes_day"] / 60
    # Basic instance = 0.25 vCPU, 1 GiB RAM, 4 GB ephemeral disk.
    instance_seconds = (floor_instances * sleep_tail_hours * 3600
                        + max(floor_instances * active_hours * 3600, cpu / (0.25 * a["target_cpu_utilization"])))
    front_worker = {**worker, "workers_cpu": over(req * a["front_worker_cpu_ms"], q["free_cpu_ms"]) / 1e6 * q["cpu_ms_million"]}
    add("cloudflare_containers_scw_pg", "USD", {
        **front_worker, **r2,
        "container_cpu": over(cpu, q["container_free_cpu_seconds"]) * q["container_cpu_second"],
        "container_memory": over(instance_seconds, q["container_free_memory_gib_seconds"]) * q["container_memory_gib_second"],
        "container_disk": over(instance_seconds * 4, q["container_free_disk_gb_seconds"]) * q["container_disk_gb_second"],
        "container_egress": over((egress + v["wire_bytes_month"]) / GB, q["container_free_egress_gb"]) * q["container_egress_gb"],
        "durable_object_requests": math.ceil(over(req, q["do_free_requests"]) / 1e6) * q["do_requests_million"],
        "durable_object_duration": math.ceil(over(instance_seconds * 0.128, q["do_free_gb_seconds"]) / 1e6) * q["do_duration_million_gb_seconds"],
    }, ["No built-in stateless autoscaling; modeled scaling requires implementation", "DO duration assumes controller stays resident while container is up; actual hibernation can reduce it", "External PostgreSQL includes only same-DC HA, not cross-AZ", "Ephemeral container disk is NOT the database volume; object downloads assumed through API"], external_db)

    q = p["hetzner"]
    # Intentionally a VM reference only. Do not invent a €/GB rate or assume
    # that this machine/its included disk serves all four user populations.
    vm = q["commercial_vm_month"] * 2 if ha else q["dev_vm_month"]
    obj_gb = (obj + backup) / GB
    add("hetzner_vm_reference", "EUR", {
        "vm": vm, "vm_backups": vm * q["backup_fraction"],
        "ipv4": q["ipv4_month"] * (2 if ha else 1),
        "object_storage_with_db_backup": q["object_base_month"] + over(obj_gb, q["object_included_gb"]) / 1000 * hours * q["object_extra_tb_hour"],
    }, ["VM reference only; additional DB volume, LB/quorum and failover engineering excluded", "Two VMs DO NOT constitute a validated HA PostgreSQL deployment", "No managed PostgreSQL is included; ops/restoration/patching are operator responsibilities", "VM backup does not cover attached volumes; logical database backup modeled separately in object storage"], capacity="NOT sized; extra database disk unpriced")
    return {"volume": v, "rows": rows}


def realtime_estimates(data):
    """Persistent-HTTP billing floors sharing the bulk API's compute/free pool.

    Connection limits are configuration ceilings, NOT measured RAM/CPU capacity.
    Uses the same 8h window for all clients; omits scale-down tail, fanout traffic,
    relay/storage/pubsub, reconnect CPU and spare slots for concurrent API calls.
    """
    a, prices = data["assumptions"], data["prices"]
    results = []
    for users in data["users"]:
        base = estimate(data, users, "commercial_reference", "cloud_readable")
        v = base["volume"]
        connections = users * a["active_device_equivalents"]
        active_seconds = a["month_days"] * a["active_hours_day"] * 3600
        for provider, capacity in [("gcp", 100), ("gcp", 250), ("gcp", 1000), ("scaleway", 80)]:
            q = prices[provider]
            instances = math.ceil(connections / capacity)
            floor_seconds = instances * active_seconds
            billed = max(floor_seconds, v["container_billed_seconds_assumed"])
            row = next(r for r in base["rows"] if r["provider"] == provider)
            if provider == "gcp":
                # One instance-based billing pool; do not charge API CPU twice
                # or also deduct the request-based free pool from this service.
                cpu_cost = over(billed, q["instance_free_cpu_seconds"]) * q["instance_cpu_second"]
                mem_cost = over(billed * a["container_memory_gib"], q["instance_free_memory_gib_seconds"]) * q["instance_memory_gib_second"]
                floor_gross = floor_seconds * (q["instance_cpu_second"] + a["container_memory_gib"] * q["instance_memory_gib_second"])
            else:
                cpu_cost = over(billed, q["free_cpu_seconds"]) * q["cpu_second"]
                mem_cost = over(billed * a["container_memory_gib"], q["free_memory_gb_seconds"]) * q["memory_gb_second"]
                floor_gross = floor_seconds * (q["cpu_second"] + a["container_memory_gib"] * q["memory_gb_second"])
            api_baseline = sum(value for key, value in row["components_native"].items() if key.startswith("api_"))
            native = row["subtotal_native"] - api_baseline + cpu_cost + mem_cost
            factor = 1 / data["fx"]["usd_per_eur"] if row["currency"] == "USD" else 1
            results.append({
                "users": users, "provider": provider, "currency": row["currency"],
                "connections": connections, "assumed_connections_per_instance": capacity,
                "minimum_instances_during_active_window": instances,
                "fits_documented_single_service_scale_limit": not (provider == "scaleway" and instances > 200),
                "connection_floor_gross_native": floor_gross,
                "shared_api_plus_connections_compute_native": cpu_cost + mem_cost,
                "partial_infrastructure_with_connections_eur": native * factor,
                "scope": "Optimistic floor, not a measured connection capacity or full realtime system cost; 1000/80 slots leave no API concurrency margin at saturation",
            })
    return results


def verify_arithmetic(data, base, realtime):
    """Independent dimensional/ledger checks for the spending comparison."""
    a = data["assumptions"]
    v = volumes(a, 1, "cloud_readable")
    # Fixed reference checks remain valid when a caller overrides event density.
    reference = {**a, "active_device_equivalents": 2, "active_hours_day": 8,
                 "batch_seconds": 60, "month_days": 30,
                 "observations_user_day": 3840, "hot_days": 90}
    ref = volumes(reference, 1, "cloud_readable")
    assert 2 * 8 * 3600 / 30 * 2 == 3840
    assert ref["ingest_requests_month"] == 28800
    assert ref["events_hot"] == 345600
    assert v["ingest_requests_month"] == (a["active_device_equivalents"] * a["active_hours_day"] * 3600 / a["batch_seconds"] * a["month_days"])
    assert v["events_hot"] == a["observations_user_day"] * a["hot_days"]
    assert v["hot_physical_bytes"] == v["events_hot"] * a["hot_physical_bytes_event"]
    assert v["requests_month"] == v["ingest_requests_month"] + v["report_requests_month"] + v["download_requests_month"]
    for result in base:
        for row in result["rows"]:
            assert all(math.isfinite(x) and x >= 0 for x in row["components_native"].values())
            assert math.isclose(row["subtotal_native"], sum(row["components_native"].values()))
            rate = 1 / data["fx"]["usd_per_eur"] if row["currency"] == "USD" else 1
            assert math.isclose(row["subtotal_eur_at_reference_fx"], row["subtotal_native"] * rate + row["external_postgres_eur"])
    # Regression: 8h/day of load cannot spend the other16h of minimum task
    # uptime as processing credit. 10k base users need demand + idle floor.
    v = volumes(a, 10000, "cloud_readable")
    aws = next(r for r in estimate(data, 10000, "commercial_reference", "cloud_readable")["rows"] if r["provider"] == "aws")
    billed_hours = aws["components_native"]["fargate"] / (data["prices"]["aws"]["cpu_hour"] + 2 * data["prices"]["aws"]["memory_gib_hour"])
    idle_floor = a["month_days"] * (24 - a["active_hours_day"]) * 2
    assert billed_hours >= idle_floor + v["cpu_seconds_assumed"] / 3600 / a["target_cpu_utilization"]
    for row in realtime:
        assert row["minimum_instances_during_active_window"] * row["assumed_connections_per_instance"] >= row["connections"]
        assert row["shared_api_plus_connections_compute_native"] >= 0
        assert row["partial_infrastructure_with_connections_eur"] >= 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    base = [estimate(data, n, profile, privacy) for privacy in ["cloud_readable", "blind_sync", "blind_sync_pg_staging"] for profile in ["development_floor", "commercial_reference"] for n in data["users"]]
    realtime = realtime_estimates(data)
    verify_arithmetic(data, base, realtime)
    sensitivity = []
    for key, vals in data["sensitivity"].items():
        for val in vals:
            changed = copy.deepcopy(data)
            changed["assumptions"][key] = val
            result = estimate(changed, 1000, "commercial_reference", "cloud_readable")
            sensitivity.append({"parameter": key, "value": val, "users": 1000, "costs_eur": {r["provider"]: r["subtotal_eur_at_reference_fx"] for r in result["rows"]}})
    out = {"price_date": data["price_date"], "fx": data["fx"], "assumptions": data["assumptions"], "base": base, "sensitivity_1000_users": sensitivity,
           "realtime_persistent_connections": realtime,
           "network_addon_sensitivity": [{"users": n, "scope": "Illustrative unpriced network path; NOT Scaleway Container API egress, which is free", "egress_eur_per_gb": rate, "additional_eur": volumes(data["assumptions"], n, "cloud_readable")["internet_egress_bytes_month"] / GB * rate} for n in data["users"] for rate in [0, 0.01, 0.09]],
           "excluded_costs": data["excluded_costs"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {args.output}")
    print("PARTIAL monthly infrastructure EUR, explicit reference FX; no capacity guarantee")
    for result in base:
        if result["volume"]["privacy"] == "cloud_readable" and result["rows"][0]["profile"] == "commercial_reference":
            print(result["volume"]["users"], {r["provider"]: round(r["subtotal_eur_at_reference_fx"], 2) for r in result["rows"]})


if __name__ == "__main__":
    main()
