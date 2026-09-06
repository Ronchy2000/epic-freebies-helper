"""Install the Firefox detached-frame guard in this process's Playwright drivers."""

import json
from pathlib import Path

from playwright._impl import _transport
from playwright._impl._driver import compute_driver_executable

_PRELOAD = Path(__file__).with_name("playwright_frame_guard.cjs")


def install_playwright_frame_guard() -> None:
    original = _transport.get_driver_env
    if getattr(original, "_epic_frame_guard", False):
        return

    def guarded_driver_env() -> dict:
        env = original().copy()
        _, entrypoint = compute_driver_executable()
        env["EPIC_PLAYWRIGHT_DRIVER_ROOT"] = str(Path(entrypoint).parent)
        preload_option = f"--require={json.dumps(_PRELOAD.as_posix())}"
        env["NODE_OPTIONS"] = f"{env.get('NODE_OPTIONS', '')} {preload_option}".strip()
        return env

    # Scope the preload to driver subprocesses, not the user's global Node environment.
    guarded_driver_env._epic_frame_guard = True
    _transport.get_driver_env = guarded_driver_env
