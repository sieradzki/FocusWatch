//! Synthetic lifecycle probe only: no native capture, database, autostart or privileges.
//! Linux Unix socket models a UI-independent process; this is NOT production IPC.
use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::os::unix::fs::PermissionsExt;
use std::os::unix::net::UnixListener;
use std::path::PathBuf;
use std::time::{Duration, Instant};

fn main() -> std::io::Result<()> {
    let directory = PathBuf::from(std::env::args().nth(1).expect("private synthetic directory"));
    let socket = directory.join("collector.sock");
    let journal_path = directory.join("synthetic-sequence.log");
    let listener = UnixListener::bind(&socket)?;
    fs::set_permissions(&socket, fs::Permissions::from_mode(0o600))?;
    listener.set_nonblocking(true)?;
    let mut journal = OpenOptions::new().create(true).read(true).append(true).open(journal_path)?;
    let mut existing = String::new();
    journal.read_to_string(&mut existing)?;
    let mut sequence = 0_u64;
    let mut valid_length = 0_u64;
    for record in existing.split_inclusive('\n') {
        if !record.ends_with('\n') { break; }
        let value: u64 = record.trim().parse().expect("synthetic journal record must be numeric");
        assert_eq!(value, sequence + 1, "non-contiguous synthetic journal");
        sequence = value;
        valid_length += record.len() as u64;
    }
    journal.set_len(valid_length)?;
    let mut next_event = Instant::now();
    loop {
        if Instant::now() >= next_event {
            sequence += 1;
            writeln!(journal, "{}", sequence)?;
            journal.sync_data()?;
            next_event = Instant::now() + Duration::from_millis(100);
        }
        if let Ok((mut stream, _)) = listener.accept() {
            stream.set_read_timeout(Some(Duration::from_millis(20)))?;
            stream.set_write_timeout(Some(Duration::from_millis(20)))?;
            let mut input = [0_u8; 64];
            if let Ok(length) = stream.read(&mut input) {
                if &input[..length] == b"snapshot\n" {
                    let _ = writeln!(stream,
                        "{{\"protocol\":1,\"sequence\":{},\"foreground\":\"synthetic-editor\",\"media_playing\":true}}", sequence);
                } else {
                    let _ = stream.write_all(b"{\"error\":\"unsupported_or_incomplete_request\"}\n");
                }
            }
        }
        std::thread::sleep(Duration::from_millis(2));
    }
}
