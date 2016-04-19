import asyncio

FIRST_COMPLETED = 'FIRST_COMPLETED'
ALL_COMPLETED = 'ALL_COMPLETED'


class AsyncZip:
    """Aggregates asynchronous iterables, like `zip` or `select`.

    The current state is stored in `self.iterating` as the `__anext__()`
    coroutine.

    When a `__anext__()` is done, we're immediatly replacing it with:
    self.iterating[i] = asyncio.ensure_future(
        self.asynchronous_iterators[i].__anext__(),
        loop=self._loop)

    There is no option to ask `AsyncZip` to stop iterating to the
    shortest iterable, just break yourself when you see an iterable is
    exhausted (having `done()` to `True` and `exception()` to
    `StopAsyncIteration`).
    """
    def __init__(self, *asynchronous_iterables, loop=None,
                 yield_when=FIRST_COMPLETED):
        """yield_when can take two values:

        - ALL_COMPLETED: Like `zip`, to get values from each iterables
          for each iterations.
        - FIRST_COMPLETED: Like `select`, to get values as soon as
          possible, so basically one value per iteration (the
          others in a pending state).
        """
        self.yield_when = yield_when
        if loop is not None:
            self._loop = loop
        else:
            self._loop = asyncio.events.get_event_loop()
        self.asynchronous_iterables = asynchronous_iterables
        self.asynchronous_iterators = []
        self.iterating = []

    async def __aiter__(self):
        self.asynchronous_iterators = []
        for iterable in self.asynchronous_iterables:
            self.asynchronous_iterators.append(await iterable.__aiter__())
        self.iterating = [asyncio.ensure_future(iterator.__anext__(),
                                                loop=self._loop)
                          for iterator in self.asynchronous_iterators]
        return self

    def should_wait(self):
        if all(f.done() and isinstance(f.exception(), StopAsyncIteration) for
               f in self.iterating):
            return False
        if self.yield_when == FIRST_COMPLETED:
            return not any(f.done() and
                           not isinstance(f.exception(), StopAsyncIteration) for
                           f in self.iterating)
        if self.yield_when == ALL_COMPLETED:
            return not all(f.done() and
                           not isinstance(f.exception(), StopAsyncIteration) for
                           f in self.iterating)

    async def __anext__(self):
        waiter = asyncio.futures.Future(loop=self._loop)
        counter = 0
        def _on_completion(f):
            nonlocal counter
            counter -= 1
            if self.yield_when == FIRST_COMPLETED or counter <= 0:
                if not waiter.done():
                    waiter.set_result(None)

        listenning_for = set()
        for i, f in enumerate(self.iterating):
            # Skip already empty iterators
            if f.done() and isinstance(f.exception(), StopAsyncIteration):
                continue
            counter += 1
            listenning_for.add(i)
            f.add_done_callback(_on_completion)

        if self.should_wait():
            await waiter

        results = []
        stop_async_iterations = 0
        for i, f in enumerate(self.iterating):
            results.append(f)
            if i not in listenning_for:
                stop_async_iterations += 1
                continue
            f.remove_done_callback(_on_completion)
            if f.done() and isinstance(f.exception(), StopAsyncIteration):
                stop_async_iterations += 1
            elif f.done():
                self.iterating[i] = asyncio.ensure_future(
                    self.asynchronous_iterators[i].__anext__(),
                    loop=self._loop)
        if stop_async_iterations == len(self.iterating):
            raise StopAsyncIteration
        return results


if __name__ == '__main__':
    class DummyAsyncIterable:
        def __init__(self, items, latency=0):
            self.items = items
            self.latency = latency

        async def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                if self.latency != 0:
                    await asyncio.sleep(self.latency)
                return self.items.pop(0)
            except IndexError:
                raise StopAsyncIteration


    def _repr_task(task):
        """Just give:
         - . if it's a StopAsyncIteration,
         - ~ if waiting
         - ? if another exception
         - the result otherwise
        """
        if task.done() and isinstance(task.exception(), StopAsyncIteration):
            return '.'
        if task.done() and isinstance(task.exception(), Exception):
            print(type(task.exception()))
            return '?'
        if task.done():
            return task.result()
        return '~'


    async def test_AsyncZip(listA, listB, listC, lag, yield_when,
                            expect):
        got = []
        async for items in AsyncZip(DummyAsyncIterable(list(listA[0]),
                                                       listA[1]),
                                    DummyAsyncIterable(list(listB[0]),
                                                       listB[1]),
                                    DummyAsyncIterable(list(listC[0]),
                                                       listC[1]),
                                    yield_when=yield_when):
            got.append(''.join(_repr_task(task) for task in items))
            await asyncio.sleep(lag)
        print(', '.join(got))
        assert(', '.join(got) == expect)


    asyncio.get_event_loop().run_until_complete(test_AsyncZip(
        ('123', 0), ('abcd', .1), ('ABCD', .25), .01, FIRST_COMPLETED,
        '1~~, 2~~, 3~~, .a~, .b~, .~A, .c~, .d~, .~B, ..C, ..D'))

    asyncio.get_event_loop().run_until_complete(test_AsyncZip(
        ('123', 0), ('abcd', .1), ('ABCD', .25), .47, FIRST_COMPLETED,
        '1~~, 2aA, 3bB, .cC, .dD'))

    asyncio.get_event_loop().run_until_complete(test_AsyncZip(
        ('123', 0), ('abcd', .1), ('ABCD', .3), .2, FIRST_COMPLETED,
        '1~~, 2a~, 3bA, .c~, .dB, ..C, ..D'))

    asyncio.get_event_loop().run_until_complete(test_AsyncZip(
        ('123', 0), ('abcd', .3), ('ABCD', .1), .2, FIRST_COMPLETED,
        '1~~, 2~A, 3aB, .~C, .bD, .c., .d.'))

    asyncio.get_event_loop().run_until_complete(test_AsyncZip(
        ('123', 0), ('abcd', .1), ('ABCD', .25), .01, ALL_COMPLETED,
        '1aA, 2bB, 3cC, .dD'))

    asyncio.get_event_loop().run_until_complete(test_AsyncZip(
        ('12', 0), ('abcd', .1), ('ABCDE', .25), .01, ALL_COMPLETED,
        '1aA, 2bB, .cC, .dD, ..E'))

    asyncio.get_event_loop().run_until_complete(test_AsyncZip(
        ('12', 0), ('abcd', .1), ('ABCDE', .25), .21, ALL_COMPLETED,
        '1aA, 2bB, .cC, .dD, ..E'))
