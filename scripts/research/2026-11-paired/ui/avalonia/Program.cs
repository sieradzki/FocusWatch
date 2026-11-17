using System.Diagnostics;
using System.Globalization;
using System.Security.Cryptography;
using System.Text.Json;
using Avalonia;
using Avalonia.Automation;
using Avalonia.Controls;
using Avalonia.Controls.Shapes;
using Avalonia.Input;
using Avalonia.Interactivity;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using Avalonia.Themes.Fluent;
using Avalonia.Threading;
using Path = System.IO.Path;

namespace PairedReport;

public static class Program
{
    public static string Fixture = "", Output = "";
    public static bool Auto;
    public static bool Capture;
    [STAThread]
    public static int Main(string[] args)
    {
        if (args.Length < 2) return 2;
        Fixture = Path.GetFullPath(args[0]); Output = Path.GetFullPath(args[1]);
        Auto = args.Contains("--auto"); Capture = args.Contains("--capture-surface"); Directory.CreateDirectory(Output);
        BuildAvaloniaApp().StartWithClassicDesktopLifetime(args);
        return 0;
    }
    public static AppBuilder BuildAvaloniaApp() => AppBuilder.Configure<ProbeApp>().UsePlatformDetect();
    public static void Emit(string name, object data) => File.AppendAllText(Path.Combine(Output, "events.jsonl"),
        JsonSerializer.Serialize(new { name, utc = DateTimeOffset.UtcNow, ticks = Stopwatch.GetTimestamp(), data }) + "\n");
    public static void Marker(string name, object data)
    {
        var dest = Path.Combine(Output, name + ".json");
        File.WriteAllText(dest + ".tmp", JsonSerializer.Serialize(data)); File.Move(dest + ".tmp", dest, true);
    }
}

public sealed class ProbeApp : Application
{
    public override void Initialize() => Styles.Add(new FluentTheme());
    public override void OnFrameworkInitializationCompleted()
    {
        if (ApplicationLifetime is Avalonia.Controls.ApplicationLifetimes.IClassicDesktopStyleApplicationLifetime desktop)
            desktop.MainWindow = new ReportWindow();
        base.OnFrameworkInitializationCompleted();
    }
}

public sealed record Observation(int Id, int Start, int End, string App, string Category);

public sealed class ReportWindow : Window
{
    private readonly List<Observation> rows;
    private readonly Dictionary<int, string> edits = new();
    private readonly TextBox category = new() { Text = "learning", Width = 200 };
    private readonly TextBlock selected = new(), categories = new();
    private readonly StackPanel table = new() { Spacing = 0 };
    private readonly Canvas timeline = new() { Width = 980, Height = 130 };
    private readonly Button apply = new() { Content = "Apply correction (Ctrl+Enter)", Padding = new Thickness(16, 7) };
    private readonly string fixtureHash;
    private readonly string[] colors = ["#2563eb", "#dc6b2f", "#16836a", "#6b7280"];
    private readonly Dictionary<int, Rectangle> timelineRects = new();
    private readonly Dictionary<int, TextBlock> detailRows = new();
    private bool ready;

