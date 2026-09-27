const {app, BrowserWindow, ipcMain} = require('electron');
const path = require('path');
app.disableHardwareAcceleration();
app.setPath('userData', process.env.PROBE_PROFILE);
ipcMain.handle('probe-config', () => Number(process.env.PROBE_SEGMENTS || '10000'));
ipcMain.on('probe-report', (_event, payload) => console.log('DESKTOP_PROBE ' + JSON.stringify(payload)));
app.whenReady().then(() => {
  const win = new BrowserWindow({width:1200,height:700,show:true,
    webPreferences:{preload:path.join(__dirname,'preload.cjs'),sandbox:true,contextIsolation:true,nodeIntegration:false}});
  win.setMenu(null);
  win.loadFile(path.join(__dirname,'dist','index.html'));
});
app.on('window-all-closed', () => app.quit());
