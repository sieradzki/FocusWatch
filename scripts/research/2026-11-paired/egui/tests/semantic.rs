use egui::{Color32, Key, Modifiers, Rect, accesskit::Role, epaint::Shape};
use egui_kittest::{Harness, kittest::Queryable};
use focuswatch_egui_kittest_probe::{Report, INPUT_LABEL, APPLY_LABEL, SELECTED_TEXT};

// Inspect actual egui paint commands, not just the model's intended color.
fn selected_paint(shapes: &[egui::epaint::ClippedShape], rect: Rect) -> (Color32, f32) {
    fn find(shape: &Shape, rect: Rect) -> Option<(Color32, f32)> {
        match shape {
            Shape::Rect(shape) if shape.rect == rect => Some((shape.fill, shape.stroke.width)),
            Shape::Vec(shapes) => shapes.iter().find_map(|shape| find(shape, rect)),
            _ => None,
        }
    }
    shapes.iter().find_map(|shape| find(&shape.shape, rect)).expect("selected segment painted")
}

fn exercise(mode: &str) {
    let report = Report::synthetic();
    let original = report.rows.clone();
    let before_learning = report.category_seconds("learning");
    let before_unclassified = report.category_seconds("unclassified");
    assert_eq!(report.rows.len(), 1440);
    let selected = report.rows.iter().find(|row| row.id == 555).unwrap();
    assert_eq!((selected.start, selected.end, selected.app.as_str(), selected.category.as_str()),
        (33240, 33300, "browser", "unclassified"));
    let mut harness = Harness::builder().with_size(egui::vec2(1100.0, 800.0))
        .with_os(egui::os::OperatingSystem::Windows)
        .build_ui_state(|ui, state: &mut Report| state.show(ui), report);
    harness.run();
    assert_eq!(selected_paint(&harness.output().shapes, harness.state().selected_rect),
        (Color32::from_rgb(0x25, 0x63, 0xeb), 2.0));
    harness.get_by_role_and_label(Role::TextInput, INPUT_LABEL);
    harness.get_by_role_and_label(Role::Button, APPLY_LABEL);

    // Real egui key/text events focus, replace input, and navigate to the button.
    harness.key_press(Key::Tab);
    harness.run();
    assert!(harness.get_by_role_and_label(Role::TextInput, INPUT_LABEL).is_focused());
    // A physical Ctrl key also sets egui's platform-neutral command flag on Windows.
    harness.key_press_modifiers(Modifiers { ctrl: true, command: true, ..Modifiers::NONE }, Key::A);
    harness.get_by_role_and_label(Role::TextInput, INPUT_LABEL).type_text("learning");
    harness.run();
    assert_eq!(harness.get_by_role_and_label(Role::TextInput, INPUT_LABEL).value().as_deref(), Some("learning"));
    match mode {
        "keyboard_tab_space" => {
            harness.key_press(Key::Tab);
            harness.run();
            assert!(harness.get_by_role_and_label(Role::Button, APPLY_LABEL).is_focused());
            harness.key_press(Key::Space);
        }
        "keyboard_ctrl_enter" => harness.key_press_modifiers(Modifiers::CTRL, Key::Enter),
        "accesskit_click" => harness.get_by_role_and_label(Role::Button, APPLY_LABEL).click_accesskit(),
        _ => unreachable!(),
    }
    harness.run();
    let state = harness.state();
    assert_eq!(state.commits, 1);
    assert_eq!(state.corrections.len(), 1);
    assert_eq!(state.rows, original, "correction must not mutate original observations");
    assert_eq!(state.selected_text(), SELECTED_TEXT);
    assert_eq!(state.category_seconds("learning"), before_learning + 60);
    assert_eq!(state.category_seconds("unclassified"), before_unclassified - 60);
    harness.get_by_label(SELECTED_TEXT);
    harness.get_by_label(format!("learning_seconds={}", before_learning + 60));
    harness.get_by_label(format!("unclassified_seconds={}", before_unclassified - 60));
    assert_eq!(selected_paint(&harness.output().shapes, state.selected_rect),
        (Color32::from_rgb(0x8b, 0x3f, 0xba), 2.0));
    let painted_segments = harness.output().shapes.iter().filter(|shape|
        matches!(&shape.shape, Shape::Rect(r) if r.rect.size() == egui::vec2(13.0, 20.0))).count();
    assert_eq!(painted_segments, 60);
    println!("PROBE_RESULT mode={mode} rows=1440 corrected_id=555 commits=1 learning_seconds={} unclassified_seconds={} segments=60 selected_fill_before=#2563eb selected_fill_after=#8b3fba selected_stroke=2 source_unchanged=true semantic_text_verified=true headless=true gpu=false timing_comparable=false", state.category_seconds("learning"), state.category_seconds("unclassified"));
}

#[test]
fn keyboard_tab_space() { exercise("keyboard_tab_space"); }
#[test]
fn keyboard_ctrl_enter() { exercise("keyboard_ctrl_enter"); }
#[test]
fn accesskit_click() { exercise("accesskit_click"); }
