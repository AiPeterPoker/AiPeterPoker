const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getSettings: () => ipcRenderer.invoke('get-settings'),
  setOpacity: (value) => ipcRenderer.invoke('set-opacity', value),
  setClickThrough: (value) => ipcRenderer.invoke('set-click-through', value),
  onClickThroughChanged: (callback) => {
    ipcRenderer.on('click-through-changed', (_, value) => callback(value));
  },
});
