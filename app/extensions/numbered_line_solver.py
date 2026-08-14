from __future__ import annotations

import base64
import zlib
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


_TEMPLATE_COUNT = 18
# Three 20x20 medoid glyphs per digit cover dark and translucent circle renderings. The
# compressed payload contains only normalized digit masks, not challenge screenshots.
_TEMPLATE_BLOB = (
    "eNq1WXdUU1kaf6lASEJIIgkkFClKEQRGQKQGJKiUKFUZigoqMAtSVERFWEFAEBAVcJCxgCKdGQVWcBRQ6RaK"
    "siCKsjq2tYyOurO7s5sJzi659yZ73Dnq+4e83/ne/Xq74HA4PB5PIBCIRCKJRCKTydgHHxzyTjfmkGCEQAs6"
    "4suEP5m7efTFVnWQSsUpquTWi1Q+iLGcRZ7ZvTt0QAxPwDBB/VZdVA7H8ggNFHOu+YqPYu7t6foo5jV4wFg"
    "GG9pniGJBY8UydGHDZaYo5lm9W+ZbvVXOTBQjs6gEeebEYZ/3kXM+WVEGcsnfrkcEAUVNr1Pi4cUQpebq8m"
    "7xgLMCiBkEJKT3N9hAwUPj6ehmHxXKcIk8ukIJxZJOeSIYjrav0Q35Fs/95pwIoSOoH7+8koJgGhWX/RGMq"
    "FfXvRzlQV0k0CD8n+b6pA/deIECwo+QdKtVCyJie0R2iZ/DYT8/J79yaoIHYfOilwjyz6lBGIlKVknq4KA6"
    "qeVf50qB31Q3b7wrTSOCwnvVrc8+4KHWMGu8z0P1MG58ooliVu2vtFBM0PNE5lub2n4uiqlaOSl8qvTAyXU"
    "mXctyoRETAjWWbzpSkx+uB5am1W0XGhsu3So2l2LKwmRvW0u/7omNQESqvjdxzuNCGQ+n39yNykOp7VuLkK"
    "klXEuZBUOz4prSZyNk6+rT0HhxP5KhgYcg1bCyPGskE9bdu7fHzsxyEaCcziHx7eJteWmZItAZudtDQ6Nd+"
    "WAhJ2vzuXxtlQ/b9Hc6hABB2m6ha1ezIEJ+1s13v4jjMJKUi1bWP+4XZU+KG+dLJWR5pa3S1bTte51CB2L6"
    "vU22vG1XQ9nvfHEBxUjVT5LpiN+2Xy3iwHYl+Y1+o4eovKik0QpEJD+d96XORtQNqdvDg81FdB0VV1tZuHl"
    "aSGulTsadv904eaCqOo4mFcMhITluU66TAk0qC57K5XJnmyrKMz/uczYMMpunpanOBCMQb1Xz8O+vx0oXAdj"
    "cvaON2/YMPCriST2sHxU/TxKrA4M+SujJ6QNRVJRrcgtcyyW0esfr7ZGaYJzXtImFh6A5af2ZSNVhJlzKmo"
    "do5F+yBW7nRE331DVkKCYxzoaLZU5ULtQsjI79U3zn+5ElIMawD4oI9gsBZxW8zI/fb3EoqvCmAjcrdQjEO"
    "xWf762Ph7TdMXGp+sz1G/WW4Hi0Vmhtuar8dZQMC58fEpEygan5VS6FZdExCDkcBs1ryl4dd5/2wf2ItuxE"
    "19A5Pyaqh8mWzgSWzEA0MBIqo+4PD4KAtBIZsLjzo58VAYNdSs/BuC0tD0+bgUZY80786uq+ORBbdmhkmLs"
    "BZCvCR6QHAZOtV5j+Og9rO98wLnhi4LPabekXxbFgHPDMOTSCSc+1YCDUfouJlok/oJxMjmWYQFOXhrHvzj"
    "RdkAfJvvaFeGonB9JEK3pXTulJf2XI9pI30wM1gSgP4pd3jqO2J8Q8rwbGCC87NsZZO/Z0CzDWVjZnxOd1T"
    "OYAXrcuudHd21sbwQBkITPVJbWJrYyXV0A+9zCF8lDi8DX56ixokPXse/72+Z8r5wKEzMyfmjbF1/9YC/TM"
    "WYE7JKP9ohvibJSBcunTXBRTqG8RQe92vht25CxThiaagu4Hk+lUqCCoFl7ubS1zgmdbVQ5df297jIxOXrcr"
    "ZepLwLs2UF91VTrZ6MzPBQDmPVywtbBLHA+y0A1xshL4h7EBG8iN8Y/fLfAyEMvOTWbY83v2TIScY/+9WPw"
    "lTMXY1d/70g/u0eHbvkoeXg5hRseFtIirK8DTDP7oTcb8e0A6auRhEkb1OO8BYLG1URRMxb/NE9gV2m9Jvu"
    "JlXJOWK4r/K3F7YdKBKy/7Imj/UU/BIaf2UN72gq7X5wPoOMgWvOzJZai+Bgf/uhLFaJYiLXnmJHyEK1Dj4"
    "+n6FJSQ4XlAgGJzK96V6cHQnNgzkpELxtanh48fmgttkmbxbpSGdG1ois1fijErkjTA8dcrdz7GOrEN2BiI"
    "SzIclDD60RygUQvKqyRDtcaRE4CTsn4Z3+i4ILDtSgp/xjIpY61HVwuT7z7abzozEy5YKQqx1faZGoriIqVf"
    "tXM/OlRj7AY/2a3YhiXPqPjPVKuAoKYSUTLi1vU6CMTcNHXSHM2jcXGLJQyZ7+r6qQKmI29IEFQULAQPw60"
    "P41PjctxBMsvDjphieI43eNj2WF2MGpMLBLTOpkP6kvhPKBACO8qN4Vjbed51zUlmM/6IHRtv3uq3efBJt3T"
    "OtkzI3bPGVtQx2b5tBiPTGAxljFcXTKIjlsZb01GTfTp/yO1RFL6hqfE8IwbIInzw4ejIg/EkcIn9+l9dG5"
    "bHpSwEc6tseLrxkqDzsuoWEFHG6efDZITJnGjKycsI4IO6Lk3dmVZzsycRvefSzL59dbFMfUl7GgOrJ8m5O"
    "PHemYzBKWgwJH9Mix5L6fAMGytVpuHm5nxDsM24tjUN3m2Ao4rrszwo0BbSBf+JW7xchxCoHD5PncsCb4M4"
    "UV0vn4xcPwIWMcu6yfHW6pb9jgDm2loQYG7uZAM2H7c6b/SSAVvWvp4mc794ofNgdJADhFmU919qOXs20QA"
    "o0LrrI9YkHJt6lU+TCk2kKisrcT0aD6rhUY1yTpmTUGz3t8COQ2YyaBSmSVqaoXTX/aI4NyEyo90X3InVX"
    "BwszRatUPtE+wde3iyg5hEaGLAuDhy0scWT4rvX34iDoTvW4d5Egc8qqJc5n3KgkxQVoVYW1KiNyjcr6y+7"
    "TZXYDJBOd+/9i5XllbnaQBwoLM7asSGxcqzOCQgSsq4mjbWs7t+nCEjk4FzvDFug19J6F2/O3Ef+92C7K9"
    "+pzDDRdhM5LbAJPn0tWkrgUnWrvercw7dFoBHsK7p6ek77qIGhqzDfRbjYSkGuTT8mGeChmm1kLxTAV0ack"
    "PTy5mro6kd313dfx4evAdsHLvxyrI0mhwumkWl+NQflEXo0mo6nUymg7Bm9WyxEiRsCwNnx5M97dNhLM1tj"
    "AWGaxYlKGM7n9lV/KdYw5SFZpVWa32RKsZKRYMmUzCh8UQTs/oO5ksNxlW/ygM2obETEn73yZp0dYALBYGV"
    "CRlfvQmgp1glM3rfHQwW2PcvIYo7Sh5bsz/Ioc7hcpiLEhRjSdaW/2BUwP0Fz58Bg0+nNXAIQ0PFjnYGODt"
    "qgiDqtfxIi5/M2dsrMLhblV3xorqEifSCT7DvvpQpijjcVekjj0mXoaZa1MKbt8RkukL99SzAFsvD8PWnNXz"
    "JQNT1CUEvfSVuDbc3J6XHQuO1naSvkx7X6YhRCYAd4v/bF5QspYdFmVDVAGCUXT1tjc4q8e8SP8Qce8a+6"
    "uT0DpqAYh5d8K4TICImHT9RU7LIF0yj6WpH7wgWWYJN36W1wQwUMv+Ms8R2U2tz9o1yMpM4G6UwbfvSd7V"
    "tanQr8s8ix41WgvnvuwMMMKbbi+ih7emMbu2g401tDxkfe+6Z0KGxmm3Tpe0Sbrs15E5Ez92aUvDfTUxmvo"
    "9eEBFy2V7lgujk3UsHFx6vxXO3poSDYLHZe3l7eKvKM/78L169JoPSG"
)

