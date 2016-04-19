# AsyncZip

`AsyncZip` is a simple `zip` like function working with asynchronous
iterables. It look, in many aspects, like `asyncio.wait`.

## Usage

Given *n* asynchronous iterables, `AsyncZip(*aiterables)` gives a new
asynchronous iterable iterating over all of them. Like `asyncio.wait`,
it's possible to wait for any iterable to yield something using the
option `FIRST_COMPLETED`, or to wait for all of them using the option
`ALL_COMPLETED`.

## class AsyncZip

    def __init__(self, *asynchronous_iterables, loop=None,
                 yield_when=FIRST_COMPLETED):

 - asynchronous_iterables: A collection of asynchronous iterables
 - loop: Optional named parameter, to give an specific event loop
 - yield_when: Like `return_when` from `asyncio.wait`,
   `FIRST_COMPLETED` or `ALL_COMPLETED`.

## FIRST_COMPLETED, ALL_COMPLETED

The two values `yield_when` can take, `FIRST_COMPLETED` and
`ALL_COMPLETED` tell, like for `asyncio.wait`, when `AsyncZip` should
yield. Defaults to FIRST_COMPLETED.

### FIRST_COMPLETED

Like `select`, where `AsyncZip` yields each time any iterable yields,
as soon as possible.

### ALL_COMPLETED

It's the classical `zip` mode, where `AsyncZip` waits for a value for
each iterator before yielding them all in a single loop.

## Example usage

    import asyncio
    from asynczip import AsyncZip

    class DummyAsyncIterable:
        def __init__(self, items):
            self.items = items

        async def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return self.items.pop(0)
            except IndexError:
                raise StopAsyncIteration

    async def test():
        async for items in AsyncZip(DummyAsyncIterable(list("foo")),
                                    DummyAsyncIterable(list("bar"))):
            print(items)

    asyncio.get_event_loop().run_until_complete(test())

Gives:

    [<Task finished coro=<DummyAsyncIterable.__anext__() done, defined at test.py:11> result='f'>,<Task finished coro=<DummyAsyncIterable.__anext__() done, defined at test.py:11> result='b'>]
    [<Task finished coro=<DummyAsyncIterable.__anext__() done, defined at test.py:11> result='o'>, <Task finished coro=<DummyAsyncIterable.__anext__() done, defined at test.py:11> result='a'>]
    [<Task finished coro=<DummyAsyncIterable.__anext__() done, defined at test.py:11> result='o'>, <Task finished coro=<DummyAsyncIterable.__anext__() done, defined at test.py:11> result='r'>]
