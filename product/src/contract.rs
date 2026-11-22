//! Local report protocol. Exactly one length-prefixed JSON document per connection.
use serde::{Deserialize, Serialize};
use std::io;
use tokio::io::{AsyncRead, AsyncReadExt, AsyncWrite, AsyncWriteExt};

pub const VERSION: u8 = 1;
pub const MAX_FRAME: usize = 4 * 1024 * 1024;
const MAX_REQUEST: usize = 4096;

#[derive(Debug, Deserialize)]
#[serde(tag = "command", rename_all = "snake_case", deny_unknown_fields)]
pub enum Command {
    Report {
        date: String,
        zone: String,
    },
    Correct {
        id: String,
        command_id: String,
        expected_revision: u64,
        category: String,
    },
}

pub fn decode(bytes: &[u8]) -> Result<Command, &'static str> {
    // Check the envelope before interpreting the version-specific command.
    // Deserialize the final command from the remaining fields to reject unknown arguments.
    let mut fields: serde_json::Map<String, serde_json::Value> =
        serde_json::from_slice(bytes).map_err(|_| "invalid_request")?;
    if fields.remove("version").and_then(|v| v.as_u64()) != Some(u64::from(VERSION)) {
        return Err("unsupported_version");
    }
    if fields
        .remove("role")
        .and_then(|v| v.as_str().map(str::to_owned))
        .as_deref()
        != Some("report")
    {
        return Err("invalid_role");
    }
    let cmd: Command = serde_json::from_value(fields.into()).map_err(|_| "invalid_request")?;
    let valid = match &cmd {
        Command::Report { date, zone } => date.len() == 10 && (1..=100).contains(&zone.len()),
        Command::Correct {
            id,
            category,
            command_id,
            ..
        } => [(id, 256), (category, 128), (command_id, 256)]
            .into_iter()
            .all(|(s, limit)| {
                !s.trim().is_empty() && s.len() <= limit && !s.chars().any(char::is_control)
            }),
    };
    if valid {
        Ok(cmd)
    } else {
        Err("invalid_request")
    }
}

pub async fn read_request(r: &mut (impl AsyncRead + Unpin)) -> io::Result<Vec<u8>> {
    let size = r.read_u32_le().await? as usize;
    if !(1..=MAX_REQUEST).contains(&size) {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "invalid frame size",
        ));
    }
    let mut payload = vec![0; size];
    r.read_exact(&mut payload).await?;
    Ok(payload)
}

pub async fn respond<W: AsyncWrite + Unpin, T: Serialize>(
    w: &mut W,
    result: Result<T, &'static str>,
) -> io::Result<()> {
    #[derive(Serialize)]
    struct Success<T> {
        version: u8,
        ok: bool,
        data: T,
    }
    let error = |tag| {
        serde_json::to_vec(&serde_json::json!({"version": VERSION, "ok": false, "error": tag}))
    };
    let mut bytes = match result {
        Ok(data) => serde_json::to_vec(&Success {
            version: VERSION,
            ok: true,
            data,
        }),
        Err(tag) => error(tag),
    }?;
    if bytes.len() > MAX_FRAME {
        bytes = error("report_too_large")?;
    }
    w.write_u32_le(bytes.len() as u32).await?;
    w.write_all(&bytes).await?;
    w.flush().await
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn version_role_and_command_allowlist() {
        for (request, expected) in [
            (r#"{"version":2}"#, "unsupported_version"),
            (r#"{"version":1,"role":"watcher"}"#, "invalid_role"),
            (
                r#"{"version":1,"role":"report","command":"sql"}"#,
                "invalid_request",
            ),
            (
                r#"{"version":1,"role":"report","command":"report","date":"2026-11-17","zone":"UTC","path":"other"}"#,
                "invalid_request",
            ),
        ] {
            assert_eq!(decode(request.as_bytes()).unwrap_err(), expected);
        }
    }

    #[tokio::test]
    async fn rejects_zero_oversize_and_truncated_frames() {
        for frame in [
            vec![0, 0, 0, 0],
            vec![255, 255, 255, 255],
            vec![2, 0, 0, 0, 42],
            vec![1, 0],
        ] {
            assert!(read_request(&mut frame.as_slice()).await.is_err());
        }
        assert_eq!(
            read_request(&mut &[2, 0, 0, 0, 42, 43][..]).await.unwrap(),
            &[42, 43]
        );
    }
}
