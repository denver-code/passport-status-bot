"""
Constants for messages and text used throughout the bot application.
Centralizes all duplicated text to ensure consistency and easy maintenance.
"""

# === WAIT MESSAGES ===
WAIT_CHECKING = "Зачекайте, будь ласка, триває перевірка..."
WAIT_DATA_LOADING = "Зачекайте, будь ласка, триває отримання даних..."
WAIT_PHOTO_ANALYSIS = "Зачекайте, будь ласка, триває аналіз фото..."
WAIT_SUBSCRIPTION_PROCESSING = (
    "Зачекайте, будь ласка, триває оформлення підписки #{session_id}..."
)

# === SUCCESS MESSAGES ===
SUCCESS_SUBSCRIPTION_CREATED = "Ви успішно підписані на сповіщення про зміну статусу"
SUCCESS_SUBSCRIPTION_CREATED_DETAILED = (
    "Ви успішно підписані на сповіщення про зміну статусу заявки"
)
SUCCESS_UNSUBSCRIPTION = "Ви успішно відписані від сповіщень про зміну статусу заявки"
SUCCESS_LINK_CREATED = (
    "Ваш Telegram ID успішно прив'язаний до ідентифікатора {session_id}"
)
SUCCESS_LINK_REMOVED = (
    "Ваш Telegram ID успішно відв'язаний від ідентифікатора {session_id}"
)

# === ERROR MESSAGES ===
ERROR_GENERIC = "Виникла помилка. Спробуйте пізніше."
ERROR_GENERIC_DETAILED = "Виникла помилка при {operation}. Спробуйте пізніше."
ERROR_CHECKING = "Виникла помилка, спробуйте пізніше."
ERROR_IDENTIFIER_VALIDATION = "Виникла помилка перевірки ідентифікатора, можливо дані некоректні чи ще не внесені в базу, спробуйте пізніше."
ERROR_QR_RECOGNITION = "Виникла помилка при розпізнаванні QR-коду. Спробуйте пізніше."
ERROR_APPLICATION_UPDATE = "Виникла помилка при оновленні заявки. Спробуйте пізніше."

# === NOT FOUND MESSAGES ===
NOT_FOUND_IDENTIFIER = "Вашого ідентифікатора не знайдено, надішліть його, будь ласка використовуючи команду /link \nНаприклад /link 1006655"
NOT_FOUND_IDENTIFIER_OR_APPLICATION = (
    "Вашого ідентифікатора не знайдено або заявка не знайдена."
)
NOT_SUBSCRIBED = "Ви не підписані на сповіщення про зміну статусу заявки"

# === INSTRUCTION MESSAGES ===
INSTRUCTION_INVALID_SESSION_ID = "Надішліть ваш ідентифікатор, будь ласка використовуючи команду {command} \nНаприклад {command} 1006655"

# === STATUS MESSAGES ===
STATUS_NOT_CHANGED = "Статуси не змінилися.\n\n/cabinet - персональний кабінет"
STATUS_CHANGE_DETECTED = "Ми помітили зміну статусу заявки *#{session_id}:*\n"
STATUS_APPLICATION_HEADER = "Статуси заявки *#{session_id}:*\n\n"
STATUS_GENERAL_HEADER = "Статуси:\n\n"

# === SUBSCRIPTION MESSAGES ===
SUBSCRIPTION_LIMIT_REACHED = (
    "Ви досягли максимальної кількості підписок на сповіщення про зміну статусу заявки"
)
SUBSCRIPTION_ALREADY_EXISTS = "Ви вже підписані на сповіщення про зміну статусу заявки.\nTopic: `MFA_{user_id}_{secret_id}`"
SUBSCRIPTION_CREATE_FAILED = (
    "Не вдалося створити підписки. Перевірте правильність ідентифікаторів."
)

# === QR CODE MESSAGES ===
QR_NOT_RECOGNIZED = (
    "QR-код не розпізнано. Переконайтеся, що фото чітке та спробуйте ще раз."
)
QR_RECOGNIZED = "Розпізнано QR-код: `{code}`"

# === SECTION HEADERS ===
HEADER_YOUR_SUBSCRIPTIONS = "*Ваші підписки:*\n"
HEADER_YOUR_CABINET = (
    "*Ваш кабінет:*\nTelegram ID: `{user_id}`\nСесія: `{session_id}`\n"
)
HEADER_APPLICATION_STATUSES = "*Статуси заявки:*\n"
HEADER_APPLICATIONS = "*Заявки:*\n"

