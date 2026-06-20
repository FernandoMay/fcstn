import json, time, logging, threading, os
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class LogEntry:
    timestamp: float
    level: str
    source: str
    message: str
    data: dict = field(default_factory=dict)

class RingLogger:
    def __init__(self, capacity=2000):
        self._entries = deque(maxlen=capacity)
        self._lock = threading.Lock()
        self._listeners = []

    def log(self, level, source, message, data=None):
        entry = LogEntry(
            timestamp=time.time(),
            level=level,
            source=source,
            message=message,
            data=data or {},
        )
        with self._lock:
            self._entries.append(entry)
        for cb in self._listeners:
            try:
                cb(entry)
            except Exception:
                pass

    def info(self, source, message, data=None):
        self.log("INFO", source, message, data)

    def warn(self, source, message, data=None):
        self.log("WARN", source, message, data)

    def error(self, source, message, data=None):
        self.log("ERROR", source, message, data)

    def debug(self, source, message, data=None):
        self.log("DEBUG", source, message, data)

    def recent(self, n=100, level=None):
        with self._lock:
            entries = list(self._entries)
        if level:
            entries = [e for e in entries if e.level == level]
        return entries[-n:]

    def to_dict_list(self, n=100):
        return [asdict(e) for e in self.recent(n)]

    def on_log(self, callback):
        self._listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

ROOT_LOG = RingLogger(capacity=2000)

def get_logger(source):
    class _Logger:
        def info(self, msg, data=None):
            ROOT_LOG.info(source, msg, data)
            logging.info(f"[{source}] {msg}")
        def warn(self, msg, data=None):
            ROOT_LOG.warn(source, msg, data)
            logging.warning(f"[{source}] {msg}")
        def error(self, msg, data=None):
            ROOT_LOG.error(source, msg, data)
            logging.error(f"[{source}] {msg}")
        def debug(self, msg, data=None):
            ROOT_LOG.debug(source, msg, data)
            logging.debug(f"[{source}] {msg}")
    return _Logger()
