from threading import Lock

from django.utils.functional import SimpleLazyObject, empty


class ThreadSafeLazyObject(SimpleLazyObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__["_lock"] = Lock()

    def _setup(self):
        with self._lock:
            # double-check locking
            if self._wrapped is empty:
                super()._setup()