# === ADMIN MESSAGES ===
ADMIN_ONLY_COMMAND = "❌ Тільки адміністратор може користуватися цією командою!"
ADMIN_USERS_LIST_HEADER = "*📊 Список користувачів:*\n"
ADMIN_CLEANUP_START = "*🔍 Аналіз бази даних...*"
ADMIN_CLEANUP_ANALYZING = "*⏳ Аналіз даних...*"
ADMIN_CLEANUP_DELETING = "*🗑 Видалення даних...*"
ADMIN_CLEANUP_CONFIRM = """*⚠️ Знайдено невалідні дані:*

*Користувачі для видалення:* `{users}`
*Підписки для видалення:* `{subs}`

*Деталі:*
• Користувачі без telegram\\_id: `{users_no_id}`
• Користувачі з невалідними даними: `{users_invalid}`
• Підписки без telegram\\_id: `{subs_no_id}`
• Підписки без session\\_id: `{subs_no_session}`
• Підписки від видалених користувачів: `{subs_orphaned}`

⚠️ *Увага: Ця дія незворотня\\!*"""

ADMIN_CLEANUP_CONFIRM_BUTTON = "✅ Підтвердити видалення"
ADMIN_CLEANUP_CANCEL_BUTTON = "❌ Скасувати"
ADMIN_CLEANUP_CANCELLED = "_Операцію скасовано_"
ADMIN_CLEANUP_PROCESSING = "Видалення..."
ADMIN_CLEANUP_CANCELLED_POPUP = "Операцію скасовано"
ADMIN_CLEANUP_NO_PERMISSION = "❌ Недостатньо прав"
ADMIN_CLEANUP_EXPIRED = (
    "*⚠️ Дані застаріли. Будь ласка, запустіть команду /cleanup знову.*"
)
ADMIN_CLEANUP_RESULT = """*✅ Очищення завершено:*

*Видалено користувачів:* `{users}`
*Видалено підписок:* `{subs}`

*Деталі:*
• Користувачі без telegram\\_id: `{users_no_id}`
• Користувачі з невалідними даними: `{users_invalid}`
• Підписки без telegram\\_id: `{subs_no_id}`
• Підписки без session\\_id: `{subs_no_session}`
• Підписки від видалених користувачів: `{subs_orphaned}`"""
ADMIN_CLEANUP_ERROR = "❌ Помилка при очищенні бази даних. Перевірте логи."
ADMIN_CLEANUP_NOTHING = "*✅ База даних не містить невалідних даних.*"
ADMIN_USER_ENTRY = "👤 *ID:* `{telegram_id}`"
ADMIN_USER_SESSION = "   *Сесія:* `{session_id}`"
ADMIN_USER_SUBSCRIPTIONS_HEADER = "   *Підписки:*"
ADMIN_USER_NO_SUBSCRIPTIONS = "   *Підписки:* немає"
ADMIN_USER_SUBSCRIPTION_ENTRY = "   • `{sub_id}`"
ADMIN_TOTAL_STATS = "\n*Всього користувачів:* {users}\n*Всього підписок:* {subs}"
ADMIN_INVALID_DATA_WARNING = "\n⚠️ *Увага:* Знайдено {invalid_users} невалідних користувачів та {invalid_subs} невалідних підписок"

# === VERSION MESSAGES ===
VERSION_ERROR = "❌ *Не вдалося отримати інформацію про версію*"
VERSION_FORMAT = "🤖 Версія бота: *v{version}*\n📦 [Завантажити останню версію]({link})"
VERSION_UPDATE_ERROR = "❌ Помилка при отриманні інформації про версію"
VERSION_API_ERROR = "Помилка при запиті до GitHub API: {error}"
VERSION_NO_RELEASES = "Репозиторій не має релізів"

# === TIME FORMATTING ===
LAST_UPDATE_FORMAT = "Останнє оновлення: {timestamp}"
SUBSCRIPTION_COUNT_FORMAT = "Всього: {count}"

# === PUSH NOTIFICATION MESSAGES ===
PUSH_SUCCESS_MESSAGE = """Ви успішно підписані на сповіщення про зміну статусу заявки
Ваш секретний ідентифікатор: {secret_id}

Щоб підписатиня на сповіщення, додайте наступний топік до NTFY.sh:
`MFA_{user_id}_{secret_id}`"""

PUSH_NOTIFICATION_TITLE = "Оновлення заявки #{session_id}"
PUSH_NOTIFICATION_ERROR = (
    "Помилка при надсиланні сповіщення користувачу {telegram_id}: {error}"
)
PUSH_NOTIFICATION_SEND_ERROR = (
    "Помилка при надсиланні сповіщення через Telegram: {error}"
)

