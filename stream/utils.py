import logging
import asyncio
from asyncio.queues import Queue

log = logging.getLogger(__name__)
TERMINATOR = object()


def periodic(loop, delay, fn, *args, **kwargs):

    async def _worker():
        while True:
            await fn(*args, **kwargs)
            await asyncio.sleep(delay, loop=loop)

    return asyncio.ensure_future(_worker(), loop=loop)


class TaskPool(object):
    def __init__(self, loop, num_workers):
        self.loop = loop
        self.tasks = Queue(loop=self.loop)
        self.workers = []
        for _ in range(num_workers):
            worker = asyncio.ensure_future(self.worker(), loop=self.loop)
            self.workers.append(worker)

    async def worker(self):
        while True:
            future, task = await self.tasks.get()
            if task is TERMINATOR:
                break
            try:
                result = await asyncio.wait_for(task, None, loop=self.loop)
                future.set_result(result)
            except Exception as e:
                log.exception("task raised exception")
                future.set_exception(e)

    def submit(self, task):
        future = asyncio.Future(loop=self.loop)
        self.tasks.put_nowait((future, task))
        return future

    async def join(self):
        for _ in self.workers:
            self.tasks.put_nowait((None, TERMINATOR))
        await asyncio.gather(*self.workers, loop=self.loop)
