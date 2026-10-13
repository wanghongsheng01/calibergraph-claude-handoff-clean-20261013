"""Owned Popen handles only. No process enumeration or foreign PID inspection.

Control-plane lifecycle implementation; science remains gated on child RSS coverage.
The periodic RSS measurement is for this Python process ONLY (macOS ru_maxrss bytes).
"""
import math
import os
import resource
import signal
import subprocess
import threading
import time


class Stopped(RuntimeError):
    pass


class OwnedCase:
    def __init__(self, wall_seconds, self_rss_stop_bytes=1024**3, interval=.025):
        if not math.isfinite(wall_seconds) or wall_seconds <= 0:
            raise ValueError('positive finite wall_seconds required')
        if type(self_rss_stop_bytes) is not int or self_rss_stop_bytes <= 0:
            raise ValueError('positive integer RSS threshold required')
        self.wall_seconds, self.self_rss_stop_bytes = wall_seconds, self_rss_stop_bytes
        self.interval = interval
        self.handles = []
        self.events = []
        self.lock = threading.RLock()
        self.cleanup_lock = threading.Lock()
        self.done = threading.Event()
        self.reason = None
        self.closed = False
        self.cleanup_errors = []
        self.entered = False

    def event(self, kind, **data):
        with self.lock:
            self.events.append(dict(kind=kind, monotonic=time.monotonic(), **data))

    def __enter__(self):
        if self.entered:
            raise RuntimeError('OwnedCase is single-use')
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError('whole-case SIGALRM requires main thread')
        if threading.active_count() != 1:
            raise RuntimeError('owned signal contract requires an otherwise single-threaded host')
        if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
            raise RuntimeError('do not replace an existing alarm')
        self.entered = True
        self.started = time.monotonic()
        self.deadline = self.started + self.wall_seconds
        self.old_alarm = signal.getsignal(signal.SIGALRM)
        mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
        try:
            signal.signal(signal.SIGALRM, self.alarm)
            signal.setitimer(signal.ITIMER_REAL, self.wall_seconds)
            self.thread = threading.Thread(target=self.watch, name='owned-case-watch', daemon=True)
            # Inherit the blocked alarm in the only secondary thread.
            self.thread.start()
            signal.pthread_sigmask(signal.SIG_SETMASK, mask)
        except BaseException:
            # __exit__ is not invoked if __enter__ raises, including at unmask.
            signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
            try:
                self.closed = True
                self.done.set()
                signal.setitimer(signal.ITIMER_REAL, 0)
                if hasattr(self, 'thread') and self.thread.ident is not None:
                    self.thread.join(timeout=2)
                self.cleanup()
                if signal.SIGALRM in signal.sigpending():
                    signal.sigwait({signal.SIGALRM})
            finally:
                try:
                    signal.signal(signal.SIGALRM, self.old_alarm)
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, mask)
            raise
        return self

    def alarm(self, signum, frame):
        self.reason = self.reason or 'CASE_DEADLINE'
        raise Stopped(self.reason)

    def request_stop(self, reason):
        with self.lock:
            if self.reason is None:
                self.reason = reason
                self.event('stop', reason=reason)

    def checkpoint(self):
        if self.closed:
            raise Stopped('CASE_CLOSED')
        if time.monotonic() >= self.deadline:
            self.request_stop('CASE_DEADLINE')
        if self.reason:
            raise Stopped(self.reason)

    def spawn(self, argv, **kwargs):
        """Register actual handles without replacing earlier handles. shell is forbidden."""
        if not isinstance(argv, (list, tuple)) or not argv or kwargs.get('shell'):
            raise ValueError('explicit argv without shell required')
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError('spawn must run in the owning main thread')
        if any(t not in (threading.main_thread(), self.thread) for t in threading.enumerate()):
            raise RuntimeError('uncontrolled thread violates the owned signal contract')
        # Block the owned alarm during Popen+registration to close the main-thread race.
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
        try:
            with self.lock:
                self.checkpoint()
                proc = subprocess.Popen(argv, **kwargs)
                self.handles.append(proc)
                self.event('spawn', index=len(self.handles)-1, pid_for_logging_only=proc.pid)
                return proc
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)

    def sample_self(self):
        # Never switch this to RUSAGE_CHILDREN, ps, proc_pidinfo, task_for_pid, etc.
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self.event('self_rss_peak', bytes=peak)
        if peak > self.self_rss_stop_bytes:
            self.request_stop('SELF_RSS_SAMPLED_STOP')
        return peak

    def watch(self):
        try:
            while not self.done.is_set():
                self.sample_self()
                if time.monotonic() >= self.deadline:
                    self.request_stop('CASE_DEADLINE')
                if self.reason:
                    self.cleanup()
                    # Wake Python main-thread sleeps/reads after owned-child cleanup.
                    if not self.done.is_set():
                        os.kill(os.getpid(), signal.SIGALRM)
                    return
                self.done.wait(self.interval)
        except BaseException as error:
            self.cleanup_errors.append(type(error).__name__ + ': ' + str(error))
            self.request_stop('WATCHDOG_ERROR')
            if not self.done.is_set():
                os.kill(os.getpid(), signal.SIGALRM)

    def cleanup(self):
        # Only signal/reap live children represented by our Popen objects.
        with self.cleanup_lock:
            with self.lock:
                handles = list(self.handles)
            for proc in reversed(handles):
                try:
                    if proc.poll() is None:
                        proc.terminate()
                        self.event('terminate', pid_for_logging_only=proc.pid)
                except ProcessLookupError:
                    pass
                except BaseException as error:
                    self.cleanup_errors.append(repr(error))
            until = time.monotonic() + .15
            for proc in reversed(handles):
                try:
                    proc.wait(timeout=max(0, until-time.monotonic()))
                except subprocess.TimeoutExpired:
                    try:
                        try:
                            proc.kill()
                            self.event('kill', pid_for_logging_only=proc.pid)
                        except ProcessLookupError:
                            pass
                        proc.wait(timeout=1)
                    except BaseException as error:
                        self.cleanup_errors.append(repr(error))
                except BaseException as error:
                    self.cleanup_errors.append(repr(error))
                self.event('wait', pid_for_logging_only=proc.pid, returncode=proc.returncode)

    def __exit__(self, typ, value, tb):
        # Prevent deadline signals interrupting cleanup. No subsequent launches allowed.
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
        try:
            self.closed = True
            self.done.set()
            signal.setitimer(signal.ITIMER_REAL, 0)
            self.thread.join(timeout=2)
            if self.thread.is_alive():
                self.cleanup_errors.append('watchdog join unconfirmed')
            self.cleanup()
            for proc in self.handles:
                for stream in (proc.stdin, proc.stdout, proc.stderr):
                    if stream is not None:
                        try:
                            stream.close()
                        except BaseException as error:
                            self.cleanup_errors.append(repr(error))
        finally:
            try:
                signal.setitimer(signal.ITIMER_REAL, 0)
                # Consume our pending alarm before restoring caller's handler/mask.
                if signal.SIGALRM in signal.sigpending():
                    signal.sigwait({signal.SIGALRM})
            finally:
                try:
                    signal.signal(signal.SIGALRM, self.old_alarm)
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
        if self.cleanup_errors or any(p.returncode is None for p in self.handles):
            raise RuntimeError('owned process cleanup unconfirmed: ' + repr(self.cleanup_errors))
        if typ is None and self.reason:
            raise Stopped(self.reason)
        return False

    def receipt(self):
        return {'reason': self.reason, 'elapsed_s': time.monotonic()-self.started,
                'wall_seconds': self.wall_seconds,
                'handle_count': len(self.handles),
                'all_reaped': all(p.returncode is not None for p in self.handles),
                'returncodes': [p.returncode for p in self.handles],
                'cleanup_errors': self.cleanup_errors,
                'self_rss_stop_bytes': self.self_rss_stop_bytes,
                'rss_scope': 'own Python high-water RSS only; excludes all children',
                'events': self.events}


def science_admission():
    """Fail closed: native Z3 allocator accounting is NOT child RSS telemetry."""
    return {'admitted': False, 'reason': 'EXTERNAL_Z3_RSS_COVERAGE_UNAVAILABLE',
            'forbidden_process_probe_retried': False,
            'native_memory_parameter_substitutes_for_rss': False,
            'science_threshold_bytes': 1024**3}


def launch_scientific_z3(case, argv):
    admission = science_admission()
    if not admission['admitted']:
        raise Stopped(admission['reason'])
    return case.spawn(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
