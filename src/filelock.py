import os
import time
import errno

class FileLock:
    def __init__(self, lockfile, timeout=10):
        self.lockfile = lockfile
        self.timeout = timeout
        self.fd = None

    def acquire(self):
        start = time.time()
        while True:
            try:
                self.fd = os.open(self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(self.fd, str(os.getpid()).encode())
                return
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                if time.time() - start > self.timeout:
                    raise TimeoutError(f"Timeout waiting for lock: {self.lockfile}")
                time.sleep(0.1)

    def release(self):
        if self.fd:
            os.close(self.fd)
            os.unlink(self.lockfile)
            self.fd = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
