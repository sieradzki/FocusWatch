"""Regenerate the shared, artificial 24-hour input used by the paired probes."""

from pathlib import Path


def build_fixture() -> bytes:
    hourly_pattern = [
        (12, "editor", "work"),
        (16, "browser", "unclassified"),
        (23, "reader", "learning"),
        (9, "player", "leisure"),
    ]
    rows = ["id\tstart_s\tend_s\tapp\tcategory"]
    for hour in range(24):
        minute = hour * 60
        for duration, app, category in hourly_pattern:
            for _ in range(duration):
                rows.append(f"{minute + 1}\t{60 * minute}\t{60 * (minute + 1)}\t{app}\t{category}")
                minute += 1
    assert rows[555] == "555\t33240\t33300\tbrowser\tunclassified"
    return ("\n".join(rows) + "\n").encode("ascii")


if __name__ == "__main__":
    Path(__file__).with_name("fixture.tsv").write_bytes(build_fixture())