# === COMMAND MESSAGES ===
COMMAND_NOT_FOUND = "❌ Команду {command} не знайдено.\n\nСкористайтеся /help для перегляду списку доступних команд."

# === AUTHORS INFO ===
AUTHORS_MESSAGE = """👨‍💻 *Автори бота:*

*1. Автор ідеї та розробник:* Ihor Savenko
   • [👨‍💻 GitHub](https://github.com/denver-code)
   • [🌐 Website](https://ihorsavenko.com/)
   • [✈️ Telegram](https://t.me/operatorSilence)
   • [💬 Discord](https://discord.gg/operatorsilence)

*2. Розробник:* Oleksandr Shevchenko
   • [👨‍💻 GitHub](https://github.com/mrAlexZT)

*Про проект:*
📦 *Версія:* [v{version}]({repo_link})
📝 *Ліцензія:* [MIT](https://github.com/denver-code/passport-status-bot/blob/main/LICENSE)

*Технічна інформація:*
🔧 [Python](https://www.python.org/), [MongoDB](https://www.mongodb.com/), [aiogram](https://docs.aiogram.dev/)
🤖 [Telegram Bot API](https://core.telegram.org/bots/api)
🔄 [Асинхронна архітектура](https://docs.python.org/3/library/asyncio.html)

Дякуємо за використання нашого бота! 🙏"""

# === RATE LIMIT MESSAGES ===
RATE_LIMIT_WAIT_MESSAGE = (
    "Останнє оновлення було менше {minutes} хв тому, спробуйте пізніше."
)

# === ANTISPAM MESSAGES ===
ANTISPAM_WAIT_MESSAGE = "⏳ Зачекайте трохи перед наступною командою..."
ANTISPAM_WAIT_WITH_WARNINGS = (
    "⏳ Зачекайте перед наступною командою. Попереджень: {warnings}/5"
)
ANTISPAM_COMMAND_RUNNING = "⚠️ Ця команда вже виконується. Зачекайте її завершення."
ANTISPAM_BANNED_MESSAGE = (
    "🚫 Ви тимчасово заблоковані за спам. Залишилось: {minutes} хв."
)
ANTISPAM_WARNING_MESSAGE = "⚠️ Попередження {warning_level}/5: Припиніть спамити!"
ANTISPAM_BAN_10MIN = "⚠️ Виявлено спам. Ви заблоковані на 10 хвилин."
ANTISPAM_BAN_30MIN = "🚫 Ви заблоковані на 30 хвилин за постійний спам."

# === COMMAND EXECUTION MESSAGES ===
COMMAND_TIMEOUT_MESSAGE = "⚠️ Команда виконується занадто довго. Спробуйте ще раз."
COMMAND_ERROR_MESSAGE = "❌ Виникла помилка при виконанні команди."
COMMAND_DUPLICATE_LINK = (
    "Ваш Telegram ID вже прив'язаний до ідентифікатора {session_id}"
)

# === BOT STATUS MESSAGES ===
BOT_STARTED_MESSAGE = "🚀 Bot started at {timestamp}"
BOT_STOPPED_MESSAGE = "🛑 Bot stopped at {timestamp}"
BOT_STARTUP_FAILED = "❌ Bot startup failed: {error}"
BOT_PING_RESPONSE = "Pong!"
BOT_TIME_RESPONSE = "Server time is: {time}"
BOT_STARTED_USER = "Бот запущено! Використовуйте команди для роботи."

# === LOGGING MESSAGES ===
LOGGING_TOGGLE_MESSAGE = "Логування переключено"
LOGGING_ERROR_MESSAGE = "❌ Помилка при зміні налаштувань логування"
LOGS_NOT_FOUND = "📁 Директорія з логами не знайдена"
LOGS_RECENT_HEADER = "📊 Останні записи логів:\n\n```\n{content}\n```"
LOGS_ERROR_HEADER = "🚨 Останні помилки:\n\n```\n{content}\n```"
LOGS_NO_ERRORS = "✅ Помилок не знайдено"
LOGS_ERROR = "❌ Помилка при отриманні логів"

# === BROADCAST MESSAGES ===
BROADCAST_NO_REPLY = "❌ Відповідайте на повідомлення, яке потрібно розіслати"
BROADCAST_PROGRESS = "📢 Розпочинаю розсилку для {count} користувачів..."
BROADCAST_RESULT = """📢 Розсилка завершена:
✅ Надіслано: {success}
❌ Заблоковано: {blocked}
⚠️ Помилки: {error}"""
BROADCAST_ERROR = "❌ Помилка при розсилці"

