from colorama import *
from datetime import datetime, timedelta
from fake_useragent import FakeUserAgent
from faker import Faker
import aiohttp
import asyncio
import json
import os
import re
import sys

class Major:
    def __init__(self) -> None:
        self.faker = Faker()
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Host': 'major.bot',
            'Pragma': 'no-cache',
            'Referer': 'https://major.bot/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': FakeUserAgent().random
        }

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_timestamp(self, message):
        print(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{message}",
            flush=True
        )

    def load_queries(self, file_path):
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if line.strip()]

    def process_queries(self, lines_per_file: int):
        if not os.path.exists('queries.txt'):
            raise FileNotFoundError(f"File 'queries.txt' not found. Please ensure it exists.")

        with open('queries.txt', 'r') as f:
            queries = [line.strip() for line in f if line.strip()]
        if not queries:
            raise ValueError("File 'queries.txt' is empty.")

        existing_queries = set()
        for file in os.listdir():
            if file.startswith('queries-') and file.endswith('.txt'):
                with open(file, 'r') as qf:
                    existing_queries.update(line.strip() for line in qf if line.strip())

        new_queries = [query for query in queries if query not in existing_queries]
        if not new_queries:
            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ No New Queries To Add ]{Style.RESET_ALL}")
            return

        files = [f for f in os.listdir() if f.startswith('queries-') and f.endswith('.txt')]
        files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0)

        last_file_number = int(re.findall(r'\d+', files[-1])[0]) if files else 0

        for i in range(0, len(new_queries), lines_per_file):
            chunk = new_queries[i:i + lines_per_file]
            if files and len(open(files[-1], 'r').readlines()) < lines_per_file:
                with open(files[-1], 'a') as outfile:
                    outfile.write('\n'.join(chunk) + '\n')
                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Updated '{files[-1]}' ]{Style.RESET_ALL}")
            else:
                last_file_number += 1
                queries_file = f"queries-{last_file_number}.txt"
                with open(queries_file, 'w') as outfile:
                    outfile.write('\n'.join(chunk) + '\n')
                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Generated '{queries_file}' ]{Style.RESET_ALL}")

    async def tg_auth(self, queries: str):
        url = 'https://major.bot/api/auth/tg/'
        accounts = []
        for query in queries:
            data = json.dumps({'init_data':query})
            headers = {
                **self.headers,
                'Content-Length': str(len(data)),
                'Content-Type': 'application/json',
                'Origin': 'https://major.bot'
            }
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                    async with session.post(url, headers=headers, data=data) as response:
                        response.raise_for_status()
                        tg_auth = await response.json()
                        token = f"Bearer {tg_auth['access_token']}"
                        id = tg_auth['user']['id']
                        first_name = tg_auth['user']['first_name'] or self.faker.first_name()
                        accounts.append({'token': token, 'id': id, 'first_name': first_name})
            except (aiohttp.ClientResponseError, aiohttp.ContentTypeError, Exception) as e:
                self.print_timestamp(
                    f"{Fore.YELLOW + Style.BRIGHT}[ Failed To Process {query} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}"
                )
                continue
        return accounts

    async def visit(self, token: str, first_name: str):
        url = 'https://major.bot/api/user-visits/visit/'
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': '0',
            'Content-Type': 'application/json',
            'Origin': 'https://major.bot'
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers) as response:
                    if response.status in [500, 520]:
                        return self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Server Major Down ]{Style.RESET_ALL}"
                        )
                    response.raise_for_status()
                    visit = await response.json()
                    if visit['is_increased']:
                        if visit['is_allowed']:
                            return self.print_timestamp(
                                f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                                f"{Fore.GREEN + Style.BRIGHT}[ Claimed Daily Visit ]{Style.RESET_ALL}"
                            )
                        return self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Subscribe Major Community To Claim Your Daily Visit Bonus And Increase Your Streak ]{Style.RESET_ALL}"
                        )
                    return self.print_timestamp(
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.MAGENTA + Style.BRIGHT}[ Daily Visit Already Claimed ]{Style.RESET_ALL}"
                    )
        except aiohttp.ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An HTTP Error Occurred While Fetching Streak: {str(e.message)} ]{Style.RESET_ALL}")
        except (Exception, aiohttp.ContentTypeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An Unexpected Error Occurred While Daily Visit: {str(e)} ]{Style.RESET_ALL}")

    async def streak(self, token: str, first_name: str):
        url = 'https://major.bot/api/user-visits/streak/'
        headers = {
            **self.headers,
            'Authorization': token
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    if response.status in [500, 520]:
                        self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Server Major Down ]{Style.RESET_ALL}"
                        )
                        return None
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientResponseError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An HTTP Error Occurred While Fetching Streak: {str(e.message)} ]{Style.RESET_ALL}")
            return None
        except (Exception, aiohttp.ContentTypeError) as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An Unexpected Error Occurred While Fetching Streak: {str(e)} ]{Style.RESET_ALL}")
            return None

    async def user(self, token: str, id: str, first_name: str):
        url = f'https://major.bot/api/users/{id}/'
        headers = {
            **self.headers,
            'Authorization': token
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    if response.status in [500, 520]:
                        self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Server Major Down ]{Style.RESET_ALL}"
                        )
                        return None
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientResponseError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An HTTP Error Occurred While Fetching User: {str(e.message)} ]{Style.RESET_ALL}")
            return None
        except (Exception, aiohttp.ContentTypeError) as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An Unexpected Error Occurred While Fetching User: {str(e)} ]{Style.RESET_ALL}")
            return None

    async def squad(self, token: str, squad_id: int, first_name: str):
        url = f'https://major.bot/api/squads/{squad_id}'
        headers = {
            **self.headers,
            'Authorization': token
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    if response.status in [500, 520]:
                        return self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Server Major Down ]{Style.RESET_ALL}"
                        )
                    response.raise_for_status()
                    squad = await response.json()
                    return self.print_timestamp(
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.GREEN + Style.BRIGHT}[ Squad {squad['name']} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ Squad Rating {squad['rating']} ]{Style.RESET_ALL}"
                    )
        except aiohttp.ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An HTTP Error Occurred While Fetching Squad: {str(e.message)} ]{Style.RESET_ALL}")
        except (Exception, aiohttp.ContentTypeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An Unexpected Error Occurred While Fetching Squad: {str(e)} ]{Style.RESET_ALL}")

    async def join_squad(self, token: str, first_name: str):
        url = f'https://major.bot/api/squads/2226636853/join/'
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': '0',
            'Origin': 'https://major.bot'
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers) as response:
                    if response.status in [500, 520]:
                        return self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Server Major Down ]{Style.RESET_ALL}"
                        )
                    response.raise_for_status()
                    join_squad = await response.json()
                    if join_squad['status'] == 'ok':
                        return await self.squad(token=token, squad_id=2226636853, first_name=first_name)
        except aiohttp.ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An HTTP Error Occurred While Join Squad: {str(e.message)} ]{Style.RESET_ALL}")
        except (Exception, aiohttp.ContentTypeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An Unexpected Error Occurred While Join Squad: {str(e)} ]{Style.RESET_ALL}")

    async def leave_squad(self, token: str, first_name: str):
        url = f'https://major.bot/api/squads/leave/'
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': '0',
            'Origin': 'https://major.bot'
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers) as response:
                    if response.status in [500, 520]:
                        return self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Server Major Down ]{Style.RESET_ALL}"
                        )
                    response.raise_for_status()
                    leave_squad = await response.json()
                    if leave_squad['status'] == 'ok':
                        return await self.join_squad(token=token, first_name=first_name)
        except aiohttp.ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An HTTP Error Occurred While Leave Squad: {str(e.message)} ]{Style.RESET_ALL}")
        except (Exception, aiohttp.ContentTypeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An Unexpected Error Occurred While Leave Squad: {str(e)} ]{Style.RESET_ALL}")

    async def tasks(self, token: str, type: str, first_name: str):
        url = f'https://major.bot/api/tasks/?is_daily={type}'
        headers = {
            **self.headers,
            'Authorization': token
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    if response.status in [500, 520]:
                        self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Server Major Down ]{Style.RESET_ALL}"
                        )
                        return None
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientResponseError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An HTTP Error Occurred While Fetching Tasks: {str(e.message)} ]{Style.RESET_ALL}")
            return None
        except (Exception, aiohttp.ContentTypeError) as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An Unexpected Error Occurred While Fetching Tasks: {str(e)} ]{Style.RESET_ALL}")
            return None

    async def complete_task(self, token: str, first_name: str, task_id: int, task_title: str, task_award: int):
        url = 'https://major.bot/api/tasks/'
        data = json.dumps({'task_id':task_id})
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Origin': 'https://major.bot'
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    if response.status == 400: return
                    elif response.status in [500, 520]:
                        return self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Server Major Down ]{Style.RESET_ALL}"
                        )
                    response.raise_for_status()
                    complete_task = await response.json()
                    if complete_task['is_completed']:
                        return self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.GREEN + Style.BRIGHT}[ Got {task_award} From {task_title} ]{Style.RESET_ALL}"
                        )
        except aiohttp.ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An HTTP Error Occurred While Complete Tasks: {str(e.message)} ]{Style.RESET_ALL}")
        except (Exception, aiohttp.ContentTypeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An Unexpected Error Occurred While Complete Tasks: {str(e)} ]{Style.RESET_ALL}")

    async def get_choices_durov(self):
        url = 'https://raw.githubusercontent.com/GravelFire/TWFqb3JCb3RQdXp6bGVEdXJvdg/master/answer.py'
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.get(url=url) as response:
                    response.raise_for_status()
                    response_answer = json.loads(await response.text())
                    return response_answer.get('answer')
        except (aiohttp.ContentTypeError, aiohttp.ClientResponseError) as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Get Choices Durov: {str(e)} ]{Style.RESET_ALL}")
            return None
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Get Choices Durov: {str(e)} ]{Style.RESET_ALL}")
            return None

    async def durov(self, token: str, first_name: str):
        url = 'https://major.bot/api/durov/'
        data = json.dumps(await self.get_choices_durov())
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Origin': 'https://major.bot'
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    if response.status == 400:
                        error_coins = await response.json()
                        if 'detail' in error_coins:
                            if 'blocked_until' in error_coins['detail']:
                                return self.print_timestamp(
                                    f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                                    f"{Fore.YELLOW + Style.BRIGHT}[ Can Play Puzzle Durov At {datetime.fromtimestamp(error_coins['detail']['blocked_until']).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                                )
                    elif response.status in [500, 520]:
                        return self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Server Major Down ]{Style.RESET_ALL}"
                        )
                    response.raise_for_status()
                    return self.print_timestamp(
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.GREEN + Style.BRIGHT}[ Got 5000 From Puzzle Durov ]{Style.RESET_ALL}"
                    )
        except aiohttp.ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An HTTP Error Occurred While Play Durov: {str(e.message)} ]{Style.RESET_ALL}")
        except (Exception, aiohttp.ContentTypeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An Unexpected Error Occurred While Durov: {str(e)} ]{Style.RESET_ALL}")

    async def coins(self, token: str, first_name: str, reward_coins: int):
        url = 'https://major.bot/api/bonuses/coins/'
        data = json.dumps({'coins':reward_coins})
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Origin': 'https://major.bot'
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    if response.status == 400:
                        error_coins = await response.json()
                        if 'detail' in error_coins:
                            if 'blocked_until' in error_coins['detail']:
                                return self.print_timestamp(
                                    f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                                    f"{Fore.YELLOW + Style.BRIGHT}[ Can Play Hold Coin At {datetime.fromtimestamp(error_coins['detail']['blocked_until']).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                                )
                    elif response.status in [500, 520]:
                        return self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Server Major Down ]{Style.RESET_ALL}"
                        )
                    response.raise_for_status()
                    coins = await response.json()
                    if coins['success']:
                        return self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.GREEN + Style.BRIGHT}[ Got {reward_coins} From Hold Coin ]{Style.RESET_ALL}"
                        )
        except aiohttp.ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An HTTP Error Occurred While Play Hold Coins: {str(e.message)} ]{Style.RESET_ALL}")
        except (Exception, aiohttp.ContentTypeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An Unexpected Error Occurred While Play Hold Coins: {str(e)} ]{Style.RESET_ALL}")

    async def roulette(self, token: str, first_name: str):
        url = 'https://major.bot/api/roulette/'
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': '0',
            'Content-Type': 'application/json',
            'Origin': 'https://major.bot'
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers) as response:
                    if response.status == 400:
                        error_coins = await response.json()
                        if 'detail' in error_coins:
                            if 'blocked_until' in error_coins['detail']:
                                return self.print_timestamp(
                                    f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                                    f"{Fore.YELLOW + Style.BRIGHT}[ Can Play Roulette At {datetime.fromtimestamp(error_coins['detail']['blocked_until']).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                                )
                    elif response.status in [500, 520]:
                        return self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Server Major Down ]{Style.RESET_ALL}"
                        )
                    response.raise_for_status()
                    roulette = await response.json()
                    return self.print_timestamp(
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.GREEN + Style.BRIGHT}[ Got {roulette['rating_award']} From Roulette ]{Style.RESET_ALL}"
                    )
        except aiohttp.ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An HTTP Error Occurred While Play Roulette: {str(e.message)} ]{Style.RESET_ALL}")
        except (Exception, aiohttp.ContentTypeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An Unexpected Error Occurred While Play Rouelette: {str(e)} ]{Style.RESET_ALL}")

    async def swipe_coin(self, token: str, first_name: str, reward_swipe_coins: int):
        url = 'https://major.bot/api/swipe_coin/'
        data = json.dumps({'coins':reward_swipe_coins})
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Origin': 'https://major.bot'
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    if response.status == 400:
                        error_coins = await response.json()
                        if 'detail' in error_coins:
                            if 'blocked_until' in error_coins['detail']:
                                return self.print_timestamp(
                                    f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                                    f"{Fore.YELLOW + Style.BRIGHT}[ Can Play Swipe Coin At {datetime.fromtimestamp(error_coins['detail']['blocked_until']).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                                )
                    elif response.status in [500, 520]:
                        return self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Server Major Down ]{Style.RESET_ALL}"
                        )
                    response.raise_for_status()
                    swipe_coin = await response.json()
                    if swipe_coin['success']:
                        return self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.GREEN + Style.BRIGHT}[ Got {reward_swipe_coins} From Swipe Coin ]{Style.RESET_ALL}"
                        )
        except aiohttp.ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An HTTP Error Occurred While Play Swipe Coin: {str(e.message)} ]{Style.RESET_ALL}")
        except (Exception, aiohttp.ContentTypeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {first_name} An Unexpected Error Occurred While Play Swipe Coin: {str(e)} ]{Style.RESET_ALL}")

    async def main(self, queries: str):
        while True:
            try:
                accounts = await self.tg_auth(queries=queries)
                total_rating = 0

                self.print_timestamp(f"{Fore.WHITE + Style.BRIGHT}[ Information ]{Style.RESET_ALL}")
                for account in accounts:
                    await self.visit(token=account['token'], first_name=account['first_name'])
                    streak = await self.streak(token=account['token'], first_name=account['first_name'])
                    if streak is None: continue
                    user = await self.user(token=account['token'], id=account['id'], first_name=account['first_name'])
                    if user is None: continue

                    self.print_timestamp(
                        f"{Fore.CYAN + Style.BRIGHT}[ {account['first_name']} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.GREEN + Style.BRIGHT}[ Balance {user['rating']} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ Streak {streak['streak']} ]{Style.RESET_ALL}"
                    )

                    if user['squad_id'] is None:
                        await self.join_squad(token=account['token'], first_name=account['first_name'])
                    elif user['squad_id'] != 1904705154:
                        await self.leave_squad(token=account['token'], first_name=account['first_name'])
                    elif user['squad_id'] == 1904705154:
                        await self.squad(token=account['token'], first_name=account['first_name'], squad_id=user['squad_id'])

                self.print_timestamp(f"{Fore.WHITE + Style.BRIGHT}[ Games ]{Style.RESET_ALL}")
                for account in accounts:
                    await self.durov(token=account['token'], first_name=account['first_name'])
                    await self.coins(token=account['token'], first_name=account['first_name'], reward_coins=915)
                    await self.roulette(token=account['token'], first_name=account['first_name'])
                    await self.swipe_coin(token=account['token'], first_name=account['first_name'], reward_swipe_coins=3200)

                self.print_timestamp(f"{Fore.WHITE + Style.BRIGHT}[ Tasks ]{Style.RESET_ALL}")
                for account in accounts:
                    for type in ['true', 'false']:
                        tasks = await self.tasks(token=account['token'], type=type, first_name=account['first_name'])
                        if tasks is None: continue
                        for task in tasks:
                            if not task['is_completed']:
                                await self.complete_task(token=account['token'], first_name=account['first_name'], task_id=task['id'], task_title=task['title'], task_award=task['award'])
                                await asyncio.sleep(3)

                    user = await self.user(token=account['token'], id=account['id'], first_name=account['first_name'])
                    total_rating += user['rating'] if user else 0

                self.print_timestamp(
                    f"{Fore.CYAN + Style.BRIGHT}[ Total Account {len(accounts)} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT}[ Total Rating {total_rating} ]{Style.RESET_ALL}"
                )

                sleep_timestamp = (datetime.now().astimezone() + timedelta(seconds=1800)).strftime('%X %Z')
                self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting At {sleep_timestamp} ]{Style.RESET_ALL}")

                await asyncio.sleep(1800)
                self.clear_terminal()
            except Exception as e:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
                continue

