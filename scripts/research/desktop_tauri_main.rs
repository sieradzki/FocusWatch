#[tauri::command]
fn report(payload: String) {
    println!("DESKTOP_PROBE {}", payload);
}
#[tauri::command]
fn probe_config() -> usize {
    std::env::var("PROBE_SEGMENTS").ok().and_then(|v| v.parse().ok())
        .filter(|v| (1..=100000).contains(v)).unwrap_or(10000)
}
fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![report, probe_config])
        .run(tauri::generate_context!())
        .expect("synthetic desktop probe failed");
}
