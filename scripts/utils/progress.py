#!/usr/bin/env python3
from __future__ import annotations
import sys, time
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Step:
    name: str
    weight: float = 1.0


class ProgressETA:
    """Lightweight step-based progress/ETA helper for CLI scripts.

    Usage:
        pg = ProgressETA([('prepare/CV',5), ('fit/metrics',3), ('figures',2), ('html',1)])
        pg.start(total_hint_min=10)  # optional initial hint in minutes
        ... heavy step ...
        pg.tick('prepare/CV')
        ...
        pg.tick('fit/metrics')
    """

    def __init__(self, steps: List[Tuple[str, float]]):
        self.steps: List[Step] = [Step(n, float(w)) for n, w in steps]
        self._start_ts: float | None = None
        self._elapsed: float = 0.0
        self._done_weight: float = 0.0
        self._total_weight: float = sum(s.weight for s in self.steps) or 1.0
        self._last_step: str | None = None

    def start(self, total_hint_min: float | None = None) -> None:
        self._start_ts = time.time()
        if total_hint_min is not None:
            self._println(f"[progress] started; rough ETA ≈ {total_hint_min:.1f} min (hint)")
        else:
            self._println("[progress] started; ETA updates after first step completes")
        self._println(self._format_plan())

    def tick(self, name: str) -> None:
        now = time.time()
        if self._start_ts is None:
            self._start_ts = now
        step_weight = 0.0
        for s in self.steps:
            if s.name == name:
                step_weight = s.weight
                break
        self._done_weight += step_weight
        self._elapsed = now - self._start_ts
        eta_str = self._eta_string()
        self._last_step = name
        pct = 100.0 * (self._done_weight / self._total_weight)
        self._println(f"[progress] {pct:5.1f}% done — finished: {name} | elapsed {self._fmt(self._elapsed)}, ETA {eta_str}")

    def _eta_string(self) -> str:
        if self._done_weight <= 0 or self._elapsed <= 0:
            return "…"
        rate = self._elapsed / self._done_weight  # sec per weight
        remaining = max(self._total_weight - self._done_weight, 0.0)
        eta_sec = remaining * rate
        return self._fmt(eta_sec)

    @staticmethod
    def _fmt(sec: float) -> str:
        m, s = divmod(int(sec), 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}h{m:02d}m"
        if m:
            return f"{m}m{s:02d}s"
        return f"{s}s"

    def _format_plan(self) -> str:
        parts = [f"- {s.name} (w={s.weight:g})" for s in self.steps]
        return "[plan]\n" + "\n".join(parts) + f"\n[total weight={self._total_weight:g}]"

    @staticmethod
    def _println(msg: str) -> None:
        sys.stdout.write(msg + "\n"); sys.stdout.flush()