    public ReportWindow()
    {
        Title = "FocusWatch paired report — Avalonia";
        Width = 1100; Height = 750; CanResize = false; WindowStartupLocation = WindowStartupLocation.CenterScreen;
        Background = Brushes.White; Foreground = Brush.Parse("#18202c"); FontFamily = new FontFamily("Segoe UI"); FontSize = 14;
        fixtureHash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(Program.Fixture))).ToLowerInvariant();
        rows = File.ReadLines(Program.Fixture).Skip(1).Where(x => !string.IsNullOrWhiteSpace(x)).Select(line =>
        {
            var p = line.Split('\t'); return new Observation(int.Parse(p[0]), int.Parse(p[1]), int.Parse(p[2]), p[3], p[4]);
        }).ToList();
        if (rows.Count != 1440 || rows.Single(x => x.Id == 555).App != "browser") throw new Exception("Unexpected shared fixture");
        AutomationProperties.SetAutomationId(category, "correction-category");
        AutomationProperties.SetName(category, "Correction category");
        AutomationProperties.SetAutomationId(apply, "apply-correction");
        AutomationProperties.SetAutomationId(selected, "selected-result");
        AutomationProperties.SetAutomationId(categories, "category-totals");
        apply.Click += Apply;
        KeyDown += (_, e) => { if (e.Key == Key.Enter && e.KeyModifiers.HasFlag(KeyModifiers.Control)) { apply.RaiseEvent(new RoutedEventArgs(Button.ClickEvent)); e.Handled = true; } };
        var root = new StackPanel { Margin = new Thickness(28, 20), Spacing = 8 };
        root.Children.Add(new TextBlock { Text = "Synthetic activity day", FontSize = 26, FontWeight = FontWeight.SemiBold });
        root.Children.Add(new TextBlock { Text = "1440 observations · 24h source time · foreground only · no personal data", Foreground = Brush.Parse("#536173") });
        root.Children.Add(new TextBlock { Text = string.Join("    ", rows.GroupBy(x => x.App).OrderBy(x => x.Key, StringComparer.Ordinal).Select(g => $"{g.Key}: {g.Sum(x => x.End - x.Start) / 60} min")), FontWeight = FontWeight.SemiBold });
        root.Children.Add(new TextBlock { Text = "Timeline 09:00–10:00 · each block = one minute", FontSize = 17 });
        root.Children.Add(timeline);
        root.Children.Add(new TextBlock { Text = "Detail 09:10–09:20 · selected observation #555", FontSize = 17 });
        root.Children.Add(table);
        root.Children.Add(new Border { Background = Brush.Parse("#eaf0fa"), Padding = new Thickness(8), Child = selected });
        var controls = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 12 };
        controls.Children.Add(new TextBlock { Text = "Category", VerticalAlignment = VerticalAlignment.Center });
        controls.Children.Add(category); controls.Children.Add(apply); root.Children.Add(controls);
        root.Children.Add(categories);
        root.Children.Add(new TextBlock { Text = "App/title inference is excluded. Categories are interpretations; source intervals remain unchanged.", FontSize = 12, Foreground = Brush.Parse("#536173") });
        Content = root; RenderReport();
        Opened += (_, _) => RequestAnimationFrame(_ => RequestAnimationFrame(_ =>
        {
            if (ready) return; ready = true;
            var data = new { runtime = "avalonia", pid = Environment.ProcessId, native_handle = TryGetPlatformHandle()?.Handle.ToInt64().ToString(), avalonia = typeof(Application).Assembly.GetName().Version?.ToString(), dotnet = Environment.Version.ToString(), fixture_sha256 = fixtureHash, rows = rows.Count, client_width = ClientSize.Width, client_height = ClientSize.Height };
            Program.Emit("ready", data); Program.Marker("ready", data);
            CaptureSurface("before");
            if (Program.Auto) DispatcherTimer.RunOnce(() => RaiseEvent(new KeyEventArgs { RoutedEvent = KeyDownEvent, Key = Key.Enter, KeyModifiers = KeyModifiers.Control }), TimeSpan.FromMilliseconds(500));
        }));
        Closed += (_, _) => Program.Emit("closed", new { });
        var poll = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(100) };
        poll.Tick += (_, _) => { if (File.Exists(Path.Combine(Program.Output, "close"))) { poll.Stop(); Close(); } }; poll.Start();
    }
    private string Effective(Observation r) => edits.TryGetValue(r.Id, out var c) ? c : r.Category;
    private void CaptureSurface(string phase)
    {
        if (!Program.Capture) return;
        using var bitmap = new RenderTargetBitmap(new PixelSize((int)Math.Ceiling(ClientSize.Width * RenderScaling), (int)Math.Ceiling(ClientSize.Height * RenderScaling)), new Vector(RenderScaling * 96, RenderScaling * 96));
        bitmap.Render(this); bitmap.Save(Path.Combine(Program.Output, "surface-" + phase + ".png"));
        Program.Emit("surface-captured", new { phase, method = "RenderTargetBitmap of this actual window control surface; not desktop capture" });
    }
    private static string Time(int seconds) => $"{seconds / 3600:00}:{seconds / 60 % 60:00}";
    private void RenderReport()
    {
        var apps = rows.Select(x => x.App).Distinct().Order(StringComparer.Ordinal).ToArray();
        timeline.Children.Clear();
        for (var i = 0; i < apps.Length; i++)
        {
            var label = new TextBlock { Text = apps[i], Width = 90, FontSize = 12 }; Canvas.SetTop(label, 15 + i * 30); timeline.Children.Add(label);
        }
        foreach (var r in rows.Where(x => x.Start >= 9 * 3600 && x.Start < 10 * 3600))
        {
            int lane = Array.IndexOf(apps, r.App);
            var rect = new Rectangle { Width = 13, Height = 20, Fill = Brush.Parse(Effective(r) == "learning" ? "#8b3fba" : colors[lane % colors.Length]), Stroke = r.Id == 555 ? Brushes.Black : null, StrokeThickness = r.Id == 555 ? 2 : 0 };
            Canvas.SetLeft(rect, 100 + (r.Start - 32400) / 60.0 * 14); Canvas.SetTop(rect, 12 + lane * 30); timeline.Children.Add(rect); timelineRects[r.Id] = rect;
        }
        table.Children.Clear();
        foreach (var r in rows.Where(x => x.Id >= 551 && x.Id <= 560))
        {
            var detail = new TextBlock { Text = $"#{r.Id}    {Time(r.Start)}–{Time(r.End)}    {r.App,-12}    {Effective(r)}", Height = 18, Background = r.Id == 555 ? Brush.Parse("#eaf0fa") : Brushes.Transparent };
            table.Children.Add(detail); detailRows[r.Id] = detail;
        }
        UpdateStatus();
    }
    private void UpdateStatus()
    {
        var chosen = rows.Single(x => x.Id == 555);
        selected.Text = $"#555 | {Time(chosen.Start)}–{Time(chosen.End)} | {chosen.App} | category={Effective(chosen)}";
        categories.Text = $"learning_seconds={rows.Where(x => Effective(x) == "learning").Sum(x => x.End - x.Start)} · unclassified_seconds={rows.Where(x => Effective(x) == "unclassified").Sum(x => x.End - x.Start)}";
    }
    private void Apply(object? sender, RoutedEventArgs e)
    {
        var start = Stopwatch.GetTimestamp(); edits[555] = category.Text?.Trim() ?? "";
        var chosen = rows.Single(x => x.Id == 555);
        var apps = rows.Select(x => x.App).Distinct().Order(StringComparer.Ordinal).ToArray();
        timelineRects[555].Fill = Brush.Parse(edits[555] == "learning" ? "#8b3fba" : colors[Array.IndexOf(apps, chosen.App) % colors.Length]);
        detailRows[555].Text = $"#555    {Time(chosen.Start)}–{Time(chosen.End)}    {chosen.App,-12}    {edits[555]}";
        UpdateStatus();
        RequestAnimationFrame(_ => RequestAnimationFrame(_ =>
        {
            var result = new { runtime = "avalonia", fixture_sha256 = fixtureHash, row_count = rows.Count, selected_id = 555, selected_category = edits[555], learning_seconds = rows.Where(x => Effective(x) == "learning").Sum(x => x.End - x.Start), unclassified_seconds = rows.Where(x => Effective(x) == "unclassified").Sum(x => x.End - x.Start), displayed_text = selected.Text, activation_mode = Program.Auto ? "programmatic Ctrl+Enter key event routed within this window" : "manual input", edit_to_two_frames_ms = Stopwatch.GetElapsedTime(start).TotalMilliseconds };
            Program.Emit("corrected", result); Program.Marker("corrected", result);
            CaptureSurface("after");
        }));
    }
}
