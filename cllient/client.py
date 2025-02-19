import asyncio
import random
import aiohttp
import time


URLS = ["http://127.0.0.1:8003/", "http://127.0.0.1:8004/"]
names = ("Анастасия", "Дарья", "Глеб", "Виталий", "Иван", "Максим", "Вероника", "Андрей", "Наталья", "Владимир")


async def send_message(url, payload: dict):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            return await response.json()


async def send_request(url):
    name = random.choice(names)
    message = f"Сообщение от {name}!"
    payload = {"name": name, "message": message}
    response = await send_message(url, payload)
    return response


async def create_workers(number_of_requests: int):
    result = []
    for _ in range(number_of_requests):
        url = random.choice(URLS)
        res = await send_request(url)
        result.append(res)
    return result


async def main():
    total_requests = 5000
    start_time = time.perf_counter()
    tasks = [asyncio.create_task(create_workers(100)) for _ in range(50)]
    results = await asyncio.gather(*tasks)
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    throughput = total_requests / elapsed
    print(f"Время работы: {elapsed:.4f} секунд")
    print(f"Пропускная способность: {throughput:.2f} запросов/сек")

if __name__ == '__main__':
    asyncio.run(main())
