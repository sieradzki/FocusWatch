using System.Diagnostics;
using System.Globalization;
using System.Runtime.InteropServices;
using System.Text;

// Isolated synthetic experiment. No collector, window, input or media APIs.
static class Sqlite
{
    const string Dll = "winsqlite3.dll";
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern int sqlite3_open_v2([MarshalAs(UnmanagedType.LPUTF8Str)] string path, out IntPtr db, int flags, IntPtr vfs);
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern int sqlite3_exec(IntPtr db, [MarshalAs(UnmanagedType.LPUTF8Str)] string sql, IntPtr callback, IntPtr arg, IntPtr error);
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern int sqlite3_prepare_v2(IntPtr db, [MarshalAs(UnmanagedType.LPUTF8Str)] string sql, int bytes, out IntPtr stmt, IntPtr tail);
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern int sqlite3_bind_int64(IntPtr stmt, int index, long value);
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern int sqlite3_bind_text(IntPtr stmt, int index, byte[] value, int bytes, IntPtr destructor);
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern int sqlite3_step(IntPtr stmt);
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern int sqlite3_reset(IntPtr stmt);
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern int sqlite3_clear_bindings(IntPtr stmt);
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern int sqlite3_finalize(IntPtr stmt);
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern int sqlite3_close(IntPtr db);
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern long sqlite3_column_int64(IntPtr stmt, int index);
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern IntPtr sqlite3_column_text(IntPtr stmt, int index);
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern IntPtr sqlite3_libversion();
    [DllImport(Dll, CallingConvention = CallingConvention.Cdecl)]
    [DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
    public static extern IntPtr sqlite3_errmsg(IntPtr db);
}

record Row(long Id, long Start, long End, byte[] App, byte[] Category);
static class Program
{
    static IntPtr db;
    static string Str(IntPtr p) => Marshal.PtrToStringUTF8(p) ?? "";
    static void Check(int rc, int wanted = 0)
    {
        if (rc != wanted) throw new Exception($"sqlite rc={rc}, expected={wanted}: {Str(Sqlite.sqlite3_errmsg(db))}");
    }
    static void Exec(string sql) => Check(Sqlite.sqlite3_exec(db, sql, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero));
    static IntPtr Prepare(string sql)
    {
        Check(Sqlite.sqlite3_prepare_v2(db, sql, -1, out var stmt, IntPtr.Zero));
        return stmt;
    }
    static void Main(string[] args)
    {
        CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
        if (args.Length != 6) throw new ArgumentException("fixture schema db idle_ms interval_ms batch_size");
        string[] lines = File.ReadAllLines(args[0]);
        if (lines[0] != "id\tstart_s\tend_s\tapp\tcategory") throw new Exception("fixture header");
        var rows = new List<Row>();
        foreach (string line in lines.Skip(1))
        {
            string[] c = line.Split('\t');
            if (c.Length != 5) throw new Exception("fixture columns");
            rows.Add(new Row(long.Parse(c[0]), long.Parse(c[1]), long.Parse(c[2]), Encoding.UTF8.GetBytes(c[3] + "\0"), Encoding.UTF8.GetBytes(c[4] + "\0")));
        }
        int idle = int.Parse(args[3]), interval = int.Parse(args[4]), batch = int.Parse(args[5]);
        if (File.Exists(args[2])) throw new Exception("database must be new");
        Check(Sqlite.sqlite3_open_v2(args[2], out db, 6, IntPtr.Zero)); // READWRITE | CREATE
        Exec(File.ReadAllText(args[1]));
        IntPtr insert = Prepare("INSERT INTO observations(id,start_s,end_s,app,category) VALUES(?1,?2,?3,?4,?5)");
        Console.WriteLine($"META\tcsharp\t{Environment.Version}\t{Str(Sqlite.sqlite3_libversion())}\t{rows.Count}");
        Console.WriteLine("PHASE\tidle");
        Thread.Sleep(idle);
        Console.WriteLine("PHASE\tactive");
        var clock = Stopwatch.StartNew();
        int batches = (rows.Count + batch - 1) / batch;
        for (int b = 0; b < batches; b++)
        {
            double remaining = b * (double)interval - clock.Elapsed.TotalMilliseconds;
            if (remaining > 0) Thread.Sleep(TimeSpan.FromMilliseconds(remaining));
            Exec("BEGIN IMMEDIATE");
            for (int i = b * batch; i < Math.Min(rows.Count, (b + 1) * batch); i++)
            {
                Row r = rows[i];
                Check(Sqlite.sqlite3_bind_int64(insert, 1, r.Id));
                Check(Sqlite.sqlite3_bind_int64(insert, 2, r.Start));
                Check(Sqlite.sqlite3_bind_int64(insert, 3, r.End));
                Check(Sqlite.sqlite3_bind_text(insert, 4, r.App, -1, new IntPtr(-1)));
                Check(Sqlite.sqlite3_bind_text(insert, 5, r.Category, -1, new IntPtr(-1)));
                Check(Sqlite.sqlite3_step(insert), 101);
                Check(Sqlite.sqlite3_reset(insert));
                Check(Sqlite.sqlite3_clear_bindings(insert));
            }
            Exec("COMMIT");
        }
        double tail = batches * (double)interval - clock.Elapsed.TotalMilliseconds;
        if (tail > 0) Thread.Sleep(TimeSpan.FromMilliseconds(tail));
        Console.WriteLine("PHASE\tverify");
        Check(Sqlite.sqlite3_finalize(insert));
        IntPtr summary = Prepare("SELECT count(*),coalesce(sum(end_s-start_s),0),coalesce(sum(id),0),coalesce(sum(id*(end_s-start_s)),0) FROM observations");
        Check(Sqlite.sqlite3_step(summary), 100);
        Console.WriteLine($"SUMMARY\t{Sqlite.sqlite3_column_int64(summary,0)}\t{Sqlite.sqlite3_column_int64(summary,1)}\t{Sqlite.sqlite3_column_int64(summary,2)}\t{Sqlite.sqlite3_column_int64(summary,3)}");
        Check(Sqlite.sqlite3_finalize(summary));
        IntPtr groups = Prepare("SELECT app,category,count(*),sum(end_s-start_s) FROM observations GROUP BY app,category ORDER BY app,category");
        int code;
        while ((code = Sqlite.sqlite3_step(groups)) == 100)
            Console.WriteLine($"GROUP\t{Str(Sqlite.sqlite3_column_text(groups,0))}\t{Str(Sqlite.sqlite3_column_text(groups,1))}\t{Sqlite.sqlite3_column_int64(groups,2)}\t{Sqlite.sqlite3_column_int64(groups,3)}");
        Check(code, 101);
        Check(Sqlite.sqlite3_finalize(groups));
        Check(Sqlite.sqlite3_close(db));
        Console.WriteLine("DONE");
    }
}
