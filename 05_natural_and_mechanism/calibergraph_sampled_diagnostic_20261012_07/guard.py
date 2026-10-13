"""Owned-process RSS sampling, lifetime channel and CPU budget (macOS only)."""
import fcntl
import json
import os
import resource
import select
import threading
import time


class Guard:
    def __init__(self, lock_fd, telemetry_fd, lifetime_fd, threshold, interval=0.05):
        self.fd, self.life = telemetry_fd, lifetime_fd
        self.threshold, self.interval = threshold, interval
        self.done = threading.Event()
        self.lock = threading.Lock()
        resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        self.send(kind="ready", pid=os.getpid(), threshold=threshold, interval=interval,
                  inherited_lock_inode=os.fstat(lock_fd).st_ino,
                  cpu_limit=resource.getrlimit(resource.RLIMIT_CPU))
        self.sample()
        self.thread = threading.Thread(target=self.watch, daemon=True)
        self.thread.start()

    def send(self, **event):
        event["t"] = time.monotonic()
        data = (json.dumps(event) + "\n").encode()
        try:
            with self.lock:
                os.write(self.fd, data)
        except OSError:
            os._exit(90)  # parent gone; no unmonitored continuation

    def sample(self):
        used = resource.getrusage(resource.RUSAGE_SELF)
        peak = used.ru_maxrss
        self.send(kind="rss", rss=peak, cpu_s=used.ru_utime + used.ru_stime)
        if peak > self.threshold:
            self.send(kind="memory_stop", rss=peak)
            os._exit(86)

    def watch(self):
        while not self.done.is_set():
            readable, _, _ = select.select([self.life], [], [], self.interval)
            if readable and not os.read(self.life, 1):
                os._exit(90)
            self.sample()

    def finish(self):
        self.sample()
        self.done.set()
        self.thread.join(timeout=0.2)


def check_contender(lock_path):
    with open(lock_path, "a") as contender:
        try:
            fcntl.flock(contender.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        raise RuntimeError("Lock exclusion failed")
