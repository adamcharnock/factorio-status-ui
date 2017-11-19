import asyncio
import traceback


async def handle_aio_exceptions(coroutine):
    try:
        await coroutine
    except asyncio.CancelledError:
        pass
    except Exception:
        traceback.print_exc()
