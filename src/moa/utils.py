from __future__ import annotations
import time
from typing import Iterable, Deque, TypeVar, Callable
from collections import deque

T = TypeVar("T")

def sliding_window(iterable: Iterable[T], maxlen: int) -> Deque[T]:
    d: Deque[T] = deque(maxlen=maxlen)
    for x in iterable:
        d.append(x)
        yield d

def now_ts() -> float:
    return time.time()
