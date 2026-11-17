// Isolated synthetic experiment. No collector, window, input or media APIs.
use std::{env, ffi::{c_char,c_int,c_void,CStr,CString}, fs, ptr, thread, time::{Duration,Instant}};
type Db = *mut c_void;
type Stmt = *mut c_void;
#[link(name="kernel32")]
unsafe extern "system" {
    fn LoadLibraryExW(name:*const u16, file:*mut c_void, flags:u32)->*mut c_void;
    fn GetProcAddress(module:*mut c_void, name:*const c_char)->*mut c_void;
}
struct Sqlite {
    open: unsafe extern "C" fn(*const c_char,*mut Db,c_int,*const c_char)->c_int,
    exec: unsafe extern "C" fn(Db,*const c_char,*mut c_void,*mut c_void,*mut c_void)->c_int,
    prepare: unsafe extern "C" fn(Db,*const c_char,c_int,*mut Stmt,*mut c_void)->c_int,
    bind_int: unsafe extern "C" fn(Stmt,c_int,i64)->c_int,
    bind_text: unsafe extern "C" fn(Stmt,c_int,*const c_char,c_int,isize)->c_int,
    step: unsafe extern "C" fn(Stmt)->c_int,
    reset: unsafe extern "C" fn(Stmt)->c_int,
    clear: unsafe extern "C" fn(Stmt)->c_int,
    finalize: unsafe extern "C" fn(Stmt)->c_int,
    close: unsafe extern "C" fn(Db)->c_int,
    column_int: unsafe extern "C" fn(Stmt,c_int)->i64,
    column_text: unsafe extern "C" fn(Stmt,c_int)->*const c_char,
    version: unsafe extern "C" fn()->*const c_char,
    errmsg: unsafe extern "C" fn(Db)->*const c_char,
}
fn string(p:*const c_char)->String {
    if p.is_null() { String::new() } else { unsafe { CStr::from_ptr(p).to_string_lossy().into_owned() } }
}
impl Sqlite {
    unsafe fn load()->Self {
        let name:Vec<u16>="winsqlite3.dll\0".encode_utf16().collect();
        let module=unsafe { LoadLibraryExW(name.as_ptr(),ptr::null_mut(),0x800) }; // SYSTEM32 only
        assert!(!module.is_null(),"load system winsqlite3.dll");
        macro_rules! symbol { ($name:literal,$ty:ty)=>{{
            let p=unsafe { GetProcAddress(module,concat!($name,"\0").as_ptr() as _) };
            assert!(!p.is_null(),"missing symbol {}",$name);
            unsafe { std::mem::transmute::<*mut c_void,$ty>(p) }
        }}; }
        Self {
            open:symbol!("sqlite3_open_v2",unsafe extern "C" fn(*const c_char,*mut Db,c_int,*const c_char)->c_int),
            exec:symbol!("sqlite3_exec",unsafe extern "C" fn(Db,*const c_char,*mut c_void,*mut c_void,*mut c_void)->c_int),
            prepare:symbol!("sqlite3_prepare_v2",unsafe extern "C" fn(Db,*const c_char,c_int,*mut Stmt,*mut c_void)->c_int),
            bind_int:symbol!("sqlite3_bind_int64",unsafe extern "C" fn(Stmt,c_int,i64)->c_int),
            bind_text:symbol!("sqlite3_bind_text",unsafe extern "C" fn(Stmt,c_int,*const c_char,c_int,isize)->c_int),
            step:symbol!("sqlite3_step",unsafe extern "C" fn(Stmt)->c_int),
            reset:symbol!("sqlite3_reset",unsafe extern "C" fn(Stmt)->c_int),
            clear:symbol!("sqlite3_clear_bindings",unsafe extern "C" fn(Stmt)->c_int),
            finalize:symbol!("sqlite3_finalize",unsafe extern "C" fn(Stmt)->c_int),
            close:symbol!("sqlite3_close",unsafe extern "C" fn(Db)->c_int),
            column_int:symbol!("sqlite3_column_int64",unsafe extern "C" fn(Stmt,c_int)->i64),
            column_text:symbol!("sqlite3_column_text",unsafe extern "C" fn(Stmt,c_int)->*const c_char),
            version:symbol!("sqlite3_libversion",unsafe extern "C" fn()->*const c_char),
            errmsg:symbol!("sqlite3_errmsg",unsafe extern "C" fn(Db)->*const c_char),
        }
    }
    fn check(&self,db:Db,code:c_int,wanted:c_int) {
        assert_eq!(code,wanted,"sqlite: {}",string(unsafe{(self.errmsg)(db)}));
    }
    fn exec(&self,db:Db,sql:&str) {
        let text=CString::new(sql).unwrap();
        self.check(db,unsafe{(self.exec)(db,text.as_ptr(),ptr::null_mut(),ptr::null_mut(),ptr::null_mut())},0);
    }
    fn prepare(&self,db:Db,sql:&str)->Stmt {
        let text=CString::new(sql).unwrap(); let mut stmt=ptr::null_mut();
        self.check(db,unsafe{(self.prepare)(db,text.as_ptr(),-1,&mut stmt,ptr::null_mut())},0); stmt
    }
}
struct Row { id:i64,start:i64,end:i64,app:CString,category:CString }
fn main() {
    let args:Vec<String>=env::args().collect();
    assert_eq!(args.len(),7,"fixture schema db idle_ms interval_ms batch_size");
    let input=fs::read_to_string(&args[1]).unwrap();
    let mut lines=input.lines(); assert_eq!(lines.next().unwrap(),"id\tstart_s\tend_s\tapp\tcategory");
    let rows:Vec<Row>=lines.map(|line| { let c:Vec<&str>=line.split('\t').collect(); assert_eq!(c.len(),5);
        Row{id:c[0].parse().unwrap(),start:c[1].parse().unwrap(),end:c[2].parse().unwrap(),app:CString::new(c[3]).unwrap(),category:CString::new(c[4]).unwrap()}
    }).collect();
    let idle:u64=args[4].parse().unwrap(); let interval:u64=args[5].parse().unwrap(); let batch:usize=args[6].parse().unwrap();
    assert!(!std::path::Path::new(&args[3]).exists(),"database must be new");
    let sqlite=unsafe{Sqlite::load()}; let mut db:Db=ptr::null_mut(); let path=CString::new(args[3].as_bytes()).unwrap();
    sqlite.check(db,unsafe{(sqlite.open)(path.as_ptr(),&mut db,6,ptr::null())},0);
    sqlite.exec(db,&fs::read_to_string(&args[2]).unwrap());
    let insert=sqlite.prepare(db,"INSERT INTO observations(id,start_s,end_s,app,category) VALUES(?1,?2,?3,?4,?5)");
    println!("META\trust\t{}\t{}\t{}",option_env!("RUSTC_VERSION").unwrap_or("see build manifest"),string(unsafe{(sqlite.version)()}),rows.len());
    println!("PHASE\tidle"); thread::sleep(Duration::from_millis(idle));
    println!("PHASE\tactive"); let clock=Instant::now(); let batches=rows.len().div_ceil(batch);
    for (b,chunk) in rows.chunks(batch).enumerate() {
        let target=Duration::from_millis(b as u64*interval); if target>clock.elapsed() {thread::sleep(target-clock.elapsed());}
        sqlite.exec(db,"BEGIN IMMEDIATE");
        for r in chunk { unsafe {
            sqlite.check(db,(sqlite.bind_int)(insert,1,r.id),0); sqlite.check(db,(sqlite.bind_int)(insert,2,r.start),0); sqlite.check(db,(sqlite.bind_int)(insert,3,r.end),0);
            sqlite.check(db,(sqlite.bind_text)(insert,4,r.app.as_ptr(),-1,-1),0); sqlite.check(db,(sqlite.bind_text)(insert,5,r.category.as_ptr(),-1,-1),0);
            sqlite.check(db,(sqlite.step)(insert),101); sqlite.check(db,(sqlite.reset)(insert),0); sqlite.check(db,(sqlite.clear)(insert),0);
        }}
        sqlite.exec(db,"COMMIT");
    }
    let target=Duration::from_millis(batches as u64*interval); if target>clock.elapsed() {thread::sleep(target-clock.elapsed());}
    println!("PHASE\tverify"); sqlite.check(db,unsafe{(sqlite.finalize)(insert)},0);
    let summary=sqlite.prepare(db,"SELECT count(*),coalesce(sum(end_s-start_s),0),coalesce(sum(id),0),coalesce(sum(id*(end_s-start_s)),0) FROM observations");
    sqlite.check(db,unsafe{(sqlite.step)(summary)},100);
    unsafe { println!("SUMMARY\t{}\t{}\t{}\t{}",(sqlite.column_int)(summary,0),(sqlite.column_int)(summary,1),(sqlite.column_int)(summary,2),(sqlite.column_int)(summary,3)); }
    sqlite.check(db,unsafe{(sqlite.finalize)(summary)},0);
    let groups=sqlite.prepare(db,"SELECT app,category,count(*),sum(end_s-start_s) FROM observations GROUP BY app,category ORDER BY app,category");
    loop { let code=unsafe{(sqlite.step)(groups)}; if code==101 {break;} sqlite.check(db,code,100);
        unsafe {println!("GROUP\t{}\t{}\t{}\t{}",string((sqlite.column_text)(groups,0)),string((sqlite.column_text)(groups,1)),(sqlite.column_int)(groups,2),(sqlite.column_int)(groups,3));}
    }
    sqlite.check(db,unsafe{(sqlite.finalize)(groups)},0); sqlite.check(db,unsafe{(sqlite.close)(db)},0);
    println!("DONE");
}
