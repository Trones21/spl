# plugins/spl-adapter-drift/src/spl_adapter_drift/async_bridge.py
import asyncio, threading, concurrent.futures
from typing import Any, Awaitable, Callable

# Used so synchronous backends (IExecutionBackend) can call async DriftPy APIs safely.

class AsyncBridge:
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def run(self, coro: Awaitable[Any]) -> Any:
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result()

    def call_soon(self, fn: Callable, *args, **kwargs):
        self._loop.call_soon_threadsafe(fn, *args, **kwargs)

    def create_task(self, coro: Awaitable[Any]) -> concurrent.futures.Future:
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def stop(self):
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=1)
