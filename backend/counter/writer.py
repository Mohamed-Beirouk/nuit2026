import fcntl
import queue
import threading
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings
from django.db import close_old_connections, transaction
from django.db.models import F

_LOCK_PATH = Path(settings.BASE_DIR) / ".counter.lock"


@contextmanager
def _process_write_lock():
    """Block other processes. Threads in this process are already queued."""
    _LOCK_PATH.touch(exist_ok=True)
    with _LOCK_PATH.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class ClaimWriter:
    """One background thread applies every increment.

    SQLite allows a single writer. If each request wrote on its own thread,
    overlapping clicks would raise "database is locked". Requests only enqueue
    here and wait. The worker runs the update, then hands the saved number back.
    """

    def __init__(self):
        self._jobs = queue.Queue()
        self._thread = None
        self._start_lock = threading.Lock()

    def submit(self, name, timeout=30):
        self._ensure_started()
        done = queue.Queue(maxsize=1)
        self._jobs.put((name, done))
        try:
            status, payload = done.get(timeout=timeout)
        except queue.Empty as exc:
            raise TimeoutError("Timed out waiting for the counter.") from exc
        if status == "error":
            raise payload
        return payload

    def _ensure_started(self):
        with self._start_lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(
                    target=self._loop,
                    name="counter-writer",
                    daemon=True,
                )
                self._thread.start()

    def _loop(self):
        while True:
            name, done = self._jobs.get()
            try:
                close_old_connections()
                with _process_write_lock():
                    done.put(("ok", self._assign(name)))
            except Exception as exc:
                done.put(("error", exc))
            finally:
                close_old_connections()
                self._jobs.task_done()

    def _assign(self, name):
        from .models import Claim, Counter
        from .serializers import ClaimSerializer

        with transaction.atomic():
            Counter.objects.get_or_create(pk=1, defaults={"value": 0})
            Counter.objects.filter(pk=1).update(value=F("value") + 1)
            value = Counter.objects.values_list("value", flat=True).get(pk=1)
            claim = Claim.objects.create(name=name, number=value)
        return dict(ClaimSerializer(claim).data)


claim_writer = ClaimWriter()
