from pathlib import Path

import numpy as np

import extensions.numbered_line_solver as numbered_line_solver


def test_solver_projects_source_and_neighbor_midpoint(monkeypatch, tmp_path):
    image = np.zeros((200, 1000, 3), dtype=np.uint8)
    mapping = {
        1: (100, 90, 8),
        2: (200, 100, 8),
        3: (300, 80, 8),
        4: (900, 100, 8),
        5: (500, 120, 8),
    }
    written_paths: list[Path] = []

    monkeypatch.setattr(numbered_line_solver.cv2, "imread", lambda _path: image)
    monkeypatch.setattr(
        numbered_line_solver, "_detect_circles", lambda _image: list(mapping.values())
    )

    def assign_layout(_image, _candidates, digit_count, source_label):
        if (digit_count, source_label) == (5, 4):
            return 0.1, mapping
        return None

    monkeypatch.setattr(numbered_line_solver, "_assign_layout", assign_layout)
    monkeypatch.setattr(
        numbered_line_solver.cv2,
        "imwrite",
        lambda path, _image: written_paths.append(Path(path)) or True,
    )

    screenshot = tmp_path / "challenge.png"
    solution = numbered_line_solver.solve_numbered_line_drag(
        screenshot, {"x": 100.0, "y": 200.0, "width": 500.0, "height": 100.0}
    )

    assert solution is not None
    assert solution.start == (550, 250)
    assert solution.end == (300, 250)
    assert solution.source_label == 4
    assert solution.digit_count == 5
    assert written_paths == [tmp_path / "challenge_numbered_solution.png"]


def test_solver_falls_back_when_template_score_is_too_high(monkeypatch, tmp_path):
    image = np.zeros((200, 1000, 3), dtype=np.uint8)
    mapping = {
        1: (100, 90, 8),
        2: (200, 100, 8),
        3: (300, 80, 8),
        4: (900, 100, 8),
        5: (500, 120, 8),
    }

    monkeypatch.setattr(numbered_line_solver.cv2, "imread", lambda _path: image)
    monkeypatch.setattr(
        numbered_line_solver, "_detect_circles", lambda _image: list(mapping.values())
    )
    monkeypatch.setattr(
        numbered_line_solver,
        "_assign_layout",
        lambda _image, _candidates, digit_count, _source_label: (
            (numbered_line_solver._MAX_TEMPLATE_SCORE + 0.01, mapping) if digit_count == 5 else None
        ),
    )

    solution = numbered_line_solver.solve_numbered_line_drag(
        tmp_path / "challenge.png", {"x": 0.0, "y": 0.0, "width": 1000.0, "height": 200.0}
    )

    assert solution is None
