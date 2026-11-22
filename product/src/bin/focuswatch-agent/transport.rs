use std::{io, path::Path};

#[cfg(windows)]
mod windows {
    use super::*;
    use std::{
        ffi::c_void,
        os::windows::io::{AsRawHandle, FromRawHandle, OwnedHandle},
        ptr,
    };
    use tokio::net::windows::named_pipe::{NamedPipeServer, ServerOptions};
    use windows_sys::Win32::{
        Foundation::{ERROR_INSUFFICIENT_BUFFER, LocalFree},
        Security::{
            Authorization::{
                ConvertSidToStringSidW, ConvertStringSecurityDescriptorToSecurityDescriptorW,
            },
            GetTokenInformation, SECURITY_ATTRIBUTES, TOKEN_GROUPS, TOKEN_QUERY, TokenLogonSid,
        },
        System::Threading::{GetCurrentProcess, OpenProcessToken},
    };

    struct LocalAllocation(*mut c_void);
    impl Drop for LocalAllocation {
        fn drop(&mut self) {
            unsafe {
                LocalFree(self.0);
            }
        }
    }

    fn logon_descriptor() -> io::Result<LocalAllocation> {
        // TokenLogonSid identifies this logon session, including its restricted child processes.
        unsafe {
            let mut token = ptr::null_mut();
            if OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &mut token) == 0 {
                return Err(io::Error::last_os_error());
            }
            let token = OwnedHandle::from_raw_handle(token);
            let mut bytes = 0;
            GetTokenInformation(
                token.as_raw_handle(),
                TokenLogonSid,
                ptr::null_mut(),
                0,
                &mut bytes,
            );
            let err = io::Error::last_os_error();
            if err.raw_os_error() != Some(ERROR_INSUFFICIENT_BUFFER as i32)
                || bytes < size_of::<TOKEN_GROUPS>() as u32
            {
                return Err(err);
            }
            let mut storage = vec![0usize; (bytes as usize).div_ceil(size_of::<usize>())];
            if GetTokenInformation(
                token.as_raw_handle(),
                TokenLogonSid,
                storage.as_mut_ptr().cast(),
                bytes,
                &mut bytes,
            ) == 0
            {
                return Err(io::Error::last_os_error());
            }
            let groups = &*storage.as_ptr().cast::<TOKEN_GROUPS>();
            if groups.GroupCount != 1 {
                return Err(io::Error::other("missing logon SID"));
            }
            let mut sid = ptr::null_mut();
            if ConvertSidToStringSidW(groups.Groups[0].Sid, &mut sid) == 0 {
                return Err(io::Error::last_os_error());
            }
            let _sid_memory = LocalAllocation(sid.cast());
            let mut len = 0;
            while *sid.add(len) != 0 {
                len += 1;
            }
            let sid = String::from_utf16(std::slice::from_raw_parts(sid, len))
                .map_err(io::Error::other)?;
            let sddl: Vec<u16> = format!("D:P(A;;GA;;;{sid})")
                .encode_utf16()
                .chain(Some(0))
                .collect();
            let mut descriptor = ptr::null_mut();
            if ConvertStringSecurityDescriptorToSecurityDescriptorW(
                sddl.as_ptr(),
                1,
                &mut descriptor,
                ptr::null_mut(),
            ) == 0
            {
                return Err(io::Error::last_os_error());
            }
            Ok(LocalAllocation(descriptor))
        }
    }

    pub struct Listener {
        name: String,
        acl: LocalAllocation,
        next: NamedPipeServer,
    }
    impl Listener {
        fn pipe(name: &str, acl: &LocalAllocation, first: bool) -> io::Result<NamedPipeServer> {
            let mut attrs = SECURITY_ATTRIBUTES {
                nLength: size_of::<SECURITY_ATTRIBUTES>() as u32,
                lpSecurityDescriptor: acl.0,
                bInheritHandle: 0,
            };
            unsafe {
                ServerOptions::new()
                    .first_pipe_instance(first)
                    .reject_remote_clients(true)
                    .in_buffer_size(4096)
                    .out_buffer_size(16384)
                    .create_with_security_attributes_raw(
                        name,
                        (&mut attrs as *mut SECURITY_ATTRIBUTES).cast(),
                    )
            }
        }
        pub fn bind(name: &str, _: &Path) -> io::Result<Self> {
            let suffix = name.strip_prefix(r"\\.\pipe\focuswatch-p0-").unwrap_or("");
            if suffix.is_empty()
                || suffix.len() > 90
                || !suffix
                    .bytes()
                    .all(|b| b.is_ascii_alphanumeric() || b == b'-')
            {
                return Err(io::Error::other(
                    "expected local pipe name starting with focuswatch-p0-",
                ));
            }
            let acl = logon_descriptor()?;
            let next = Self::pipe(name, &acl, true)?;
            Ok(Self {
                name: name.into(),
                acl,
                next,
            })
        }
        pub async fn accept(&mut self) -> io::Result<NamedPipeServer> {
            self.next.connect().await?;
            Ok(std::mem::replace(
                &mut self.next,
                Self::pipe(&self.name, &self.acl, false)?,
            ))
        }
    }
}
#[cfg(windows)]
pub use windows::Listener;

#[cfg(unix)]
mod unix {
    use super::*;
    use std::{fs, os::unix::fs::FileTypeExt, path::PathBuf};
    use tokio::net::{UnixListener, UnixStream};
    pub struct Listener {
        listener: UnixListener,
        path: PathBuf,
    }
    impl Listener {
        pub fn bind(name: &str, state: &Path) -> io::Result<Self> {
            let path = PathBuf::from(name);
            if !path.is_absolute()
                || path.file_name().and_then(|v| v.to_str()) != Some("report.sock")
                || path.parent().and_then(|p| p.canonicalize().ok()).as_deref() != Some(state)
            {
                return Err(io::Error::other(
                    "endpoint must be report.sock inside the private state directory",
                ));
            }
            // Caller holds the exclusive state lock. Remove only the previous session's socket.
            if let Ok(meta) = fs::symlink_metadata(&path) {
                if !meta.file_type().is_socket() {
                    return Err(io::Error::other("endpoint is not a socket"));
                }
                fs::remove_file(&path)?;
            }
            Ok(Self {
                listener: UnixListener::bind(&path)?,
                path,
            })
        }
        pub async fn accept(&mut self) -> io::Result<UnixStream> {
            Ok(self.listener.accept().await?.0)
        }
    }
    impl Drop for Listener {
        fn drop(&mut self) {
            let _ = fs::remove_file(&self.path);
        }
    }
}
#[cfg(unix)]
pub use unix::Listener;