_SUPPORTED_LAYOUTS = ((5, 4), (6, 3))
_MAX_TEMPLATE_SCORE = 0.24


@dataclass(frozen=True)
class NumberedDragSolution:
    start: tuple[int, int]
    end: tuple[int, int]
    source_label: int
    digit_count: int
    score: float


def _load_templates() -> dict[int, list[np.ndarray]]:
    raw = zlib.decompress(base64.b64decode(_TEMPLATE_BLOB))
    labels = raw[:_TEMPLATE_COUNT]
    images = np.frombuffer(raw[_TEMPLATE_COUNT:], dtype=np.uint8).reshape(_TEMPLATE_COUNT, 20, 20)
    templates: dict[int, list[np.ndarray]] = {label: [] for label in range(1, 7)}
    for label, image in zip(labels, images):
        templates[int(label)].append(image)
    return templates


_DIGIT_TEMPLATES = _load_templates()


def _digit_glyph(image: np.ndarray, x: int, y: int) -> np.ndarray:
    radius = 7
    crop = image[y - radius : y + radius + 1, x - radius : x + radius + 1]
    if crop.shape[:2] != (15, 15):
        return np.zeros((20, 20), dtype=np.uint8)

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).astype(np.float32)
    yy, xx = np.indices(gray.shape)
    center = (gray.shape[0] - 1) / 2
    mask = (xx - center) ** 2 + (yy - center) ** 2 <= 5.8**2
    background = cv2.GaussianBlur(gray, (0, 0), 1.8)
    response = np.maximum(gray - background, 0) * mask
    response[response < np.percentile(response[mask], 55)] = 0
    if np.max(response) > 0:
        response = response / np.max(response) * 255
    return cv2.resize(response.astype(np.uint8), (20, 20), interpolation=cv2.INTER_CUBIC)


