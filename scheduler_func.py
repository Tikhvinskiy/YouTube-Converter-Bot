from pathlib import Path
import config
import asyncio
import aioschedule


async def rm_store(pth=Path(config.STORE)):
    for child in pth.glob('*'):
        if child.is_file():
            child.unlink()
        else:
            pass
            # rm_store(child) # to delete dir


async def scheduler():
    aioschedule.every(24).hours.do(rm_store)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(20)