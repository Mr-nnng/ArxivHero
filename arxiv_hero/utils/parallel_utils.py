import traceback
from typing import Callable
import concurrent.futures

from arxiv_hero import logger


def parallel_func(func: Callable, args: list[tuple], max_workers: int = 8):
    results = [None] * len(args)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures_map = {executor.submit(func, *arg): i for i, arg in enumerate(args)}
        for future in concurrent.futures.as_completed(futures_map):
            try:
                result = future.result()
                if result is not None:
                    results[futures_map[future]] = result
            except Exception as e:
                logger.warning(f"Error in parallel_func: {e}")
                logger.debug(
                    (
                        f"\nError in parallel_func: {e}"
                        "---------------------------------------------------------------------"
                        f"\nfunc: {func.__name__}"
                        f"\nargs: {args}"
                        f"\ntacktrace: {traceback.format_exc()}"
                        "\n-------------------------------------------------------------------"
                    )
                )
        return results