def _template_distance(first: np.ndarray, second: np.ndarray) -> float:
    first_value = first.astype(float)
    second_value = second.astype(float)
    denominator = np.linalg.norm(first_value) * np.linalg.norm(second_value)
    return 1 - float(np.sum(first_value * second_value) / max(denominator, 1e-6))


def _detect_circles(image: np.ndarray) -> list[tuple[int, int, int]]:
    height = image.shape[0]
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(
        cv2.GaussianBlur(grayscale, (3, 3), 0),
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=20,
        param1=80,
        param2=18,
        minRadius=6,
        maxRadius=14,
    )
    if circles is None:
        return []
    return [
        (int(x), int(y), int(radius))
        for x, y, radius in np.round(circles[0]).astype(int)
        if y > height * 0.31
    ]


def _assign_layout(
    image: np.ndarray, candidates: list[tuple[int, int, int]], digit_count: int, source_label: int
) -> tuple[float, dict[int, tuple[int, int, int]]] | None:
    labels = list(range(1, digit_count + 1))
    glyphs = [_digit_glyph(image, x, y) for x, y, _radius in candidates]
    costs = np.array(
        [
            [
                min(_template_distance(glyph, template) for template in _DIGIT_TEMPLATES[label])
                for label in labels
            ]
            for glyph in glyphs
        ]
    )
    source_indices = [
        index for index, circle in enumerate(candidates) if circle[0] > image.shape[1] * 0.75
    ]
    fixed_indices = [
        index for index, circle in enumerate(candidates) if circle[0] <= image.shape[1] * 0.75
    ]
    fixed_labels = [label for label in labels if label != source_label]
    best: tuple[float, dict[int, int]] | None = None

    for source_index in source_indices:
        states: dict[int, tuple[float, dict[int, int]]] = {
            0: (float(costs[source_index, source_label - 1]), {})
        }
        for candidate_index in fixed_indices:
            updated = dict(states)
            for mask, (total, assignments) in states.items():
                for bit, label in enumerate(fixed_labels):
                    if mask & (1 << bit):
                        continue
                    next_mask = mask | (1 << bit)
                    next_total = total + float(costs[candidate_index, label - 1])
                    if next_mask not in updated or next_total < updated[next_mask][0]:
                        updated[next_mask] = (next_total, {**assignments, label: candidate_index})
            states = updated

        full_mask = (1 << len(fixed_labels)) - 1
        if full_mask not in states:
            continue
        total, assignments = states[full_mask]
        assignments = {**assignments, source_label: source_index}
        if best is None or total < best[0]:
            best = (total, assignments)

    if best is None:
        return None
    total, assignments = best
    return total / digit_count, {label: candidates[assignments[label]] for label in labels}


