#[path = "focuswatch-agent/state.rs"]
mod state;
#[path = "focuswatch-agent/transport.rs"]
mod transport;

use focuswatch_core::{
    contract::{self, Command},
    domain::{CorrectionRequest, DayRequest},
    storage::{Storage, StorageError},
};
use serde_json::Value;
use std::{
    cell::RefCell,
    io::{self, Write},
    path::PathBuf,
    rc::Rc,
    time::{Duration, SystemTime, UNIX_EPOCH},
};
use tokio::{
    io::{AsyncRead, AsyncWrite},
    task::{JoinSet, LocalSet},
};

fn error_code(error: StorageError) -> &'static str {
    match error {
        StorageError::CommandConflict { .. } | StorageError::RevisionConflict { .. } => "conflict",
        StorageError::ObservationNotFound { .. } => "not_found",
        StorageError::InvalidInput(_) | StorageError::Domain(_) => "invalid_request",
        StorageError::ReportTooLarge { .. } | StorageError::QueryBudgetExceeded => {
            "report_too_large"
        }
        _ => "storage_error",
    }
}

fn execute(storage: &mut Storage, cmd: Command) -> Result<Value, &'static str> {
    let value = match cmd {
        Command::Report { date, zone } => {
            let request = DayRequest {
                date,
                time_zone: zone,
            };
            let rules = focuswatch_core::domain::default_category_rules();
            serde_json::to_value(storage.day_report(&request, &rules).map_err(error_code)?)
        }
        Command::Correct {
            id,
            category,
            command_id,
            expected_revision,
        } => {
            let now = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .map_err(|_| "storage_error")?;
            let created_at_ms = i64::try_from(now.as_millis()).map_err(|_| "storage_error")?;
            let request = CorrectionRequest {
                observation_id: id,
                command_id,
                category,
                expected_revision,
            };
            serde_json::to_value(
                storage
                    .apply_correction(&request, created_at_ms)
                    .map_err(error_code)?,
            )
        }
    };
    value.map_err(|_| "storage_error")
}

async fn connection<S: AsyncRead + AsyncWrite + Unpin>(
    mut stream: S,
    db: Rc<RefCell<Storage>>,
) -> io::Result<()> {
    let bytes = contract::read_request(&mut stream).await?;
    let result =
        contract::decode(&bytes).and_then(|command| execute(&mut db.borrow_mut(), command));
    contract::respond(&mut stream, result).await
}

async fn run() -> Result<(), Box<dyn std::error::Error>> {
    let mut state_path = None;
    let mut endpoint = None;
    let mut args = std::env::args_os().skip(1);
    while let Some(flag) = args.next() {
        if flag == "--state" && state_path.is_none() {
            state_path = Some(PathBuf::from(args.next().ok_or("missing state path")?));
        } else if flag == "--endpoint" && endpoint.is_none() {
            endpoint = Some(
                args.next()
                    .and_then(|s| s.into_string().ok())
                    .ok_or("missing UTF-8 endpoint")?,
            );
        } else {
            return Err("usage: focuswatch-agent --state <absolute synthetic directory> --endpoint <local endpoint>".into());
        }
    }
    let endpoint = endpoint.ok_or("missing --endpoint")?;
    let state = state::State::open(&state_path.ok_or("missing --state")?)?;
    let mut listener = transport::Listener::bind(&endpoint, &state.path)?;
    let mut storage = Storage::open(state.path.join("synthetic.sqlite3"))?;
    storage.seed_synthetic_fixture()?;
    let storage = Rc::new(RefCell::new(storage));
    println!("READY");
    io::stdout().flush()?;

    let mut clients = JoinSet::new();
    loop {
        // Backpressure: at most eight bounded requests in flight. Stalled peers expire.
        while clients.try_join_next().is_some() {}
        if clients.len() >= 8 {
            clients.join_next().await;
            continue;
        }
        let stream = listener.accept().await?;
        let db = Rc::clone(&storage);
        clients.spawn_local(async move {
            let _ = tokio::time::timeout(Duration::from_secs(8), connection(stream, db)).await;
        });
    }
}

#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    LocalSet::new().run_until(run()).await
}
