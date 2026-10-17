# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from pathlib import Path

class QueueLogHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            self.log_queue.put({"level": record.levelname, "message": self.format(record)})
        except Exception:
            self.handleError(record)

def configure_logger(log_queue):
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"reysearch_{datetime.now():%Y-%m-%d}.log"
    logger = logging.getLogger("reysearch")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
    fh = logging.FileHandler(path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    qh = QueueLogHandler(log_queue)
    qh.setFormatter(fmt)
    logger.addHandler(qh)
    return logger
