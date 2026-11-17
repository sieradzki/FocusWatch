const {contextBridge, ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('probe',{fixture:()=>ipcRenderer.invoke('fixture'),ready:data=>ipcRenderer.send('ready',data),corrected:data=>ipcRenderer.send('corrected',data)});
