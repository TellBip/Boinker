from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_ignore_empty=True,
        extra='allow'
    )

    API_ID: int
    API_HASH: str

    USE_REF: bool = False
    REF_ID: str = 'boink252453226'

    TELEGRAM: bool = True  # Используется ли Телеграм  (True or False)
    BOT_TOKEN:  str = ''                      # Токен Телеграм-Бота
    CHAT_ID:  int = ''                        # Ваш chatid (@getmyid_bot)

    CHECK_API: bool  = True  # Проверять APi или нет

    USE_RANDOM_DELAY_IN_RUN: bool = True
    RANDOM_DELAY_IN_RUN: list[int] = [5, 60]

    PROXY_TYPE: str = 'http'

    AD_TASK_PREFIX: str = 'AdTask'

    BLACK_LIST_TASKS: list[str] = [
         'playSpell',
         'playKolo',
         'playAngryMiner',
         'playJetton',
         'telegramShareStory',
         'emojiOnPostTelegramNewsChannel',
         'NotGoldReward',
         'NotPlatinumReward',
         'connectTonWallet',
         'telegramJoinBoinkersNewsChannel',
         'telegramBoost',
         'telegramJoinAcidGames',
         'AnimalsAndCoins',
         'AnimalsAndCoinsIsland',
         'AnimalsAndCoinsInstall',
         'playCornBattle',
         'NBPSep',
         'inviteAFriend',
         'MergePalsQuests',
         'playAAO',
         'playPiggyPiggy',
         'dailyVIPEnergyPerk',
         'vipGoldPerk',
         'dailyVIPWheelSpins',
         'foxCoinEnergy',
         'DiamoreSep18',
         'VIPWheelSpins10',
         'playHexacore',
         'playdeckEnergy',
         'joinFomoHash',
         'playDropee3',
         'playPiggyBank',
         'twitterQuotePost64',
         'twitterLikePost64',
         'twitterLikeShitcoinaire10',
         'regPalmPay1',
         'playTrump',
         'testJettonByProperty',
         'twitterPost2',
         'twitterLikeShitcoinaire11',
         'twitterLikeShitcoinaire12',
         'twitterLikeShitcoinaire13',
         'sghTaskLvl10',
         'sghTaskCrop5d5',
         'sghTaskCrop10d7',
         'sghTaskInstall',
         'Play7/10_1',
         'sghTaskCrop25d20',
         'sghTaskCrop15d7',
         'sghTaskRevenue10',
         'sghTaskFtd',
    ]

    USE_PROXY_FROM_FILE: bool = True
    MAX_RETRIES: int = 2

    ENABLE_AUTO_TASKS: bool = True
    ENABLE_AUTO_WHEEL_FORTUNE: bool = True
    ENABLE_RAFFLE: bool = True
    TICKETS_MAX_LEVEL: int = 3
    ENABLE_AUTO_SPIN: bool = True
    ENABLE_EVENTS: bool = True
    ENABLE_AUTO_UPGRADE: bool = True
    ENABLE_AUTO_ELEVATOR: bool = True
    ELEVATOR_MAX_LEVEL: int = 3

settings = Settings()


