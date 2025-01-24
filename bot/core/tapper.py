import asyncio
import random

from datetime import datetime, timedelta, timezone
from dateutil import parser
from time import time
from urllib.parse import unquote

import json
import re

from curl_cffi import requests

from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw import types
from bot.core.agents import generate_random_user_agent
from bot.core.headers import headers, get_sec_ch_ua


from bot.utils import logger
from bot.utils.logger import SelfTGClient
from bot.exceptions import InvalidSession
from bot.config import settings

self_tg_client = SelfTGClient()

class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.user_id = 0
        self.username = None
        self.first_name = None
        self.last_name = None
        self.fullname = None
        self.start_param = None
        self.peer = None
        self.first_run = None
        self.scraper = None

        self.session_ug_dict = self.load_user_agents() or []

        user_agent = self.check_user_agent()
        headers['User-Agent'] = user_agent
        headers.update(**get_sec_ch_ua(user_agent))

    async def generate_random_user_agent(self):
        return generate_random_user_agent()

    def info(self, message):
        from bot.utils import info
        info(f"<light-yellow>{self.session_name}</light-yellow> | {message}")

    def debug(self, message):
        from bot.utils import debug
        debug(f"<light-yellow>{self.session_name}</light-yellow> | {message}")

    def check_timeout_error(self, error):
        try:
            error_message = str(error)
            is_timeout_error = re.search("504, message='Gateway Timeout'", error_message)
            return is_timeout_error
        except Exception as e:
            return False

    def check_error(self, error, message):
        try:
            error_message = str(error)
            is_equal = re.search(message, error_message)
            return is_equal
        except Exception as e:
            return False

    def warning(self, message):
        from bot.utils import warning
        warning(f"<light-yellow>{self.session_name}</light-yellow> | {message}")

    def error(self, message):
        from bot.utils import error
        error(f"<light-yellow>{self.session_name}</light-yellow> | {message}")

    def critical(self, message):
        from bot.utils import critical
        critical(f"<light-yellow>{self.session_name}</light-yellow> | {message}")

    def success(self, message):
        from bot.utils import success
        success(f"<light-yellow>{self.session_name}</light-yellow> | {message}")

    def save_user_agent(self):
        user_agents_file_name = "user_agents.json"

        if not any(session['session_name'] == self.session_name for session in self.session_ug_dict):
            user_agent_str = generate_random_user_agent()

            self.session_ug_dict.append({
                'session_name': self.session_name,
                'user_agent': user_agent_str})

            with open(user_agents_file_name, 'w') as user_agents:
                json.dump(self.session_ug_dict, user_agents, indent=4)

            logger.success(f"<light-yellow>{self.session_name}</light-yellow> | User agent saved successfully")

            return user_agent_str

    def load_user_agents(self):
        user_agents_file_name = f'sessions/accounts.json'

        try:
            with open(user_agents_file_name, 'r') as user_agents:
                session_data = json.load(user_agents)
                if isinstance(session_data, list):
                    return session_data

        except FileNotFoundError:
            logger.warning("User agents file not found, creating...")

        except json.JSONDecodeError:
            logger.warning("User agents file is empty or corrupted.")

        return []

    def check_user_agent(self):
        load = next(
            (session['user_agent'] for session in self.session_ug_dict if session['session_name'] == self.session_name),
            None)

        if load is None:
            return self.save_user_agent()

        return load

    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            with_tg = True

            if not self.tg_client.is_connected:
                with_tg = False
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            if settings.USE_REF == True:
                ref_id = settings.REF_ID
            else:
                ref_id = random.choice(['boink1076726282','boink228618799', 'boink252453226'])

            self.start_param = random.choices([ref_id, 'boink1076726282', "boink252453226", "boink228618799"], weights=[70, 10, 10, 10], k=1)[0]
            peer = await self.tg_client.resolve_peer('boinker_bot')
            InputBotApp = types.InputBotAppShortName(bot_id=peer, short_name="boinkapp")

            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=peer,
                app=InputBotApp,
                platform='android',
                write_allowed=True,
                start_param=self.start_param
            ))

            auth_url = web_view.url

            tg_web_data = unquote(
                string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0])

            try:
                if self.user_id == 0:
                    information = await self.tg_client.get_me()
                    self.user_id = information.id
                    self.first_name = information.first_name or ''
                    self.last_name = information.last_name or ''
                    self.username = information.username or ''
            except Exception as e:
                self.error(f'Error during get tg web data: {e}')

            if with_tg is False:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(
                f"<light-yellow>{self.session_name}</light-yellow> | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def login(self, http_client, initdata):
        url = "https://boink.boinkers.co/public/users/loginByTelegram?p=android"
        json_data = {
            "initDataString": initdata
        }

        for retry_count in range(settings.MAX_RETRIES):
            try:
                response = await http_client.post(url,json=json_data)

                response.raise_for_status()
                resp_json = response.json()

                if not resp_json.get('token'):
                    self.error(f"Error during login | Invalid server response: {resp_json}")
                    return False

                logger.success(f"<light-yellow>{self.session_name}</light-yellow> | Login successful.")
                return resp_json.get("token")

            except Exception as e:
                self.error(f"Error during login attempt {retry_count + 1}: {e}")
                await asyncio.sleep(delay=random.randint(5, 10))
                if retry_count == settings.MAX_RETRIES - 1:
                    await asyncio.sleep(delay=random.randint(5, 10))
                continue

        self.error("Login failed after max retries.")
        return False

    async def upgrade_boinker(self, http_client, upgrade_type):
        url = f"https://boink.boinkers.co/api/boinkers/{upgrade_type}?p=android"
        data = {}

        for retry_count in range(settings.MAX_RETRIES):
            try:
                await asyncio.sleep(delay=random.randint(3, 5))
                response = await http_client.post(url, json=data)

                response.raise_for_status()
                resp_json = response.json()

                if response.status_code == 200 and resp_json:
                    coins = "{:,}".format(resp_json['newSoftCurrencyAmount'])
                    spins = resp_json.get('newSlotMachineEnergy', 0)
                    rank = resp_json.get('rank', 'Unknown')

                    logger.success(
                        f"<light-yellow>{self.session_name}</light-yellow> | Upgrade Boinker | "
                        f"Coins: <light-yellow>{coins}</light-yellow> | "
                        f"Spins: <light-blue>{spins}</light-blue> | "
                        f"Rank: <magenta>{rank}</magenta>"
                    )
                    return True
                else:
                    self.error(
                        f"<light-yellow>{self.session_name}</light-yellow> | Upgrade Boinker | "
                        f"Not enough coins | Status: <magenta>{response.status_code}</magenta>"
                    )
                    return False

            except Exception as e:
                if retry_count == settings.MAX_RETRIES - 1:
                    await asyncio.sleep(delay=random.randint(1, 3))
                continue

        self.error("Failed to upgrade boinker")
        return False

    async def claim_booster(self, http_client, spin: int, multiplier: int = 0):
        url = 'https://boink.boinkers.co/api/boinkers/addShitBooster?p=android'
        json_data = {
            'multiplier': multiplier,
            'optionNumber': 1
        }

        if spin > 30 and multiplier == 0:
            json_data = {
                'multiplier': 2,
                'optionNumber': 3
            }

        for retry_count in range(settings.MAX_RETRIES):
            try:
                response = await http_client.post(url, json=json_data)

                if response is None:
                    self.error("Received None response while claiming booster.")
                    return False

                if response.status_code == 404:
                    logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Failed to claim booster")
                    return False

                response.raise_for_status()

                if response.status_code == 200:
                    return True
                else:
                    self.error(f"Failed to claim booster. Server responded with status: {response.status_code}")
                    return False

            except Exception as e:
                self.error(f"Error during claim booster attempt {retry_count + 1}: {e}")
                if retry_count == settings.MAX_RETRIES - 1:
                    self.error(f"Max retries reached. Failed to claim booster.")
                await asyncio.sleep(delay=random.randint(5, 10))
                continue

        return False

    async def spin_wheel_fortune(self, http_client, live_op):
        url = f"https://boink.boinkers.co/api/play/spinWheelOfFortune/1?p=android"
        json_data = {
            'liveOpId': live_op
        }

        for retry_count in range(settings.MAX_RETRIES):
            try:
                response = await http_client.post(url,json=json_data)
                response.raise_for_status()

                resp_json = response.json()

                if response.status_code == 200 and 'prize' in resp_json and 'prizeName' in resp_json['prize']:
                    name = resp_json['prize']['prizeName']
                    if 'prizeTypeName' in resp_json['prize']:
                        name = resp_json['prize']['prizeTypeName']

                    logger.success(
                        f"<light-yellow>{self.session_name}</light-yellow> | Wheel of Fortune | Prize: <magenta>{name}</magenta> - <light-green>{resp_json['prize']['prizeValue']}</light-green>")
                    return True
                else:
                    self.error(f"Failed to spin Wheel of Fortune. Response: {resp_json}")
                    return False

            except Exception as e:
                self.error(f"Error during spin wheel attempt {retry_count + 1}: {e}")
                if retry_count == settings.MAX_RETRIES - 1:
                    self.error(f"Max retries reached. Failed to spin Wheel of Fortune.")
                await asyncio.sleep(delay=random.randint(5, 10))
                continue

        self.error("Failed to spin Wheel of Fortune after max retries.")
        return False

    async def spin_slot_machine(self, http_client, spins: int):
        url_template = "https://boink.boinkers.co/api/play/spinSlotMachine/{spin_amount}?p=android"
        spin_amounts = [500, 150, 100, 50, 25, 10, 5, 3, 2, 1]
        remaining_spins = spins

        for retry_count in range(settings.MAX_RETRIES):
            try:
                while remaining_spins > 0:
                    spin_amount = next((amount for amount in spin_amounts if amount <= remaining_spins), 1)
                    url = url_template.format(spin_amount=spin_amount)
                    response = await http_client.post(url, json={})
                    response.raise_for_status()

                    resp_json = response.json()

                    if response.status_code == 200:
                        if 'prizeTypeName' in resp_json.get('prize', {}):
                            prize_type = resp_json['prize']['prizeTypeName']
                            prize_value = resp_json['prize'].get('prizeValue', 0)
                            self.success(
                                f"Spin prize: <light-blue>{prize_type}</light-blue> - "
                                f"<light-green>{prize_value}</light-green>"
                            )

                        await asyncio.sleep(delay=random.randint(1, 4))

                        remaining_spins = resp_json.get('userGamesEnergy', {}).get('slotMachine', {}).get('energy', 0)
                    else:
                        self.error(f"Unexpected status code: {response.status_code}")
                        await asyncio.sleep(delay=2)
                        return False

                return True

            except Exception as e:
                self.error(f"Error during slot machine spin attempt {retry_count + 1}: {e}")
                if retry_count == settings.MAX_RETRIES - 1:
                    self.error("Max retries reached. Failed to spin slot machine.")
                await asyncio.sleep(delay=random.randint(5, 10))
                continue

        return False

    async def get_user_info(self, http_client):

        url = 'https://boink.boinkers.co/api/users/me?p=android'
        for retry_count in range(settings.MAX_RETRIES):
            try:
                await asyncio.sleep(delay=2)
                response = await http_client.get(url)
                response.raise_for_status()

                user_data = response.json()
                return user_data

            except Exception as e:
                
                if retry_count == settings.MAX_RETRIES - 1:
                    self.error(f"Unknown error during getting user info: <light-yellow>{e}</light-yellow>")
                await asyncio.sleep(delay=random.randint(5, 10))
                continue
        return None

    async def events(self, http_client):
        await asyncio.sleep(delay=2)
        url = 'https://boink.boinkers.co/public/data/config?p=android'

        for retry_count in range(settings.MAX_RETRIES):
            try:
                response = await http_client.get(url)
                response.raise_for_status()

                user_data = response.json()
                ev = user_data.get('liveOps')

                if ev:
                    for obj in ev:
                        liveOpName = obj.get('liveOpName', '')
                        eventType = obj.get('dynamicLiveOp', {}).get('eventType', '')

                        if 'wheel' not in liveOpName.lower() and eventType == 'orderedGrid':
                            _id = obj.get('_id')
                            if _id:
                                for x in range(3):
                                    try:
                                        url_event = f"https://boink.boinkers.co/api/liveOps/dynamic/{_id}/{x}?p=android"
                                        await asyncio.sleep(delay=2)
                                        event_response = await http_client.post(url_event, json={})
                                        event_response.raise_for_status()

                                        event_data = event_response.json()
                                        prize_name = event_data['milestones'][x]['prizes'][0]['prizeName']
                                        prize_value = event_data['milestones'][x]['prizes'][0]['prizeValue']

                                        logger.success(
                                            f"<light-yellow>{self.session_name}</light-yellow> | EVENT | {liveOpName} | Prize: <magenta>{prize_name}</magenta> - <light-green>{prize_value}</light-green>")

                                    except Exception as e:
                                        
                                        break

                return None

            except Exception as e:
                self.error(f"Error get events attempt {retry_count + 1}: {e}")
                if retry_count == settings.MAX_RETRIES - 1:
                    self.error(f"Unknown error during getting events: <light-yellow>{e}</light-yellow>")
                await asyncio.sleep(delay=random.randint(5, 10))
                continue

    async def play_elevator(self, http_client, live_op):
        
        try:
            await asyncio.sleep(delay=2)
            url_empty = 'https://boink.boinkers.co/api/play/emptyElevatorPrizeStockpile?actionOrigin=init&p=android'
            await http_client.post(url_empty, json={})

            can_elevate = True
            is_win = True
            max_level = settings.ELEVATOR_MAX_LEVEL

            completed_level = 0

            while can_elevate and completed_level < max_level:
                await asyncio.sleep(delay=2)
                json_data = {'liveOpId': live_op}
                url_open = 'https://boink.boinkers.co/api/play/openElevator?p=android'
                resp = await http_client.post(url_open, json=json_data)

                data = None

                if resp.status_code == 200:
                    data = resp.json()
                    
                else:
                    return None

                if data and resp.status_code == 200 and 'isWin' in data:
                    completed_level = completed_level + 1
                    name = data['prize']['prizeTypeName']
                    self.success(f"Elevator | <magenta>Level</magenta> - <light-green>{completed_level}</light-green> | Prize: <magenta>{name}</magenta> - <light-green>{data['prize']['prizeValue']}</light-green>")
                    can_elevate = True
                    is_win = True
                    continue
                elif data and 'isWin' in data and data['isWin'] == False:
                    can_elevate = False
                    is_win = False
                    completed_level = completed_level + 1
                else:
                    can_elevate = False
                    is_win = False
                    completed_level = completed_level + 1

                await asyncio.sleep(delay=2)

            if is_win == True:
                await asyncio.sleep(delay=2)
                url_quit = 'https://boink.boinkers.co/api/play/quitAndCollect?p=android'
                res = await http_client.post(url_quit,json={})

                if res.status_code == 200:
                    self.success(f"You win in elevator | <magenta>Level</magenta> - <light-green>{completed_level}</light-green>")
                else:
                    self.warning(f"You lose in elevator | <magenta>Level</magenta> - <yellow>{completed_level}</yellow>")
            elif is_win == False:
                self.warning(f"You lose in elevator | <magenta>Level</magenta> - <yellow>{completed_level}</yellow>")
            else:
                self.warning(f"Something went wrong in elevator | <magenta>Level</magenta> - <yellow>{completed_level}</yellow>")

            return True
        except Exception as e:
            self.error(f"Error occurred during elevator: {e}")
            return False

    async def get_liveOpId(self, http_client):
        url = 'https://boink.boinkers.co/public/data/config?p=android'
        for retry_count in range(settings.MAX_RETRIES):
            try:
                response = await http_client.get(url)
                response.raise_for_status()

                user_data = response.json()

                fid = await self.find_id_by_key(user_data, "wheelOfFortune"), user_data['versionHash']
                return fid
            except Exception as e:
                if retry_count == settings.MAX_RETRIES - 1:
                    self.error(f"Unknown error during getting liveOP: <light-yellow>{e}</light-yellow>")

                await asyncio.sleep(delay=random.randint(5, 10))
                continue

    async def find_id_by_key(self, data, target_key: str, parent_id=None):
        if isinstance(data, dict):
            if target_key in data:
                
                return parent_id

            for key, value in data.items():
                result = await self.find_id_by_key(value, target_key, data.get("_id"))
                if result:
                    return result

        elif isinstance(data, list):
            for item in data:
                result = await self.find_id_by_key(item, target_key, parent_id)
                if result:
                    return result

        return None

    async def claim_raffle_data(self, http_client):
        url = 'https://boink.boinkers.co/api/raffle/claimTicketForUser?p=android'
        json_data = {}

        for retry_count in range(settings.MAX_RETRIES):
            try:
                await asyncio.sleep(delay=random.randint(15, 30))
                response = await http_client.post(url, json=json_data)
                response.raise_for_status()

                data = response.json()

                if data and response.status_code == 200:
                    milestone = data['milestoneReached']
                    tickets = data['tickets']

                    self.info(
                        f"Raffle Ticket Is Claimed | Milestone <light-green>{milestone}</light-green> Reached | "
                        f"Tickets: <light-green>{tickets}</light-green>"
                    )
                    return True
                else:
                    self.warning(f"Unexpected response during get raffle data: {data}")
                    return False

            except Exception as error:
                self.error(f"Error during claim raffle data attempt {retry_count + 1}: {error}")
                if retry_count == settings.MAX_RETRIES - 1:
                    return False
                else:
                    await asyncio.sleep(delay=random.randint(5, 10))

        return False

    async def _fetch_claimed_actions(self, http_client):
        url = "https://boink.boinkers.co/api/rewardedActions/mine?p=android"

        for retry_count in range(settings.MAX_RETRIES):
            try:
               await asyncio.sleep(delay=2)
               response = await http_client.get(url)
               response.raise_for_status()

               if response.status_code == 200:
                    claimed_actions = response.json()
                    return claimed_actions
               else:
                    return False

            except Exception as error:
                if retry_count == settings.MAX_RETRIES - 1:
                    self.error(f"Failed to fetch claimed actions after maximum retries. Error: {error}")
                    return False
                self.error(f"Error while fetching claimed actions, retrying... (Attempt {retry_count + 1}): {error}")
                await asyncio.sleep(random.randint(5, 10))

        return False

    async def perform_rewarded_actions(self, http_client):
        url = "https://boink.boinkers.co/api/rewardedActions/getRewardedActionList?p=android"
        skipped_tasks = settings.BLACK_LIST_TASKS

        for retry_count in range(settings.MAX_RETRIES):
            try:
                claimed_actions = await self._fetch_claimed_actions(http_client)
                await asyncio.sleep(delay=2)
                response = await http_client.get(url)

                response.raise_for_status()

                if response.status_code != 200:
                    self.error(f"Failed to fetch rewarded actions. Server responded with status: {response.status_code}")
                    continue

                rewarded_actions = response.json()
                if isinstance(rewarded_actions, dict):
                    rewarded_actions = list(rewarded_actions.values())

                if not isinstance(rewarded_actions, list) or not rewarded_actions:
                    self.warning("No valid rewarded actions found.")
                    return

                for action in rewarded_actions:
                    name_id = action.get('nameId', '')
                    started = action.get('clickDateTime', None)
                    claimed = action.get('claimDateTime', None)

                    if any(item.lower() in name_id.lower() for item in skipped_tasks):
                        continue

                    if started and claimed:
                        continue

                    if action.get('verification', {}).get('paramKey') == 'joinedChat':
                        continue

                    can_perform_task, wait_time = await self._can_perform_task(claimed_actions, action, name_id)

                    if not can_perform_task:
                        if wait_time:
                            wait_seconds = (wait_time - datetime.now(timezone.utc)).seconds
                            self.info(f"Task {name_id} not yet available. Waiting {wait_seconds} seconds.")
                        continue

                    if settings.AD_TASK_PREFIX.lower() in name_id.lower():
                        provider_id = action.get('verification', {}).get('paramKey', 'adsgram')
                        
                        await asyncio.sleep(delay=2)
                        await self.handle_ad_task(http_client=http_client, name_id=name_id, provider_id=provider_id,action=action)
                        continue

                    if not await self._perform_regular_task(http_client, name_id, action):
                        continue

                return

            except Exception as error:
                if retry_count == settings.MAX_RETRIES - 1:
                    self.error(f"Failed after maximum retries. Error: {error}")
                    return
                self.error(f"Error while performing rewarded actions, retrying... (Attempt {retry_count + 1}): {error}")
                await asyncio.sleep(random.randint(5, 10))

    async def _can_perform_task(self, claimed_actions, action, name_id):
        current_time = datetime.now(timezone.utc)
        seconds_to_claim_again = action.get('secondsToClaimAgain', 0)

        for retry_count in range(settings.MAX_RETRIES):
            try:
                if not claimed_actions or name_id not in claimed_actions:
                    return True, None

                curr_reward = claimed_actions.get(name_id)

                if 'claimDateTime' in curr_reward and curr_reward['claimDateTime'] and \
                        'clickDateTime' in curr_reward and curr_reward['clickDateTime']:
                    return False, None

                last_claim_time = parser.isoparse(
                    curr_reward.get('claimDateTime', '')
                ) if 'claimDateTime' in curr_reward else None

                if seconds_to_claim_again and last_claim_time:
                    next_available_time = last_claim_time + timedelta(seconds=seconds_to_claim_again)
                    if current_time < next_available_time:
                        return False, next_available_time

                return True, None

            except Exception as error:
                if retry_count == settings.MAX_RETRIES - 1:
                    self.error(f"Failed to check if task can be performed after maximum retries: {error}")
                    return False, None

                self.error(f"Error checking task availability, retrying... (Attempt {retry_count + 1}): {error}")
                await asyncio.sleep(random.randint(5, 10))

        return False, None

    async def _perform_regular_task(self, http_client, name_id, action):
        click_url = f"https://boink.boinkers.co/api/rewardedActions/rewardedActionClicked/{name_id}?p=android"

        for retry_count in range(settings.MAX_RETRIES):
            try:
                await asyncio.sleep(random.randint(5, 10))
                response = await http_client.post(click_url)
                response.raise_for_status()

                if response.status_code != 200:
                    return
                rewarded_actions = response.json()

                if rewarded_actions:
                    started = rewarded_actions.get('clickDateTime', None)
                    claimed = rewarded_actions.get('claimDateTime', None)

                    if started and claimed:
                        self.info(f"Task {name_id} already started and claimed. Skipping.")
                        return False


            except Exception as e:
                self.error(f"Error clicking task {name_id}: {e}")
                if retry_count == settings.MAX_RETRIES - 1:
                    self.error(f"Max retries reached for clicking task {name_id}.")
                    return False
                await asyncio.sleep(random.randint(3, 4))

        seconds_to_allow_claim = action.get('secondsToAllowClaim', 10)

        if seconds_to_allow_claim > 60:
            self.info(f"Task {name_id} requires {seconds_to_allow_claim} seconds to wait. Skipping.")
            return False

        if seconds_to_allow_claim < 5:
            self.warning(f"Task {name_id} has less than 5 seconds ({seconds_to_allow_claim}). Using minimum 5 seconds.")
            seconds_to_allow_claim = 5

        self.info(f"Waiting {seconds_to_allow_claim} seconds before claiming reward for task {name_id}.")
        await asyncio.sleep(seconds_to_allow_claim)

        claim_url = f"https://boink.boinkers.co/api/rewardedActions/claimRewardedAction/{name_id}?p=android"

        for retry_count in range(settings.MAX_RETRIES):
            try:
                response = await http_client.post(claim_url)
                response.raise_for_status()
                if response.status_code != 200:
                    return
                result = response.json()

                if result and 'prizeGotten' in result:
                    reward = result['prizeGotten']
                    self.success(f"Task {name_id} completed. Reward: 💰 <light-green>{reward}</light-green> 💰")
                else:
                    self.warning(f"No reward found for task {name_id}.")

                break

            except Exception as e:
                self.error(f"Error claiming reward for task {name_id}: {e}")
                if retry_count == settings.MAX_RETRIES - 1:
                    self.error(f"Max retries reached for claiming reward for task {name_id}.")
                    return False
                await asyncio.sleep(random.randint(5, 10))

        return True

    async def get_raffle_data(self, http_client):
        url = "https://boink.boinkers.co/api/raffle/getRafflesData?p=android"

        for retry_count in range(settings.MAX_RETRIES):
            try:
                await asyncio.sleep(delay=2)
                response = await http_client.get(url)
                response.raise_for_status()

                data = response.json()

                if data and response.status_code == 200:
                    raffle_id = data.get('userRaffleData', {}).get('raffleId')
                    milestone = data.get('userRaffleData', {}).get('milestoneReached', 0)
                    ticket = data.get('userRaffleData', {}).get('tickets', 0)
                    current_raffle = data.get('currentRaffle') or {}
                    time_end = current_raffle.get('endDate', 0)
                    

                    self.info(
                        f"Raffle Data | "
                        f"ID : {raffle_id} | "
                        f"Milestone <light-green>{milestone}</light-green> Reached | "
                        f"{ticket} Ticket"
                    )
                    return milestone , time_end

                else:
                    self.warning(f"Unexpected response during get raffle data: {data}")
                    return False

            except Exception as e:
                self.error(f"Error during get raffle data attempt {retry_count + 1}: {e}")
                if retry_count == settings.MAX_RETRIES - 1:
                    self.error("Max retries reached. Failed to retrieve raffle data.")
                await asyncio.sleep(delay=random.randint(5, 10))
                continue
            return None

    async def handle_ad_task(self, http_client, name_id, provider_id, action):
        for retry_count in range(settings.MAX_RETRIES):
            try:
                await asyncio.sleep(delay=random.randint(5, 10))
                click_url = f"https://boink.boinkers.co/api/rewardedActions/rewardedActionClicked/{name_id}?p=android"

                response = await http_client.post(click_url)
                response.raise_for_status()

                if response.status_code != 200:
                    logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Failed to click ad task {name_id}. Status code: {response.status}")
                    return

                logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Ad task {name_id} clicked successfully")
                logger.info(f"<light-yellow>{self.session_name}</light-yellow> | 💤 Sleep 5 seconds before closing ad... 💤")

                await asyncio.sleep(delay=random.randint(5, 10))
                ad_watched_url = "https://boink.boinkers.co/api/rewardedActions/ad-watched?p=android"
                ad_payload = {'adsForSpins': False, "providerId": provider_id}

                response = await http_client.post(ad_watched_url, json=ad_payload)
                response.raise_for_status()
                if response.status_code != 200:
                    logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Failed to mark ad as watched for task {name_id}. Status code: {response.status}")
                    return


                logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Ad task {name_id} watched successfully")

                seconds_to_allow_claim = action.get('secondsToAllowClaim', 25) + 5
                logger.info(
                    f"<light-yellow>{self.session_name}</light-yellow> | 💤 Sleep {seconds_to_allow_claim} seconds before claiming ad reward... 💤")
                await asyncio.sleep(delay=seconds_to_allow_claim)

                claim_url = f"https://boink.boinkers.co/api/rewardedActions/claimRewardedAction/{name_id}?p=android"

                response = await http_client.post(claim_url)
                response.raise_for_status()
                if response.status_code != 200:
                    logger.error(f"<light-yellow>{self.session_name}</light-yellow> | 😢 Failed to claim reward for ad task {name_id}. Status code: {response.status}")
                    return

                result = response.json()

                if result and 'prizeGotten' in result:
                    reward = result['prizeGotten']
                    logger.success(
                        f"<light-yellow>{self.session_name}</light-yellow> | Successfully completed ad task {name_id} | Reward: 💰<light-green>{reward}</light-green> 💰")
                else:
                    logger.warning(
                        f"<light-yellow>{self.session_name}</light-yellow> | No reward found for ad task {name_id}.")

                break

            except Exception as error:
                logger.error(
                    f"<light-yellow>{self.session_name}</light-yellow> | 😢 Error handling ad task {name_id}: {error}")

            if retry_count == settings.MAX_RETRIES - 1:
                logger.error(
                    f"<light-yellow>{self.session_name}</light-yellow> | Max retries reached for ad task {name_id}. Task failed.")

    async def check_proxy(self, http_client) -> None:
        try:

            response = await http_client.get('https://ipinfo.io/json', headers={}, timeout=5)

            response.raise_for_status()
            data = response.json()

            ip = data.get('ip')
            city = data.get('city')
            country = data.get('country')
            self.info(f"Check proxy! Country: <cyan>{country}</cyan> | City: <light-yellow>{city}</light-yellow> | Proxy IP: {ip}")
            return True
        except Exception as error:
            self.error(f"Proxy: 😢 Error: {error}")
            return False

    async def run(self, proxy: str | None) -> None:
        if settings.USE_RANDOM_DELAY_IN_RUN:
            random_delay = random.randint(settings.RANDOM_DELAY_IN_RUN[0], settings.RANDOM_DELAY_IN_RUN[1])
            self.info(f"Bot will start in <ly>{random_delay}s</ly>")
            await asyncio.sleep(random_delay)

        access_token = None
        login_need = True

        http_client = requests.AsyncSession(impersonate="chrome99_android")
        http_client.headers.update(headers)

        if settings.USE_PROXY_FROM_FILE:
            proxys = {
                "http": proxy,
                "https": proxy}
            http_client.proxies = proxys

        self.access_token_created_time = 0
        self.token_live_time = random.randint(4000, 4600)
        
        tries_to_login = 3

        while True:
            try:
                if not await self.check_proxy(http_client):
                    self.error('Failed to connect to proxy server. Sleep 150 seconds.')
                    await asyncio.sleep(150)
                    continue
                if time() - self.access_token_created_time >= self.token_live_time:
                    login_need = True

                if login_need:
                    if "Authorization" in http_client.headers:
                        del http_client.headers["Authorization"]
                    

                    init_data = await self.get_tg_web_data(proxy=proxy)
                    
                    
                    access_token = await self.login(http_client, init_data)

                    if not access_token:
                        return

                    http_client.headers['Authorization'] = f"{access_token}"

                    self.access_token_created_time = time()
                    self.token_live_time = random.randint(1500, 1900)
                    


                    login_need = False

                await asyncio.sleep(3)

            except Exception as error:
                self.error(f"Unknown error during login: <light-yellow>{error}</light-yellow>")
                break

            try:
                await asyncio.sleep(delay=2)
                live_op , hash = await self.get_liveOpId(http_client)
                
                self.info(f"Hash - {hash}")
                if hash != '-1326987291':
                    self.warning(f"Please STOP - NEED UPDATE")
                    break
                await asyncio.sleep(delay=2)
                user_info = await self.get_user_info(http_client)
                await asyncio.sleep(delay=2)
                if user_info is not None:
                    if user_info['boinkers'] and 'completedBoinkers' in user_info['boinkers']:
                        logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Boinkers: <light-blue>{user_info['boinkers']['completedBoinkers']}</light-blue> 👨‍🚀")

                    if 'currencySoft' in user_info:
                        logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Coin Balance: 💰 <light-green>{'{:,}'.format(user_info['currencySoft'])}</light-green> 💰")

                    if 'currencyCrypto' in user_info:
                        logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Shit Balance: 💩 <cyan>{'{:,.3f}'.format(user_info['currencyCrypto'])}</cyan> 💩")

                    current_time = datetime.now(timezone.utc)
                    last_claimed_time_str = user_info.get('boinkers', {}).get('booster', {}).get('x2', {}).get('lastTimeFreeOptionClaimed')
                    last_claimed_time = parser.isoparse(last_claimed_time_str) if last_claimed_time_str else None

                    last_claimed_time_str_x29 = user_info.get('boinkers', {}).get('booster', {}).get('x29', {}).get('lastTimeFreeOptionClaimed')
                    last_claimed_time_x29 = parser.isoparse(last_claimed_time_str_x29) if last_claimed_time_str_x29 else None
                    if not last_claimed_time_x29 or current_time > last_claimed_time_x29 + timedelta(hours=2, minutes=5):
                        await asyncio.sleep(delay=2)
                        
                        success = await self.claim_booster(http_client=http_client, spin=user_info['gamesEnergy']['slotMachine']['energy'], multiplier=29)
                        if success:
                            logger.success(f"<light-yellow>{self.session_name}</light-yellow> | 🚀 Claimed boost successfully 🚀")
                            await asyncio.sleep(delay=4)
                    if not last_claimed_time or current_time > last_claimed_time + timedelta(hours=2, minutes=5):
                        await asyncio.sleep(delay=2)
                        
                        success = await self.claim_booster(http_client=http_client, spin=user_info['gamesEnergy']['slotMachine']['energy'])
                        if success:
                            logger.success(f"<light-yellow>{self.session_name}</light-yellow> | 🚀 Claimed boost successfully 🚀")
                            await asyncio.sleep(delay=4)
                    
                    if settings.ENABLE_RAFFLE:
                        milestone, time_end_str = await self.get_raffle_data(http_client)
                        await asyncio.sleep(delay=4)
                        time_end = parser.isoparse(time_end_str) if time_end_str else None
                        if time_end and settings.TICKETS_MAX_LEVEL > milestone and current_time <= time_end:
                            while settings.TICKETS_MAX_LEVEL > milestone:
                                await asyncio.sleep(delay=2)
                                milestone_result = await self.claim_raffle_data(http_client)
                                if not milestone_result:
                                    self.error("Claim raffle data failed multiple times. Stopping loop to avoid redundant retries.")
                                    break
                                milestone += 1
                            await asyncio.sleep(delay=4)
                    
                    if settings.ENABLE_AUTO_WHEEL_FORTUNE:
                        fortune_user = await self.get_user_info(http_client)
                        await asyncio.sleep(delay=random.randint(2, 4))
                        if fortune_user and 'gamesEnergy' in fortune_user and 'wheelOfFortune' in fortune_user['gamesEnergy']:
                            fortune_energy = fortune_user['gamesEnergy']['wheelOfFortune']['energy']
                            last_claimed_wheel_str = fortune_user['gamesEnergy']['wheelOfFortune']['lastUpdated']
                            last_claimed_wheel_time = parser.isoparse(last_claimed_wheel_str) if last_claimed_wheel_str else None
                            
                            freespin = fortune_user['gamesEnergy']['wheelOfFortune']['freeEnergyUsed']
                            
                            if fortune_energy > 0:
                                for _ in range(fortune_energy):
                                    
                                    await asyncio.sleep(delay=2)
                                    if not await self.spin_wheel_fortune(http_client, live_op):
                                        break
                                    await asyncio.sleep(delay=random.randint(2, 4))
                            elif not last_claimed_wheel_time or current_time > last_claimed_wheel_time + timedelta(hours=24):
                                
                                await self.spin_wheel_fortune(http_client, live_op)
                                await asyncio.sleep(delay=random.randint(2, 4))
                            
                                
                                
                                
                    
                    if settings.ENABLE_EVENTS:
                        events = await self.events(http_client)
                        await asyncio.sleep(delay=4)
                    
                    if settings.ENABLE_AUTO_TASKS:
                        await asyncio.sleep(delay=2)
                        task = await self.perform_rewarded_actions(http_client)
                        await asyncio.sleep(delay=4)
                    
                    if settings.ENABLE_AUTO_ELEVATOR:
                        await asyncio.sleep(delay=2)
                        elevator_user = await self.get_user_info(http_client)
                        
                        await asyncio.sleep(delay=random.randint(1, 3))
                        if elevator_user and 'gamesEnergy' in elevator_user and 'elevators' in elevator_user['gamesEnergy']:
                            elevator_last_used = elevator_user['gamesEnergy']['elevators']['lastUpdated']
                            
                            

                            parsed_date = datetime.strptime(elevator_last_used, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

                            one_day_ago = current_time - timedelta(days=1)
                            
                            
                            if parsed_date < one_day_ago:
                                await asyncio.sleep(delay=2)
                                
                                await self.play_elevator(http_client,live_op)
                                await asyncio.sleep(delay=random.randint(2, 4))
                    
                    if settings.ENABLE_AUTO_SPIN:
                        spin_user = await self.get_user_info(http_client=http_client)
                        await asyncio.sleep(delay=random.randint(1, 3))
                        if spin_user and 'gamesEnergy' in spin_user and 'slotMachine' in spin_user['gamesEnergy']:
                            spins = spin_user['gamesEnergy']['slotMachine']['energy']
                            last_claimed_spins_str = user_info.get('boinkers', {}).get('booster', {}).get('x2', {}).get('lastTimeFreeOptionClaimed')
                            last_claimed_spins_time = parser.isoparse(last_claimed_spins_str) if last_claimed_spins_str else None
                            if spins > 0:
                                self.info(f"Spins: <light-blue>{spins}</light-blue>")
                                await self.spin_slot_machine(http_client=http_client, spins=spins)
                                await asyncio.sleep(delay=random.randint(2, 4))
                    
                    if settings.ENABLE_AUTO_UPGRADE:
                        upgrade_types = ['megaUpgradeBoinkers', 'upgradeBoinker']
                        upgrade_success = True
                        while upgrade_success:
                            for upgrade_type in upgrade_types:
                                result = await self.upgrade_boinker(http_client=http_client, upgrade_type=upgrade_type)
                                if not result:
                                    upgrade_success = False
                                    break


                logger.info(f"<light-yellow>{self.session_name}</light-yellow> | 💤 sleep 30 minutes 💤")
                await asyncio.sleep(delay=1800)

            except Exception as error:
                self.error(f"😢 Unknown error: <light-yellow>{error}</light-yellow>")
                await asyncio.sleep(delay=120)

async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | 😢 Invalid Session 😢")