def solve_numbered_line_drag(
    challenge_screenshot: Path, challenge_bbox: dict[str, float]
) -> NumberedDragSolution | None:
    image = cv2.imread(str(challenge_screenshot))
    if image is None:
        return None

    candidates = _detect_circles(image)
    options = []
    for digit_count, source_label in _SUPPORTED_LAYOUTS:
        if len(candidates) < digit_count:
            continue
        assigned = _assign_layout(image, candidates, digit_count, source_label)
        if assigned:
            score, mapping = assigned
            options.append((score, digit_count, source_label, mapping))
    if not options:
        return None

    score, digit_count, source_label, mapping = min(options, key=lambda item: item[0])
    if score > _MAX_TEMPLATE_SCORE:
        return None

    source = mapping[source_label]
    previous = mapping[source_label - 1]
    following = mapping[source_label + 1]
    target = ((previous[0] + following[0]) / 2, (previous[1] + following[1]) / 2)
    height, width = image.shape[:2]
    scale_x = challenge_bbox["width"] / width
    scale_y = challenge_bbox["height"] / height

    def project(point: tuple[float, float]) -> tuple[int, int]:
        return (
            round(challenge_bbox["x"] + point[0] * scale_x),
            round(challenge_bbox["y"] + point[1] * scale_y),
        )

    start = project((source[0], source[1]))
    end = project(target)

    debug_image = image.copy()
    for label, (x, y, radius) in mapping.items():
        cv2.circle(debug_image, (x, y), radius + 4, (0, 0, 255), 2)
        cv2.putText(
            debug_image,
            str(label),
            (x + radius + 4, y - radius - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )
    target_local = (round(target[0]), round(target[1]))
    cv2.circle(debug_image, target_local, 6, (0, 255, 0), 2)
    cv2.arrowedLine(
        debug_image, (source[0], source[1]), target_local, (0, 255, 0), 2, tipLength=0.04
    )
    if challenge_screenshot.name.endswith("_challenge_view.png"):
        debug_name = challenge_screenshot.name.replace(
            "_challenge_view.png", "_numbered_solution.png"
        )
    else:
        debug_name = f"{challenge_screenshot.stem}_numbered_solution.png"
    debug_path = challenge_screenshot.with_name(debug_name)
    cv2.imwrite(str(debug_path), debug_image)

    return NumberedDragSolution(
        start=start, end=end, source_label=source_label, digit_count=digit_count, score=score
    )
