const {app, BrowserWindow, ipcMain, session} = require('electron');
const fs = require('node:fs'); const path = require('node:path'); const crypto = require('node:crypto');
const args = process.argv.slice(2), fixturePath = path.resolve(args[0]), output = path.resolve(args[1]);
const auto = args.includes('--auto'), capture = args.includes('--capture-surface'); fs.mkdirSync(output, {recursive:true});
const profile = path.join(__dirname, 'profiles', path.basename(output));
fs.mkdirSync(profile, {recursive:true});
app.setPath('userData', profile); // TEMP work tree only, outside uploaded results.
for (const sw of ['disable-background-networking','disable-component-update','disable-domain-reliability','disable-breakpad']) app.commandLine.appendSwitch(sw);
app.commandLine.appendSwitch('disable-features','MediaRouter');
const bytes = fs.readFileSync(fixturePath), hash = crypto.createHash('sha256').update(bytes).digest('hex');
const rows = bytes.toString('utf8').trim().split(/\r?\n/).slice(1).map(line=>{const [id,start,end,app,category]=line.split('\t');return {id:+id,start:+start,end:+end,app,category};});
if (rows.length !== 1440 || rows.find(x=>x.id===555).app !== 'browser') throw Error('Unexpected shared fixture');
const emit = (name,data)=>fs.appendFileSync(path.join(output,'events.jsonl'),JSON.stringify({name,utc:new Date().toISOString(),data})+'\n');
const marker = (name,data)=>{const dest=path.join(output,name+'.json');fs.writeFileSync(dest+'.tmp',JSON.stringify(data));fs.renameSync(dest+'.tmp',dest);};
let win;
const captureSurface = async phase => {if(capture){const picture=await win.webContents.capturePage();fs.writeFileSync(path.join(output,'surface-'+phase+'.png'),picture.toPNG());emit('surface-captured',{phase,method:'webContents.capturePage of this report; not desktop capture'});}};
ipcMain.handle('fixture',()=>({rows,hash,auto}));
ipcMain.on('ready',(_event,data)=>{ const result={runtime:'electron',pid:process.pid,native_handle:win.getNativeWindowHandle().readBigUInt64LE().toString(),versions:process.versions,fixture_sha256:hash,...data};emit('ready',result);marker('ready',result);captureSurface('before').catch(e=>emit('surface-error',{error:String(e)}));});
ipcMain.on('corrected',(_event,data)=>{const result={runtime:'electron',fixture_sha256:hash,...data};emit('corrected',result);marker('corrected',result);captureSurface('after').catch(e=>emit('surface-error',{error:String(e)}));});
app.whenReady().then(()=>{
  session.defaultSession.webRequest.onBeforeRequest((details,callback)=>callback({cancel: !details.url.startsWith('file:') && !details.url.startsWith('data:')}));
  win=new BrowserWindow({title:'FocusWatch paired report — Electron',width:1100,height:750,useContentSize:true,resizable:false,autoHideMenuBar:true,backgroundColor:'#ffffff',webPreferences:{preload:path.join(__dirname,'preload.cjs'),nodeIntegration:false,contextIsolation:true,sandbox:true}});
  win.loadFile(path.join(__dirname,'index.html'));
  const poll=setInterval(()=>{if(fs.existsSync(path.join(output,'close')))win.close();},100);
  win.on('closed',()=>{clearInterval(poll);emit('closed',{});});
});
app.on('window-all-closed',()=>app.quit());
