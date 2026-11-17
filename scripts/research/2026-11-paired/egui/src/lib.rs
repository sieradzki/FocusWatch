//! Isolated feasibility probe, not a FocusWatch implementation or a timing benchmark.

use std::collections::BTreeMap;
use egui::{Color32, Rect, Stroke, StrokeKind, Ui, pos2, vec2};

pub const INPUT_LABEL: &str = "Correction category";
pub const APPLY_LABEL: &str = "Apply correction (Ctrl+Enter)";
pub const SELECTED_TEXT: &str = "#555 | 09:14–09:15 | browser | category=learning";

#[derive(Clone, Debug, PartialEq)]
pub struct Observation {
    pub id: u32,
    pub start: u32,
    pub end: u32,
    pub app: String,
    pub category: String,
}

pub struct Report {
    pub rows: Vec<Observation>,
    pub corrections: BTreeMap<u32, String>,
    pub category_text: String,
    pub commits: u32,
    pub selected_rect: Rect,
}

impl Report {
    pub fn synthetic() -> Self {
        let rows = include_str!("../../fixture.tsv").lines().skip(1).map(|line| {
            let f: Vec<_> = line.split('\t').collect();
            assert_eq!(f.len(), 5);
            Observation { id: f[0].parse().unwrap(), start: f[1].parse().unwrap(),
                end: f[2].parse().unwrap(), app: f[3].into(), category: f[4].into() }
        }).collect();
        Self { rows, corrections: BTreeMap::new(), category_text: "learning".into(),
            commits: 0, selected_rect: Rect::NOTHING }
    }

    fn category<'a>(&'a self, row: &'a Observation) -> &'a str {
        self.corrections.get(&row.id).map(String::as_str).unwrap_or(&row.category)
    }

    pub fn category_seconds(&self, category: &str) -> u32 {
        self.rows.iter().filter(|row| self.category(row) == category)
            .map(|row| row.end - row.start).sum()
    }

    pub fn selected_text(&self) -> String {
        let row = self.rows.iter().find(|row| row.id == 555).unwrap();
        format!("#555 | 09:14–09:15 | browser | category={}", self.category(row))
    }

    pub fn show(&mut self, ui: &mut Ui) {
        ui.heading("Synthetic daily activity report");
        ui.label(format!("{} observations | 24 hours | source=foreground", self.rows.len()));
        let apps = ["browser", "editor", "player", "reader"];
        for app in apps {
            let seconds: u32 = self.rows.iter().filter(|row| row.app == app)
                .map(|row| row.end - row.start).sum();
            ui.label(format!("{app}: {seconds} seconds"));
        }
        ui.horizontal(|ui| {
            let label = ui.label(INPUT_LABEL);
            ui.text_edit_singleline(&mut self.category_text).labelled_by(label.id);
            let button = ui.button(APPLY_LABEL);
            let shortcut = ui.input_mut(|input| input.consume_key(egui::Modifiers::CTRL, egui::Key::Enter));
            if button.clicked() || shortcut {
                self.corrections.insert(555, self.category_text.trim().to_owned());
                self.commits += 1;
                ui.ctx().request_repaint();
            }
        });
        ui.label(self.selected_text());
        ui.label(format!("learning_seconds={}", self.category_seconds("learning")));
        ui.label(format!("unclassified_seconds={}", self.category_seconds("unclassified")));
        ui.label("09:00–10:00 | foreground observations, app lanes");
        let (chart, _) = ui.allocate_exact_size(vec2(950.0, 140.0), egui::Sense::hover());
        let colors = [Color32::from_rgb(0x25,0x63,0xeb), Color32::from_rgb(0xdc,0x6b,0x2f),
            Color32::from_rgb(0x16,0x83,0x6a), Color32::from_rgb(0x6b,0x72,0x80)];
        for row in self.rows.iter().filter(|row| row.start >= 32400 && row.start < 36000) {
            let lane = apps.iter().position(|app| *app == row.app).unwrap();
            let rect = Rect::from_min_size(pos2(chart.min.x + 100.0 + (row.start - 32400) as f32 / 60.0 * 14.0,
                chart.min.y + 12.0 + lane as f32 * 30.0), vec2(13.0, 20.0));
            let fill = if self.category(row) == "learning" { Color32::from_rgb(0x8b,0x3f,0xba) } else { colors[lane] };
            let stroke = if row.id == 555 { Stroke::new(2.0, Color32::BLACK) } else { Stroke::NONE };
            ui.painter().rect(rect, 0.0, fill, stroke, StrokeKind::Inside);
            if row.id == 555 { self.selected_rect = rect; }
        }
        for row in self.rows.iter().filter(|row| (551..=560).contains(&row.id)) {
            ui.label(format!("#{} | {}–{} | {} | {}", row.id, row.start, row.end, row.app, self.category(row)));
        }
    }
}
