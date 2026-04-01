const { app, BrowserWindow, ipcMain, screen, globalShortcut, Tray, Menu } = require('electron');
const path = require('path');
const Store = require('electron-store');

const store = new Store({
  defaults: { overlayBounds: null, opacity: 0.97, alwaysOnTop: true, clickThrough: false, position: 'right' },
});

let mainWindow = null;
let espWindow = null;
let calibrateWindow = null;
let tray = null;
let isClickThrough = false;

function getGameRegion() {
  try {
    const dotenv = require('dotenv');
    dotenv.config({ path: path.join(__dirname, '..', '.env') });
  } catch(e) {}
  return {
    x: parseInt(process.env.GAME_REGION_X || '0', 10),
    y: parseInt(process.env.GAME_REGION_Y || '0', 10),
    w: parseInt(process.env.GAME_REGION_W || '960', 10),
    h: parseInt(process.env.GAME_REGION_H || '1080', 10),
  };
}

function createWindow() {
  const { width: screenW, height: screenH } = screen.getPrimaryDisplay().workAreaSize;
  const saved = store.get('overlayBounds');
  const bounds = saved || { width: 420, height: screenH - 40, x: screenW - 440, y: 20 };

  mainWindow = new BrowserWindow({
    ...bounds, frame: false, transparent: true, alwaysOnTop: store.get('alwaysOnTop'),
    skipTaskbar: false, resizable: true, hasShadow: false,
    webPreferences: { preload: path.join(__dirname, 'preload.js'), nodeIntegration: false, contextIsolation: true },
  });

  const isDev = !app.isPackaged;
  if (isDev) { mainWindow.loadURL('http://localhost:5173'); }
  else { mainWindow.loadFile(path.join(__dirname, '../dist/index.html')); }

  mainWindow.setOpacity(store.get('opacity'));
  mainWindow.on('moved', () => store.set('overlayBounds', mainWindow.getBounds()));
  mainWindow.on('resized', () => store.set('overlayBounds', mainWindow.getBounds()));
  mainWindow.on('closed', () => { mainWindow = null; });
}

function createEspWindow() {
  const gr = getGameRegion();
  espWindow = new BrowserWindow({
    x: gr.x, y: gr.y, width: gr.w, height: gr.h,
    frame: false, transparent: true, alwaysOnTop: true,
    skipTaskbar: true, resizable: false, hasShadow: false,
    focusable: false,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });
  espWindow.setIgnoreMouseEvents(true, { forward: true });
  espWindow.loadFile(path.join(__dirname, 'esp.html'));
  espWindow.on('closed', () => { espWindow = null; });
}

function openCalibration() {
  if (calibrateWindow) { calibrateWindow.focus(); return; }

  const gr = getGameRegion();
  calibrateWindow = new BrowserWindow({
    x: gr.x, y: gr.y, width: gr.w, height: gr.h,
    frame: false, transparent: true, alwaysOnTop: true,
    skipTaskbar: true, resizable: false, hasShadow: false,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });
  calibrateWindow.loadFile(path.join(__dirname, 'calibrate.html'));
  calibrateWindow.on('closed', () => { calibrateWindow = null; });
}

function createTray() {
  try {
    tray = new Tray(path.join(__dirname, '../assets/tray-icon.png').replace('app.asar', 'app.asar.unpacked'));
    const menu = Menu.buildFromTemplate([
      { label: 'Show/Hide Peter', click: () => mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show() },
      { label: 'Show/Hide ESP', click: () => { if (espWindow) espWindow.isVisible() ? espWindow.hide() : espWindow.show(); }},
      { type: 'separator' },
      { label: 'Calibrate Zones', click: () => openCalibration() },
      { type: 'separator' },
      { label: 'Click-Through Mode', type: 'checkbox', checked: isClickThrough, click: (item) => {
        isClickThrough = item.checked;
        mainWindow.setIgnoreMouseEvents(isClickThrough, { forward: true });
        mainWindow.webContents.send('click-through-changed', isClickThrough);
      }},
      { label: 'Always on Top', type: 'checkbox', checked: store.get('alwaysOnTop'), click: (item) => {
        store.set('alwaysOnTop', item.checked); mainWindow.setAlwaysOnTop(item.checked);
      }},
      { type: 'separator' },
      { label: 'Reset Position', click: () => {
        const { width: sw, height: sh } = screen.getPrimaryDisplay().workAreaSize;
        mainWindow.setBounds({ width: 420, height: sh - 40, x: sw - 440, y: 20 });
      }},
      { type: 'separator' },
      { label: 'Quit Peter', click: () => { if (espWindow) espWindow.close(); app.quit(); } },
    ]);
    tray.setToolTip('AI-IN Peter');
    tray.setContextMenu(menu);
  } catch (e) { console.log('Tray icon not found, skipping'); }
}

function registerShortcuts() {
  globalShortcut.register('CommandOrControl+Shift+P', () => mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show());
  globalShortcut.register('CommandOrControl+Shift+E', () => {
    if (espWindow) espWindow.isVisible() ? espWindow.hide() : espWindow.show();
  });
  globalShortcut.register('CommandOrControl+Shift+C', () => openCalibration());
  globalShortcut.register('CommandOrControl+Shift+T', () => {
    isClickThrough = !isClickThrough;
    mainWindow.setIgnoreMouseEvents(isClickThrough, { forward: true });
    mainWindow.webContents.send('click-through-changed', isClickThrough);
  });
}

ipcMain.handle('get-settings', () => ({
  opacity: store.get('opacity'), alwaysOnTop: store.get('alwaysOnTop'),
  clickThrough: isClickThrough, position: store.get('position'),
}));
ipcMain.handle('set-opacity', (_, v) => { store.set('opacity', v); mainWindow.setOpacity(v); });
ipcMain.handle('set-click-through', (_, v) => { isClickThrough = v; mainWindow.setIgnoreMouseEvents(v, { forward: true }); });

app.whenReady().then(() => { createWindow(); createEspWindow(); registerShortcuts(); createTray(); });
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
app.on('will-quit', () => globalShortcut.unregisterAll());
app.on('activate', () => { if (mainWindow === null) createWindow(); });
