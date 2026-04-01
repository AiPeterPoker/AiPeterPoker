/**
 * Screen Reader — Client-side screenshot capture
 * Uses Electron's desktopCapturer or screenshot-desktop for screen capture.
 * Sends captured frames to the backend for vision processing.
 */

import wsManager from '../utils/websocket';

class ScreenReader {
  constructor() {
    this.isCapturing = false;
    this.interval = null;
    this.captureIntervalMs = 2000;
    this.targetWindow = null;
  }

  /**
   * Start capturing screenshots at the configured interval.
   * In practice, the Python backend handles capture via mss.
   * This client-side module manages the capture lifecycle and settings.
   */
  startCapture(intervalMs = 2000) {
    if (this.isCapturing) return;

    this.captureIntervalMs = intervalMs;
    this.isCapturing = true;

    // Tell backend to start its capture loop
    wsManager.send('start_capture', {
      interval: this.captureIntervalMs,
    });

    console.log(`[ScreenReader] Capture started (${intervalMs}ms interval)`);
  }

  /**
   * Stop screen capture.
   */
  stopCapture() {
    this.isCapturing = false;

    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }

    wsManager.send('stop_session');
    console.log('[ScreenReader] Capture stopped');
  }

  /**
   * Update capture settings.
   */
  updateSettings({ intervalMs, cropRegion }) {
    if (intervalMs) {
      this.captureIntervalMs = intervalMs;
    }

    wsManager.send('update_settings', {
      capture_interval: this.captureIntervalMs,
      crop_region: cropRegion || null,
    });
  }

  /**
   * Set the target window/region to capture.
   * Used when the user selects the game window area.
   */
  setTargetRegion(x, y, width, height) {
    this.targetWindow = { x, y, width, height };
    wsManager.send('update_settings', {
      crop_region: this.targetWindow,
    });
  }

  /**
   * Clear target region — capture full screen.
   */
  clearTargetRegion() {
    this.targetWindow = null;
    wsManager.send('update_settings', {
      crop_region: null,
    });
  }
}

const screenReader = new ScreenReader();
export default screenReader;
