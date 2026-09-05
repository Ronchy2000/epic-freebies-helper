"use strict";

const path = require("node:path");
const root = process.env.EPIC_PLAYWRIGHT_DRIVER_ROOT;

if (root) {
  const { FFPage } = require(path.join(root, "lib/server/firefox/ffPage.js"));
  const original = FFPage.prototype._onNavigationCommitted;
  if (typeof original !== "function") {
    throw new Error("Unsupported Playwright Firefox navigation contract; update the frame guard");
  }

  FFPage.prototype._onNavigationCommitted = function (params) {
    // Firefox can deliver navigationCommitted after the checkout iframe was detached.
    // Passing that missing frame to FrameManager crashes the entire Node driver.
    // Upstream report: https://github.com/microsoft/playwright/issues/35570
    if (!this._page.frameManager.frame(params.frameId)) {
      process.stderr.write("[epic] Ignored late Firefox navigation for a detached frame\n");
      return;
    }
    return original.call(this, params);
  };
}