# === ADMIN PERMISSION MESSAGES ===
ADMIN_PERMISSION_DENIED = "⛔️ Доступно лише для адміністратора."

# === FILE MESSAGES ===
FILE_NOT_FOUND = "❌ Файл {filename} не знайдено"
FILE_ERROR = "❌ Помилка при отриманні файлу"

# === STATS MESSAGES ===
STATS_MESSAGE = """📊 Статистика:

👤 Користувачі: {users}
🔔 Підписки: {subscriptions}
📨 Запити: {requests}
🚨 Помилки сьогодні: {errors}"""
STATS_ERROR = "❌ Помилка при отриманні статистики"
STATS_GRAPH_PROGRESS = "📊 Генерую графік..."
STATS_GRAPH_NO_DATA = "❌ Немає даних для побудови графіку"
STATS_GRAPH_CAPTION = """📊 Графік запитів за період
📅 Всього днів: {days}
📨 Всього запитів: {requests}"""
STATS_GRAPH_ERROR = "❌ Помилка при створенні графіку"

# === AUTHORS ERROR MESSAGES ===
AUTHORS_ERROR = "❌ Помилка при отриманні інформації про авторів"

# === BOT STOPPED MESSAGE ===
BOT_STOPPED_MANUALLY = "Bot stopped manually."

# === START AND WELCOME MESSAGES ===
START_WELCOME_MESSAGE = """*Вітаю!*👋

Цей бот повідомляє про зміни статусу вашої заявки на _passport.mfa.gov.ua_, щоб почати користуватися ботом надішліть свій ідентифікатор.
Для користування всіма функціями надішліть /cabinet або /help для детальнішої інформації.

Важливо зазначити, що цей бот *НЕ ПОВ'ЯЗАНИЙ* з МЗС України, і не несе відповідальності за вірогідність чи своєчасність інформації, для детального пояснення надішліть /policy"""

POLICY_MESSAGE = """*Загальна інформація*
Бот розроблений для спрощення процесу відстеження статусу заявки на оформлення паспорту на сайті _passport.mfa.gov.ua_ незалежним розробником, і не пов'язаний з МЗС України.
Використання функцій бота не зобов'язує вас ні до чого, і не несе відповідальності за вірогідність чи своєчасність інформації, використання відбувається на ваш страх та ризик.

*Користування*
Функція відображення статусу заявки доступна лише після надіслання боту вашого ідентифікатора, який ви отримали при реєстрації заявки на сайті _passport.mfa.gov.ua_ ніяким чином не зберігається, і використовується лише для надіслення цього ідентифікатору на офіційний вебсайт.
Всі решта функцій доступні (кабінет, сповіщення про зміни статусу) - використовують базу даних та зберігають ваш Telegram ID, Ідентифікатор Сесії _passport.mfa.gov.ua_, та всі статуси заявки.
Використання цих функцій підтверджує вашу згоду на зберігання цих даних.

*Видалення даних*
Для видалення всіх ваших даних з бази даних скористайтеся командою /unlink

*Технічна інформація*
Бот використовує офіційний API Telegram, MongoDB для зберігання даних, і Python для обробки запитів.
Всі дані зберігаються на серверах в Європі, і не передаються третім особам.

*Контакти*
З питаннями та пропозиціями звертайтеся до розробника: /authors"""

# === HELP MESSAGES ===
HELP_MESSAGE = """*Доступні команди:*

*Основні команди:*
/start - Почати роботу з ботом
/help - Список команд
/cabinet - Персональний кабінет
/policy - Політика та умови використання

*Управління профілем:*
/link <ID> - Прив'язати ідентифікатор заявки
/unlink - Відв'язати ідентифікатор та видалити профіль

*Підписки на сповіщення:*
/subscribe <ID> - Підписатися на сповіщення
/unsubscribe <ID> - Відписатися від сповіщень
/subscriptions - Список ваших підписок
/update - Оновити статус заявки вручну

*Push-сповіщення:*
/push - Підписатися на сповіщення через NTFY.sh
/dump - Отримати дамп даних ваших підписок

*Інше:*
/ping - Перевірити роботу бота
/version - Версія бота
/authors - Інформація про авторів

*Швидкий старт:*
1. Надішліть /link YOUR_ID для прив'язки заявки
2. Надішліть /cabinet для перегляду статусу
3. Надішліть /subscribe YOUR_ID для підписки на сповіщення"""
