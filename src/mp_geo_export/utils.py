from __future__ import annotations

import csv
import io
import json
import sys
import time
from pathlib import Path
from typing import Iterable, Sequence

from rich.console import Console


def write_json(data: object, out_path: Path | None, pretty: bool) -> None:
    text = json.dumps(data, indent=2 if pretty else None)
    if out_path is None or str(out_path) == "-":
        sys.stdout.write(text + ("\n" if pretty else ""))
    else:
        Path(out_path).write_text(text)


def write_csv(rows: Iterable[Sequence[object]], headers: Sequence[str] | None, out_path: Path | None) -> None:
    file_handle = sys.stdout if (out_path is None or str(out_path) == "-") else open(out_path, "w", newline="")
    try:
        writer = csv.writer(file_handle)
        if headers:
            writer.writerow(headers)
        for row in rows:
            writer.writerow(list(row))
    finally:
        if file_handle is not sys.stdout:
            file_handle.close()


def console() -> Console:
    return Console()


class Timer:
    def __init__(self) -> None:
        self.elapsed: float = 0.0

    def __enter__(self) -> "Timer":
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc_info) -> None:  # type: ignore[no-untyped-def]
        self.end = time.perf_counter()
        self.elapsed = self.end - self.start


