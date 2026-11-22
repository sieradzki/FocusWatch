use std::{
    fs::{self, File, OpenOptions},
    io,
    path::{Path, PathBuf},
};

/// Every invocation names an isolated synthetic profile explicitly.
pub struct State {
    pub path: PathBuf,
    _lock: File,
}

impl State {
    pub fn open(path: &Path) -> io::Result<Self> {
        if !path.is_absolute() {
            return Err(io::Error::other("--state must be absolute"));
        }
        let mut builder = fs::DirBuilder::new();
        #[cfg(unix)]
        std::os::unix::fs::DirBuilderExt::mode(&mut builder, 0o700);
        if let Err(e) = builder.create(path)
            && e.kind() != io::ErrorKind::AlreadyExists
        {
            return Err(e);
        }
        let meta = fs::symlink_metadata(path)?;
        if !meta.is_dir() {
            return Err(io::Error::other("expected state directory"));
        }
        #[cfg(unix)]
        if std::os::unix::fs::PermissionsExt::mode(&meta.permissions()) & 0o077 != 0 {
            return Err(io::Error::other(
                "state must be a private directory (mode 0700)",
            ));
        }
        let path = path.canonicalize()?;
        let lock_path = path.join(".focuswatch-synthetic-p0.lock");
        if !lock_path.try_exists()? && path.read_dir()?.next().is_some() {
            return Err(io::Error::other(
                "choose an empty directory or an existing synthetic P0 profile",
            ));
        }
        let lock = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .open(lock_path)?;
        lock.try_lock()
            .map_err(|_| io::Error::other("state is in use or locking is unavailable"))?;
        Ok(Self { path, _lock: lock })
    }
}
