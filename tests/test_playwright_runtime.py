import os
import shutil
import subprocess
from pathlib import Path

from playwright._impl import _transport
from playwright._impl._driver import compute_driver_executable, get_driver_env

import extensions.playwright_runtime as playwright_runtime
from extensions.playwright_runtime import install_playwright_frame_guard

_DRIVER_SCENARIO = """
const assert = require('node:assert/strict');
const path = require('node:path');
const root = process.env.EPIC_PLAYWRIGHT_DRIVER_ROOT;
const { FFPage } = require(path.join(root, 'lib/server/firefox/ffPage.js'));
const { FrameManager } = require(path.join(root, 'lib/server/frames.js'));
const manager = new FrameManager({ frameNavigatedToNewDocument() {} });
const page = Object.create(FFPage.prototype);
page._page = { frameManager: manager };
page._workers = new Map();
const params = { frameId: 'checkout', url: 'https://example.test/checkout', navigationId: 'doc' };

// Model a checkout frame that detached before its navigation event arrived.
manager._frames.set(params.frameId, {});
manager._frames.delete(params.frameId);
page._onNavigationCommitted(params);
assert.equal(manager.frame(params.frameId), null);

// Existing frames must still take the original navigation and worker-cleanup path.
let navigations = 0;
const frame = {
  childFrames: () => [],
  parentFrame: () => null,
  pendingDocument: () => undefined,
  setPendingDocument() {},
  _onClearLifecycle() {},
  emit() { navigations++; },
};
manager._frames.set(params.frameId, frame);
page._workers.set('worker', { frameId: params.frameId });
page._onWorkerDestroyed = ({ workerId }) => page._workers.delete(workerId);
page._onNavigationCommitted(params);
assert.equal(frame._url, params.url);
assert.equal(frame._currentDocument.documentId, 'doc');
assert.equal(page._workers.size, 0);
assert.equal(navigations, 1);

// The guard must not hide unrelated errors for a live frame.
frame.childFrames = () => { throw new Error('unrelated navigation failure'); };
assert.throws(() => page._onNavigationCommitted(params), /unrelated navigation failure/);
console.log('detached event ignored; live navigation and real errors preserved');
"""


def _run_driver_scenario(env):
    node, entrypoint = compute_driver_executable()
    env = {**env, "EPIC_PLAYWRIGHT_DRIVER_ROOT": str(Path(entrypoint).parent)}
    return subprocess.run(
        [node, "-e", _DRIVER_SCENARIO], env=env, capture_output=True, text=True, timeout=15
    )


def test_unguarded_driver_reproduces_reported_child_frames_crash():
    result = _run_driver_scenario(get_driver_env())

    assert result.returncode != 0
    assert "reading 'childFrames'" in result.stderr


def test_guard_handles_detached_navigation_without_masking_live_frame_errors(monkeypatch):
    monkeypatch.setattr(_transport, "get_driver_env", get_driver_env)
    install_playwright_frame_guard()

    result = _run_driver_scenario(_transport.get_driver_env())

    assert result.returncode == 0, result.stderr
    assert "detached event ignored" in result.stdout
    assert "Ignored late Firefox navigation" in result.stderr


def test_guard_is_driver_scoped_and_idempotent(monkeypatch):
    monkeypatch.setattr(_transport, "get_driver_env", get_driver_env)
    monkeypatch.setenv("NODE_OPTIONS", "--no-warnings")
    install_playwright_frame_guard()
    installed = _transport.get_driver_env
    install_playwright_frame_guard()

    env = _transport.get_driver_env()

    assert _transport.get_driver_env is installed
    assert os.environ["NODE_OPTIONS"] == "--no-warnings"
    assert env["NODE_OPTIONS"].startswith("--no-warnings --require=")
    assert env["NODE_OPTIONS"].count("playwright_frame_guard.cjs") == 1

    result = _run_driver_scenario(env)
    assert result.returncode == 0, result.stderr


def test_guard_preload_supports_workspace_paths_with_spaces(monkeypatch, tmp_path):
    preload = tmp_path / "workspace with spaces" / "playwright_frame_guard.cjs"
    preload.parent.mkdir()
    shutil.copyfile(playwright_runtime._PRELOAD, preload)
    monkeypatch.setattr(playwright_runtime, "_PRELOAD", preload)
    monkeypatch.setattr(_transport, "get_driver_env", get_driver_env)
    install_playwright_frame_guard()

    result = _run_driver_scenario(_transport.get_driver_env())

    assert result.returncode == 0, result.stderr
