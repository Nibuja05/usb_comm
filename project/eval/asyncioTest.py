import asyncio
from concurrent.futures import ThreadPoolExecutor
import time


def testRequest(id: int):
	print("Test Start", id)
	time.sleep(1)
	print("Test End", id)
	return id * 10


async def testRequestAsync(count: int):

	results = []
	with ThreadPoolExecutor(max_workers=count) as executor:
		loop = asyncio.get_event_loop()
		tasks = [
			loop.run_in_executor(
				executor,
				testRequest,
				(id)
			)
			for id in range(count)
		]
		for response in await asyncio.gather(*tasks):
			results.append(response)
	return results


def main():
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)
	future = asyncio.ensure_future(testRequestAsync(20))
	loop.run_until_complete(future)
	poolList = future.result()

	print(poolList)


if __name__ == "__main__":
	main()
