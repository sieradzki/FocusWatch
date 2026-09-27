//! Synthetic bounded latest-state relay. No TLS/auth/PG/real device collection.
use axum::{extract::{ws::{Message, WebSocket, WebSocketUpgrade}, Path, State}, response::IntoResponse, routing::get, Json, Router};
use futures_util::{SinkExt, StreamExt};
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, sync::{Arc, Mutex, atomic::{AtomicU64, Ordering}}, time::Duration};
use tokio::sync::watch;

#[derive(Clone, Deserialize, Serialize)]
struct Context { account: u32, device: u8, seq: u64, stamp_ns: String, payload: String }
#[derive(Default)]
struct Account { latest: HashMap<u8, Context>, peers: HashMap<u8, watch::Sender<Option<Arc<str>>>> }
#[derive(Default)]
struct Relay {
    accounts: Mutex<HashMap<u32, Account>>, connected: AtomicU64,
    accepted: AtomicU64, delivered: AtomicU64, rejected: AtomicU64,
}
async fn upgrade(ws: WebSocketUpgrade, Path((account, device)): Path<(u32,u8)>, State(relay): State<Arc<Relay>>) -> impl IntoResponse {
    // Explicit small buffers suit <=2KiB synthetic state; not generic streaming.
    ws.read_buffer_size(4096).write_buffer_size(4096).max_write_buffer_size(16384)
        .max_message_size(2048).max_frame_size(2048)
        .on_upgrade(move |socket| connection(socket, relay, account, device))
}
async fn connection(socket: WebSocket, relay: Arc<Relay>, account: u32, device: u8) {
    if device > 1 { return; }
    let (tx, mut rx) = watch::channel(None);
    let snapshot = {
        let mut accounts = relay.accounts.lock().unwrap();
        let room = accounts.entry(account).or_default();
        let initial = room.latest.get(&(device ^ 1)).map(|v| serde_json::to_string(v).unwrap());
        room.peers.insert(device, tx);
        initial
    };
    relay.connected.fetch_add(1, Ordering::Relaxed);
    let (mut sink, mut stream) = socket.split();
    if let Some(value) = snapshot { let _ = sink.send(Message::Text(value.into())).await; }
    loop {
        tokio::select! {
            incoming = stream.next() => {
                match incoming {
                    Some(Ok(Message::Text(text))) => {
                        let Ok(value) = serde_json::from_str::<Context>(&text) else {
                            relay.rejected.fetch_add(1, Ordering::Relaxed); continue;
                        };
                        if value.account != account || value.device != device || value.payload.len() > 1024 {
                            relay.rejected.fetch_add(1, Ordering::Relaxed); continue;
                        }
                        let mut accounts = relay.accounts.lock().unwrap();
                        let room = accounts.get_mut(&account).unwrap();
                        if room.latest.get(&device).is_some_and(|prior| value.seq <= prior.seq) {
                            relay.rejected.fetch_add(1, Ordering::Relaxed); continue;
                        }
                        room.latest.insert(device, value);
                        relay.accepted.fetch_add(1, Ordering::Relaxed);
                        if let Some(peer) = room.peers.get(&(device ^ 1)) {
                            // One latest value per recipient. Slow clients may skip intermediates.
                            let _ = peer.send(Some(Arc::<str>::from(text.as_str())));
                        }
                    }
                    Some(Ok(Message::Close(_))) | Some(Err(_)) | None => break,
                    _ => {}
                }
            }
            changed = rx.changed() => {
                if changed.is_err() { break; }
                let value = rx.borrow_and_update().clone();
                if let Some(text) = value {
                    match tokio::time::timeout(Duration::from_secs(2), sink.send(Message::Text(text.to_string().into()))).await {
                        Ok(Ok(())) => { relay.delivered.fetch_add(1, Ordering::Relaxed); },
                        _ => break,
                    }
                }
            }
        }
    }
    relay.connected.fetch_sub(1, Ordering::Relaxed);
    // Probe forbids concurrent replacement connections for the same device.
    if let Some(room) = relay.accounts.lock().unwrap().get_mut(&account) { room.peers.remove(&device); }
}
async fn metrics(State(relay): State<Arc<Relay>>) -> Json<serde_json::Value> {
    let accounts = relay.accounts.lock().unwrap();
    Json(serde_json::json!({
        "connections": relay.connected.load(Ordering::Relaxed),
        "accounts": accounts.len(), "latest_records": accounts.values().map(|a| a.latest.len()).sum::<usize>(),
        "accepted": relay.accepted.load(Ordering::Relaxed), "delivered": relay.delivered.load(Ordering::Relaxed),
        "rejected": relay.rejected.load(Ordering::Relaxed)
    }))
}
#[tokio::main(flavor="multi_thread", worker_threads=1)]
async fn main() {
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    println!("READY {}", listener.local_addr().unwrap().port());
    let app = Router::new().route("/ws/{account}/{device}", get(upgrade)).route("/metrics", get(metrics))
        .with_state(Arc::new(Relay::default()));
    axum::serve(listener, app).await.unwrap();
}