if __name__ == '__main__':
    try:
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        init(autoreset=True)
        major = Major()

        queries_files = [f for f in os.listdir() if f.startswith('queries-') and f.endswith('.txt')]
        queries_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0)

        major.print_timestamp(
            f"{Fore.MAGENTA + Style.BRIGHT}[ 1 ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}[ Split Queries ]{Style.RESET_ALL}"
        )
        major.print_timestamp(
            f"{Fore.MAGENTA + Style.BRIGHT}[ 2 ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}[ Use Existing 'queries-*.txt' ]{Style.RESET_ALL}"
        )
        major.print_timestamp(
            f"{Fore.MAGENTA + Style.BRIGHT}[ 3 ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}[ Use 'queries.txt' Without Splitting ]{Style.RESET_ALL}"
        )

        initial_choice = int(input(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.YELLOW + Style.BRIGHT}[ Select An Option ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
        ))
        if initial_choice == 1:
            accounts = int(input(
                f"{Fore.YELLOW + Style.BRIGHT}[ How Much Account That You Want To Process Each Terminal ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            ))
            major.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Processing Queries To Generate Files ]{Style.RESET_ALL}")
            major.process_queries(lines_per_file=accounts)

            queries_files = [f for f in os.listdir() if f.startswith('queries-') and f.endswith('.txt')]
            queries_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0)

            if not queries_files:
                raise FileNotFoundError("No 'queries-*.txt' Files Found")
        elif initial_choice == 2:
            if not queries_files:
                raise FileNotFoundError("No 'queries-*.txt' Files Found")
        elif initial_choice == 3:
            queries = [line.strip() for line in open('queries.txt') if line.strip()]
        else:
            raise ValueError("Invalid Initial Choice. Please Run The Script Again And Choose A Valid Option")

        if initial_choice in [1, 2]:
            major.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Select The Queries File To Use ]{Style.RESET_ALL}")
            for i, queries_file in enumerate(queries_files, start=1):
                major.print_timestamp(
                    f"{Fore.MAGENTA + Style.BRIGHT}[ {i} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.CYAN + Style.BRIGHT}[ {queries_file} ]{Style.RESET_ALL}"
                )

            choice = int(input(
                f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.YELLOW + Style.BRIGHT}[ Select 'queries-*.txt' File ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            )) - 1
            if choice < 0 or choice >= len(queries_files):
                raise ValueError("Invalid Choice. Please Run The Script Again And Choose A Valid Option")

            selected_file = queries_files[choice]
            queries = major.load_queries(selected_file)

        asyncio.run(major.main(queries=queries))
    except (ValueError, IndexError, FileNotFoundError) as e:
        major.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
    except KeyboardInterrupt:
        sys.exit(0)