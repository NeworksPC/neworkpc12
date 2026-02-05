import asyncio
import logging
import random
import string
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime, timedelta
import json
import os

# Токен вашего бота
BOT_TOKEN = "8342883084:AAH_INTLiRgrW1fpAsTPcxYvI9fd6c8wowU"
# ID администратора (основного)
ADMIN_ID = 7165501889
# Ссылка на приватную группу
PRIVATE_GROUP_LINK = "https://t.me/+iL5qzjdLjjM4YTMy"
# Ссылка на отзывы
REVIEWS_LINK = "https://t.me/reviewsNeworkPC"
# Ссылка на обзор функционала
FUNCTIONALITY_REVIEW_LINK = "https://t.me/neworkpcf"
# Ссылка для скачивания DLC
DLC_DOWNLOAD_LINK = "https://t.me/+UNdIZOL8P0U3Yzcy"  # ОБНОВЛЕНА
# Общий ключ для всех
COMMON_KEY = "ZINA-0518MNON3PK"  # ОБЩИЙ КЛЮЧ ДЛЯ ВСЕХ
# Реферальная комиссия (15%)
REFERRAL_PERCENT = 15
# Username вашего бота (ВАЖНО: без @)
BOT_USERNAME = "NeworkPCprivatekeybot"
# Минимальная сумма для вывода
MIN_WITHDRAWAL = 100

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Файлы для хранения данных
ORDERS_FILE = "orders.json"
KEYS_FILE = "keys.json"
USERS_FILE = "users.json"
ADMINS_FILE = "admins.json"
BANNED_USERS_FILE = "banned_users.json"
WITHDRAWALS_FILE = "withdrawals.json"

# Подписки с разными сроками
SUBSCRIPTION_PERIODS = {
    "7_days": {"name": "7 дней", "price": 300, "days": 7},
    "30_days": {"name": "30 дней", "price": 450, "days": 30},
    "forever": {"name": "Вечно", "price": 650, "days": "навсегда"}
}

# Типы устройств
DEVICES = {
    "apk": {
        "name": "NeworkPC APK Android - БЕЗ рут прав",
        "description": (
            "📱 NeworkPC APK Android - БЕЗ рут прав\n\n"
            "🔥 Поддержка последней версии игры (0.37.0)\n\n"
            "📲 Данный продукт поддерживает Android устройства версий 8-16\n\n"
            "🗽 Без рут прав!\n\n"
            "🔍 **Функционал APК версии:** [посмотреть обзор]({})\n\n"
            "✅ **Поддерживаются такие способы входа:**\n"
            "• Google аккаунт\n"
            "• VK\n"
            "• Facebook\n"
            "• Любой удобный способ!\n\n"
            "Выберите срок подписки ниже ⬇️"
        ).format(FUNCTIONALITY_REVIEW_LINK)
    },
    "emulator": {
        "name": "NeworkPC Emulator - БЕЗ рут прав",
        "description": (
            "💻 NeworkPC Emulator - БЕЗ рут прав\n\n"
            "🔥 Поддержка последней версии игры (0.37.0)\n\n"
            "🖥️ Работает на ПК через эмулятор Android\n\n"
            "🗽 Без рут прав!\n\n"
            "🔍 **Функционал эмулятора:** [посмотреть обзор]({})\n\n"
            "✅ **Поддерживаются такие способы входа:**\n"
            "• Google аккаунт\n"
            "• VK\n"
            "• Facebook\n"
            "• Любой удобный способ!\n\n"
            "Выберите срок подписки ниже ⬇️"
        ).format(FUNCTIONALITY_REVIEW_LINK)
    },
    "ios": {
        "name": "NeworkPC IPA iOS - на все iOS устройства",
        "description": (
            "📱 NeworkPC IPA iOS - на все iOS устройства\n\n"
            "🔥 Поддержка последней версии игры (0.37.0)\n\n"
            "🍎 Данный продукт поддерживает все iOS устройства\n"
            "   • iPhone 8 и новее\n"
            "   • iPad (любые модели)\n\n"
            "⚡ Установка через AltStore/Sideloadly\n"
            "🔧 Работает на непрошитых устройствах\n\n"
            "🔍 **Функционал iOS версии:** [посмотреть обзор]({})\n\n"
            "✅ **Поддерживаются такие способы входа:**\n"
            "• Game Center\n"
            "• Apple ID\n"
            "• Любой удобный способ!\n\n"
            "📦 **В комплекте:**\n"
            "• IPA файл приложения\n"
            "• Инструкция по установки\n"
            "• Поддержка и помощь в установке\n\n"
            "Выберите срок подписки ниже ⬇️"
        ).format(FUNCTIONALITY_REVIEW_LINK)
    }
}

# Реквизиты для оплаты
PAYMENT_DETAILS = {
    "tinkoff": {
        "name": "Тинькофф",
        "card_number": "2200702051431554",
        "instructions": "Оплата доступна только по карте Тинькофф",
        "type": "card"
    },
    "sber_sbp": {
        "name": "СБП Сбербанк",
        "phone_number": "+79308798141",
        "instructions": "Оплата через СБП (Систему быстрых платежей)",
        "type": "sbp"
    }
}

# Состояния для FSM
class PurchaseStates(StatesGroup):
    waiting_for_period = State()
    waiting_for_payment_method = State()
    waiting_for_receipt = State()

# Состояния для админки
class AdminStates(StatesGroup):
    waiting_broadcast_message = State()
    waiting_user_id_for_ban = State()
    waiting_user_id_for_unban = State()

# Функции для работы с данными
def load_data(filename):
    """Загрузка данных из JSON файла"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Ошибка при загрузке файла {filename}: {e}")
        return {}

def save_data(filename, data):
    """Сохранение данных в JSON файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка при сохранении файла {filename}: {e}")
        return False

def init_files():
    """Инициализация файлов данных при первом запуске"""
    files_to_init = [
        ORDERS_FILE, KEYS_FILE, USERS_FILE, 
        ADMINS_FILE, BANNED_USERS_FILE,
        WITHDRAWALS_FILE, "referral_transactions.json"
    ]
    
    for file in files_to_init:
        if not os.path.exists(file):
            save_data(file, {})
            print(f"✅ Создан файл: {file}")

def get_user_data(user_id):
    """Получение данных пользователя"""
    users = load_data(USERS_FILE)
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        users[user_id_str] = {
            "id": user_id,
            "username": None,
            "first_name": "",
            "last_name": "",
            "join_date": datetime.now().isoformat(),
            "balance": 0,
            "total_earned": 0,
            "referral_code": generate_referral_code(user_id),
            "referrer_id": None,
            "referrals": [],
            "active_key": None,
            "key_expires": None,
            "total_spent": 0,
            "orders_count": 0,
            "is_banned": False,
            "last_activity": datetime.now().isoformat(),
            "withdrawals": [],
            "total_withdrawn": 0,
            "card_number": None,
            "cardholder_name": None
        }
        save_data(USERS_FILE, users)
    return users[user_id_str]

def update_user_data(user_id, data):
    """Обновление данных пользователя"""
    users = load_data(USERS_FILE)
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        get_user_data(user_id)
        users = load_data(USERS_FILE)
    
    users[user_id_str].update(data)
    users[user_id_str]["last_activity"] = datetime.now().isoformat()
    save_data(USERS_FILE, users)

def generate_order_id():
    """Генерация ID заказа"""
    orders = load_data(ORDERS_FILE)
    if not orders:
        return "ORD-001"
    
    max_id = 0
    for order_id in orders.keys():
        if order_id.startswith("ORD-"):
            try:
                num = int(order_id.split('-')[1])
                if num > max_id:
                    max_id = num
            except:
                continue
    
    new_id = max_id + 1
    return f"ORD-{new_id:03d}"

def generate_key(order_id, period_days, device_type="apk"):
    """Генерация ключа (теперь возвращает общий ключ для всех)"""
    # Возвращаем общий ключ для всех пользователей
    key = COMMON_KEY
    
    if period_days == "навсегда":
        expires_at = None
    else:
        expires_at = (datetime.now() + timedelta(days=period_days)).isoformat()
    
    # Сохраняем информацию о ключе
    keys = load_data(KEYS_FILE)
    keys[key] = {
        "order_id": order_id,
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at,
        "is_used": False,
        "period_days": period_days,
        "device_type": device_type,
        "is_common": True  # Отметка, что это общий ключ
    }
    save_data(KEYS_FILE, keys)
    
    return key

def generate_referral_code(user_id):
    """Генерация реферального кода"""
    code = f"REF{user_id % 10000:04d}{random.randint(100, 999)}"
    return code

def get_referral_link(user_id):
    """Получение реферальной ссылки"""
    user_data = get_user_data(user_id)
    referral_code = user_data["referral_code"]
    return f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}"

def process_referral_system(user_id, amount):
    """Обработка реферальной системы при покупке"""
    users = load_data(USERS_FILE)
    user_id_str = str(user_id)
    
    if user_id_str in users:
        user_data = users[user_id_str]
        
        if "referrer_id" in user_data and user_data["referrer_id"]:
            referrer_id = user_data["referrer_id"]
            referrer_id_str = str(referrer_id)
            
            if referrer_id_str in users:
                referrer_data = users[referrer_id_str]
                
                if not referrer_data.get("is_banned", False):
                    # Расчет реферального бонуса (15% от суммы)
                    referral_bonus = int(amount * REFERRAL_PERCENT / 100)
                    
                    # Обновляем данные реферера
                    referrer_data["balance"] = referrer_data.get("balance", 0) + referral_bonus
                    referrer_data["total_earned"] = referrer_data.get("total_earned", 0) + referral_bonus
                    
                    # Добавляем реферала в список если его там еще нет
                    if "referrals" not in referrer_data:
                        referrer_data["referrals"] = []
                    
                    if user_id not in referrer_data["referrals"]:
                        referrer_data["referrals"].append(user_id)
                    
                    users[referrer_id_str] = referrer_data
                    save_data(USERS_FILE, users)
                    
                    # Сохраняем транзакцию
                    transactions = load_data("referral_transactions.json")
                    transaction_id = f"TRX-{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
                    transactions[transaction_id] = {
                        "referrer_id": referrer_id,
                        "user_id": user_id,
                        "amount": amount,
                        "bonus": referral_bonus,
                        "timestamp": datetime.now().isoformat(),
                        "order_id": None
                    }
                    save_data("referral_transactions.json", transactions)
                    
                    return referral_bonus
    
    return 0

def is_user_banned(user_id):
    """Проверка, забанен ли пользователь"""
    banned_users = load_data(BANNED_USERS_FILE)
    return str(user_id) in banned_users

def ban_user(user_id, reason="Нарушение правил", admin_id=ADMIN_ID):
    """Блокировка пользователя"""
    banned_users = load_data(BANNED_USERS_FILE)
    user_id_str = str(user_id)
    
    banned_users[user_id_str] = {
        "user_id": user_id,
        "banned_at": datetime.now().isoformat(),
        "banned_by": admin_id,
        "reason": reason
    }
    
    # Обновляем статус в данных пользователя
    users = load_data(USERS_FILE)
    if user_id_str in users:
        users[user_id_str]["is_banned"] = True
        save_data(USERS_FILE, users)
    
    save_data(BANNED_USERS_FILE, banned_users)
    return True

def unban_user(user_id):
    """Разблокировка пользователя"""
    banned_users = load_data(BANNED_USERS_FILE)
    user_id_str = str(user_id)
    
    if user_id_str in banned_users:
        del banned_users[user_id_str]
        save_data(BANNED_USERS_FILE, banned_users)
        
        # Обновляем статус в данных пользователя
        users = load_data(USERS_FILE)
        if user_id_str in users:
            users[user_id_str]["is_banned"] = False
            save_data(USERS_FILE, users)
        
        return True
    return False

# Команда /start с обработкой реферальных ссылок
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Проверяем, не забанен ли пользователь
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Вы заблокированы в этом боте. Для разблокировки свяжитесь с администратором.")
        return
    
    args = message.text.split()
    user_id = message.from_user.id
    
    # Обновляем/создаем данные пользователя
    user_data = get_user_data(user_id)
    user_data.update({
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name or ""
    })
    update_user_data(user_id, user_data)
    
    # Обработка реферальной ссылки
    referrer_name = ""
    if len(args) > 1 and args[1].startswith("ref_"):
        referral_code = args[1].replace("ref_", "")
        
        # Находим реферера по коду
        users = load_data(USERS_FILE)
        referrer_id = None
        
        for uid, data in users.items():
            if data.get("referral_code") == referral_code and int(uid) != user_id:
                referrer_id = int(uid)
                referrer_name = data.get("first_name", "Пользователь")
                break
        
        # Если нашли реферера и у пользователя еще нет реферера
        if referrer_id and not user_data.get("referrer_id"):
            user_data["referrer_id"] = referrer_id
            update_user_data(user_id, user_data)
            
            welcome_text = (
                f"👋 Добро пожаловать, {message.from_user.first_name}!\n\n"
                f"✅ Вы зашли по реферальной ссылке от {referrer_name}!\n\n"
                f"💰 **Теперь {referrer_name} будет получать {REFERRAL_PERCENT}% с ваших покупок!**\n\n"
                f"👇 Начните выбор подписки или посмотрите свой профиль:"
            )
        else:
            welcome_text = (
                f"👋 Добро пожаловать, {message.from_user.first_name}!\n\n"
                f"👇 Начните выбор подписки или посмотрите свой профиль:"
            )
    else:
        welcome_text = (
            f"👋 Добро пожаловать, {message.from_user.first_name}!\n\n"
            f"👇 Начните выбор подписки или посмотрите свой профиль:"
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Выбрать подписку", callback_data="choose_subscription")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton(text="🎁 Реферальная система", callback_data="referral_system")],
        [InlineKeyboardButton(text="📝 Отзывы", url=REVIEWS_LINK)]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard)

# Команда /admin для администратора
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        await message.answer("❌ У вас нет прав доступа к этой команде!")
        return
    
    admin_text = (
        f"👑 **Панель администратора**\n\n"
        f"📊 **Статистика:**\n"
        f"• Пользователей: {len(load_data(USERS_FILE))}\n"
        f"• Заказов: {len(load_data(ORDERS_FILE))}\n"
        f"• Ключей: {len(load_data(KEYS_FILE))}\n"
        f"• Заблокированных: {len(load_data(BANNED_USERS_FILE))}\n\n"
        f"⚙️ **Доступные команды:**\n"
        f"/stats - Общая статистика\n"
        f"/users - Список пользователей\n"
        f"/orders - Список заказов\n"
        f"/broadcast - Рассылка сообщений\n"
        f"/ban - Заблокировать пользователя\n"
        f"/unban - Разблокировать пользователя\n"
        f"/addkey - Выдать ключ пользователю"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="📦 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🚫 Блокировка", callback_data="admin_ban")],
        [InlineKeyboardButton(text="✅ Разблокировка", callback_data="admin_unban")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
    ])
    
    await message.answer(admin_text, parse_mode="Markdown", reply_markup=keyboard)

# Рассылка сообщений - начало
@dp.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast_start(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ У вас нет прав доступа!")
        return
    
    await state.set_state(AdminStates.waiting_broadcast_message)
    
    text = (
        "📢 **Рассылка сообщений**\n\n"
        "Отправьте сообщение для рассылки всем пользователям бота.\n\n"
        "Вы можете отправить:\n"
        "• Текст\n"
        "• Текст с фотографией\n"
        "• Документ\n\n"
        "Для отмены нажмите /cancel"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback_query.answer()

# Обработка рассылки
@dp.message(AdminStates.waiting_broadcast_message)
async def admin_broadcast_process(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав доступа!")
        await state.clear()
        return
    
    if message.text and message.text.startswith("/cancel"):
        await message.answer("❌ Рассылка отменена.")
        await state.clear()
        return
    
    # Начинаем рассылку
    users = load_data(USERS_FILE)
    total_users = len(users)
    successful = 0
    failed = 0
    
    progress_msg = await message.answer(f"📢 Начинаю рассылку...\nВсего пользователей: {total_users}\n\n⏳ Обработано: 0/{total_users}")
    
    for i, (user_id_str, user_data) in enumerate(users.items(), 1):
        try:
            user_id = int(user_id_str)
            
            # Пропускаем забаненных пользователей
            if user_data.get("is_banned", False):
                continue
            
            # Отправляем сообщение в зависимости от типа
            if message.photo:
                await bot.send_photo(
                    user_id,
                    message.photo[-1].file_id,
                    caption=message.caption if message.caption else None,
                    parse_mode="Markdown" if message.caption and any(mark in message.caption for mark in ['*', '_', '`', '[']) else None
                )
            elif message.document:
                await bot.send_document(
                    user_id,
                    message.document.file_id,
                    caption=message.caption if message.caption else None,
                    parse_mode="Markdown" if message.caption and any(mark in message.caption for mark in ['*', '_', '`', '[']) else None
                )
            else:
                await bot.send_message(
                    user_id,
                    message.text,
                    parse_mode="Markdown" if any(mark in message.text for mark in ['*', '_', '`', '[']) else None
                )
            
            successful += 1
            
            # Обновляем прогресс каждые 10 пользователей
            if i % 10 == 0 or i == total_users:
                await progress_msg.edit_text(
                    f"📢 Рассылка...\nВсего пользователей: {total_users}\n\n"
                    f"✅ Успешно: {successful}\n"
                    f"❌ Ошибок: {failed}\n"
                    f"⏳ Обработано: {i}/{total_users}"
                )
            
            # Задержка чтобы не превысить лимиты Telegram
            await asyncio.sleep(0.1)
            
        except Exception as e:
            failed += 1
            print(f"Ошибка при отправке пользователю {user_id_str}: {e}")
    
    await state.clear()
    
    result_text = (
        f"✅ **Рассылка завершена!**\n\n"
        f"📊 **Результаты:**\n"
        f"• Всего пользователей: {total_users}\n"
        f"• Успешно доставлено: {successful}\n"
        f"• Не удалось доставить: {failed}\n"
        f"• Процент успеха: {successful/max(total_users, 1)*100:.1f}%\n\n"
        f"⏱️ Рассылка завершена: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    )
    
    await progress_msg.edit_text(result_text, parse_mode="Markdown")
    await message.answer("✅ Рассылка завершена!")

# Блокировка пользователя - начало
@dp.callback_query(lambda c: c.data == "admin_ban")
async def admin_ban_start(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ У вас нет прав доступа!")
        return
    
    await state.set_state(AdminStates.waiting_user_id_for_ban)
    
    banned_users = load_data(BANNED_USERS_FILE)
    text = (
        f"🚫 **Блокировка пользователя**\n\n"
        f"Введите ID пользователя для блокировки.\n\n"
        f"📊 Сейчас заблокировано: {len(banned_users)} пользователей\n\n"
        f"ℹ️ **Как найти ID пользователя:**\n"
        f"1. Попросите пользователя отправить /id\n"
        f"2. Или найдите в списке пользователей\n\n"
        f"Для отмены нажмите /cancel"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback_query.answer()

# Обработка блокировки
@dp.message(AdminStates.waiting_user_id_for_ban)
async def admin_ban_process(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав доступа!")
        await state.clear()
        return
    
    if message.text.startswith("/cancel"):
        await message.answer("❌ Блокировка отменена.")
        await state.clear()
        return
    
    try:
        user_id = int(message.text)
        user_data = get_user_data(user_id)
        
        # Проверяем, не забанен ли уже
        if is_user_banned(user_id):
            await message.answer(f"❌ Пользователь {user_id} уже заблокирован!")
            await state.clear()
            return
        
        # Блокируем пользователя
        ban_user(user_id, reason="Блокировка администратором", admin_id=message.from_user.id)
        
        # Отправляем уведомление пользователю
        try:
            await bot.send_message(
                user_id,
                "❌ **Вы были заблокированы в боте!**\n\n"
                "Для разблокировки свяжитесь с администратором.",
                parse_mode="Markdown"
            )
        except:
            pass
        
        await message.answer(
            f"✅ **Пользователь заблокирован!**\n\n"
            f"👤 ID: {user_id}\n"
            f"👋 Имя: {user_data.get('first_name', 'Неизвестно')}\n"
            f"📛 Username: @{user_data.get('username', 'нет')}\n"
            f"📅 Заблокирован: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"👮 Администратор: {message.from_user.full_name}"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите числовой ID пользователя.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при блокировке: {e}")
        await state.clear()

# Разблокировка пользователя - начало
@dp.callback_query(lambda c: c.data == "admin_unban")
async def admin_unban_start(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ У вас нет прав доступа!")
        return
    
    await state.set_state(AdminStates.waiting_user_id_for_unban)
    
    banned_users = load_data(BANNED_USERS_FILE)
    
    if not banned_users:
        text = "✅ Нет заблокированных пользователей."
        await callback_query.message.edit_text(text)
        await state.clear()
        return
    
    # Формируем список заблокированных
    banned_list = "🚫 **Заблокированные пользователи:**\n\n"
    for user_id_str, ban_info in list(banned_users.items())[:20]:  # Показываем первые 20
        user_id = int(user_id_str)
        user_data = get_user_data(user_id)
        banned_date = datetime.fromisoformat(ban_info['banned_at']).strftime('%d.%m.%Y %H:%M')
        banned_list += f"👤 ID: {user_id}\n"
        banned_list += f"👋 Имя: {user_data.get('first_name', 'Неизвестно')}\n"
        banned_list += f"📅 Заблокирован: {banned_date}\n"
        banned_list += f"📝 Причина: {ban_info.get('reason', 'Не указана')}\n\n"
    
    if len(banned_users) > 20:
        banned_list += f"... и еще {len(banned_users) - 20} пользователей\n\n"
    
    banned_list += "Введите ID пользователя для разблокировки.\nДля отмены нажмите /cancel"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
    ])
    
    await callback_query.message.edit_text(banned_list, parse_mode="Markdown", reply_markup=keyboard)
    await callback_query.answer()

# Обработка разблокировки
@dp.message(AdminStates.waiting_user_id_for_unban)
async def admin_unban_process(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав доступа!")
        await state.clear()
        return
    
    if message.text.startswith("/cancel"):
        await message.answer("❌ Разблокировка отменена.")
        await state.clear()
        return
    
    try:
        user_id = int(message.text)
        
        # Проверяем, забанен ли пользователь
        if not is_user_banned(user_id):
            await message.answer(f"❌ Пользователь {user_id} не заблокирован!")
            await state.clear()
            return
        
        # Разблокируем пользователя
        if unban_user(user_id):
            user_data = get_user_data(user_id)
            
            # Отправляем уведомление пользователю
            try:
                await bot.send_message(
                    user_id,
                    "✅ **Ваша блокировка снята!**\n\n"
                    "Теперь вы снова можете пользоваться ботом.",
                    parse_mode="Markdown"
                )
            except:
                pass
            
            await message.answer(
                f"✅ **Пользователь разблокирован!**\n\n"
                f"👤 ID: {user_id}\n"
                f"👋 Имя: {user_data.get('first_name', 'Неизвестно')}\n"
                f"📛 Username: @{user_data.get('username', 'нет')}\n"
                f"📅 Разблокирован: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                f"👮 Администратор: {message.from_user.full_name}"
            )
        else:
            await message.answer("❌ Ошибка при разблокировке пользователя.")
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите числовой ID пользователя.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при разблокировке: {e}")
        await state.clear()

# Отмена админских действий
@dp.callback_query(lambda c: c.data == "admin_cancel")
async def admin_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ У вас нет прав доступа!")
        return
    
    await state.clear()
    await callback_query.message.edit_text("❌ Действие отменено.")
    await callback_query.answer()

# Команда /id для получения своего ID
@dp.message(Command("id"))
async def cmd_id(message: types.Message):
    user_id = message.from_user.id
    
    if is_user_banned(user_id):
        await message.answer("❌ Вы заблокированы в этом боте.")
        return
    
    user_data = get_user_data(user_id)
    
    text = (
        f"👤 **Ваши данные:**\n\n"
        f"🆔 **Ваш ID:** `{user_id}`\n"
        f"👋 **Имя:** {message.from_user.full_name}\n"
        f"📛 **Username:** @{message.from_user.username or 'нет'}\n"
        f"📅 **Дата регистрации:** {datetime.fromisoformat(user_data['join_date']).strftime('%d.%m.%Y %H:%M')}\n\n"
        f"🔗 **Ваша реферальная ссылка:**\n"
        f"`{get_referral_link(user_id)}`\n\n"
        f"💡 **ID нужен для:**\n"
        f"• Обращения к администратору\n"
        f"• Проверки статуса заказа\n"
        f"• Получения помощи"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать ID", callback_data=f"copy_id_{user_id}")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

# Личный профиль пользователя (обновлен с проверкой бана)
@dp.callback_query(lambda c: c.data == "my_profile")
async def my_profile(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Проверяем, не забанен ли пользователь
    if is_user_banned(user_id):
        await callback_query.message.answer("❌ Вы заблокированы в этом боте. Для разблокировки свяжитесь с администратором.")
        await callback_query.answer()
        return
    
    user_data = get_user_data(user_id)
    
    # Получаем информацию о активном ключе
    active_key_info = ""
    if user_data.get("active_key"):
        active_key_info = f"🔑 **Ваш ключ:** `{user_data['active_key']}`\n"
        
        keys = load_data(KEYS_FILE)
        key_info = keys.get(user_data["active_key"], {})
        
        if key_info:
            if key_info.get("expires_at"):
                expires_date = datetime.fromisoformat(key_info["expires_at"])
                now = datetime.now()
                
                if expires_date > now:
                    days_left = (expires_date - now).days
                    hours_left = (expires_date - now).seconds // 3600
                    active_key_info += f"⏳ Осталось: {days_left} дн. {hours_left} ч.\n"
                    expires_text = f"📅 Истекает: {expires_date.strftime('%d.%m.%Y %H:%M')}"
                else:
                    active_key_info += "❌ Ключ истек\n"
                    expires_text = "📅 Истек"
            else:
                active_key_info += "✅ Ключ активен\n"
                expires_text = "📅 Истекает: НИКОГДА"
        else:
            active_key_info += "✅ Ключ активен (общий ключ)\n"
            expires_text = "📅 Истекает: НИКОГДА"
    else:
        active_key_info = "❌ Нет активных ключей\n"
        expires_text = ""
    
    # Формируем текст профиля
    profile_text = (
        f"👤 **Ваш профиль**\n\n"
        f"🆔 ID: {user_id}\n"
        f"👋 Имя: {user_data.get('first_name', 'Неизвестно')}\n"
        f"📅 Дата регистрации: {datetime.fromisoformat(user_data['join_date']).strftime('%d.%m.%Y %H:%M')}\n\n"
        f"💰 **Баланс:** {user_data.get('balance', 0)} RUB\n"
        f"💵 Всего заработано: {user_data.get('total_earned', 0)} RUB\n"
        f"💸 Всего потрачено: {user_data.get('total_spent', 0)} RUB\n"
        f"💳 Всего выведено: {user_data.get('total_withdrawn', 0)} RUB\n"
        f"📦 Заказов: {user_data.get('orders_count', 0)}\n\n"
        f"🔑 **Активная подписка:**\n"
        f"{active_key_info}"
    )
    
    if user_data.get("active_key"):
        profile_text += f"{expires_text}\n\n"
    
    if user_data.get("referrals"):
        referrals_count = len(user_data["referrals"])
        profile_text += f"👥 Рефералов: {referrals_count} чел.\n"
    
    # Кнопки профиля
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="my_profile")],
        [InlineKeyboardButton(text="🎁 Реферальная система", callback_data="referral_system")],
        [InlineKeyboardButton(text="💰 Вывести средства", callback_data="withdraw_funds")],
        [InlineKeyboardButton(text="📝 Посмотреть отзывы", url=REVIEWS_LINK)],
        [InlineKeyboardButton(text="🛒 Купить подписку", callback_data="choose_subscription")],
        [InlineKeyboardButton(text="🆔 Мой ID", callback_data=f"copy_id_{user_id}")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu")]
    ])
    
    await callback_query.message.edit_text(profile_text, parse_mode="Markdown", reply_markup=keyboard)
    await callback_query.answer()

# Копирование ID
@dp.callback_query(lambda c: c.data.startswith("copy_id_"))
async def copy_id_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.answer(f"Ваш ID: {user_id} скопирован!")
    
    # Отправляем сообщение с ID для копирования
    await callback_query.message.answer(
        f"🆔 **Ваш ID для копирования:**\n"
        f"```\n{user_id}\n```\n\n"
        f"📋 Выделите и скопируйте ID выше",
        parse_mode="Markdown"
    )

# Главное меню (с проверкой бана)
@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Проверяем, не забанен ли пользователь
    if is_user_banned(user_id):
        await callback_query.message.answer("❌ Вы заблокированы в этом боте. Для разблокировки свяжитесь с администратором.")
        await callback_query.answer()
        return
    
    welcome_text = (
        f"👋 Добро пожаловать, {callback_query.from_user.first_name}!\n\n"
        f"👇 Выберите действие:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Выбрать подписку", callback_data="choose_subscription")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton(text="🎁 Реферальная система", callback_data="referral_system")],
        [InlineKeyboardButton(text="📝 Отзывы", url=REVIEWS_LINK)]
    ])
    
    await callback_query.message.edit_text(welcome_text, reply_markup=keyboard)
    await callback_query.answer()

# Начало выбора подписки (с проверкой бана)
@dp.callback_query(lambda c: c.data == "choose_subscription")
async def start_subscription_choice(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    
    # Проверяем, не забанен ли пользователь
    if is_user_banned(user_id):
        await callback_query.message.answer("❌ Вы заблокированы в этом боте. Для разблокировки свяжитесь с администратором.")
        await callback_query.answer()
        return
    
    await state.clear()
    device_text = "📱 **На какое устройство нужен DLC?**"
    
    device_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Android устройство (APK)", callback_data="select_device_apk")],
        [InlineKeyboardButton(text="💻 Эмулятор/ПК", callback_data="select_device_emulator")],
        [InlineKeyboardButton(text="🍎 iOS устройство (IPA)", callback_data="select_device_ios")],
        [InlineKeyboardButton(text="📝 Посмотреть отзывы", url=REVIEWS_LINK)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    
    await callback_query.message.edit_text(device_text, parse_mode="Markdown", reply_markup=device_keyboard)
    await callback_query.answer()

# Выбор устройства (APK) - ИСПРАВЛЕНО: все периоды сразу
@dp.callback_query(lambda c: c.data == "select_device_apk")
async def process_device_apk(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(
        device_type="apk",
        device_name=DEVICES["apk"]["name"]
    )
    await state.set_state(PurchaseStates.waiting_for_period)
    
    # Создаем клавиатуру с ВСЕМИ периодами сразу
    period_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="7 дней - 300 RUB", callback_data="select_period_7_days"),
            InlineKeyboardButton(text="30 дней - 450 RUB", callback_data="select_period_30_days")
        ],
        [
            InlineKeyboardButton(text="Вечно - 650 RUB", callback_data="select_period_forever")
        ],
        [
            InlineKeyboardButton(text="🔍 Посмотреть обзор", url=FUNCTIONALITY_REVIEW_LINK),
            InlineKeyboardButton(text="📝 Отзывы", url=REVIEWS_LINK)
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="choose_subscription")
        ]
    ])
    
    await callback_query.message.edit_text(
        DEVICES["apk"]["description"],
        parse_mode="Markdown",
        reply_markup=period_keyboard
    )
    await callback_query.answer()

# Выбор устройства (Emulator) - ИСПРАВЛЕНО: все периоды сразу
@dp.callback_query(lambda c: c.data == "select_device_emulator")
async def process_device_emulator(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(
        device_type="emulator",
        device_name=DEVICES["emulator"]["name"]
    )
    await state.set_state(PurchaseStates.waiting_for_period)
    
    # Создаем клавиатуру с ВСЕМИ периодами сразу
    period_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="7 дней - 300 RUB", callback_data="select_period_7_days"),
            InlineKeyboardButton(text="30 дней - 450 RUB", callback_data="select_period_30_days")
        ],
        [
            InlineKeyboardButton(text="Вечно - 650 RUB", callback_data="select_period_forever")
        ],
        [
            InlineKeyboardButton(text="🔍 Посмотреть обзор", url=FUNCTIONALITY_REVIEW_LINK),
            InlineKeyboardButton(text="📝 Отзывы", url=REVIEWS_LINK)
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="choose_subscription")
        ]
    ])
    
    await callback_query.message.edit_text(
        DEVICES["emulator"]["description"],
        parse_mode="Markdown",
        reply_markup=period_keyboard
    )
    await callback_query.answer()

# Выбор устройства (iOS) - ИСПРАВЛЕНО: все периоды сразу
@dp.callback_query(lambda c: c.data == "select_device_ios")
async def process_device_ios(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(
        device_type="ios",
        device_name=DEVICES["ios"]["name"]
    )
    await state.set_state(PurchaseStates.waiting_for_period)
    
    # Создаем клавиатуру с ВСЕМИ периодами сразу
    period_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="7 дней - 300 RUB", callback_data="select_period_7_days"),
            InlineKeyboardButton(text="30 дней - 450 RUB", callback_data="select_period_30_days")
        ],
        [
            InlineKeyboardButton(text="Вечно - 650 RUB", callback_data="select_period_forever")
        ],
        [
            InlineKeyboardButton(text="🔍 Посмотреть обзор", url=FUNCTIONALITY_REVIEW_LINK),
            InlineKeyboardButton(text="📝 Отзывы", url=REVIEWS_LINK)
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="choose_subscription")
        ]
    ])
    
    await callback_query.message.edit_text(
        DEVICES["ios"]["description"],
        parse_mode="Markdown",
        reply_markup=period_keyboard
    )
    await callback_query.answer()

# Выбор срока подписки (остается без изменений)
@dp.callback_query(lambda c: c.data.startswith("select_period_"))
async def process_period_choice(callback_query: types.CallbackQuery, state: FSMContext):
    period_id = callback_query.data.replace("select_period_", "")
    
    if period_id not in SUBSCRIPTION_PERIODS:
        await callback_query.answer("Неверный срок подписки!")
        return
    
    period_info = SUBSCRIPTION_PERIODS[period_id]
    
    await state.update_data(
        period_id=period_id,
        period_name=period_info["name"],
        period_price=period_info["price"],
        period_days=period_info["days"]
    )
    await state.set_state(PurchaseStates.waiting_for_payment_method)
    
    data = await state.get_data()
    device_name = data.get("device_name")
    
    summary_text = (
        f"✅ **Вы выбрали:**\n"
        f"📱 Устройство: {device_name}\n"
        f"⏳ Срок подписки: {period_info['name']}\n"
        f"💰 Цена: {period_info['price']} RUB\n"
        f"📅 Действует: {period_info['days']} дней\n\n"
        f"💳 **Выберите удобный вам метод для оплаты:**"
    )
    
    payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 Тинькофф", callback_data="select_payment_tinkoff"),
            InlineKeyboardButton(text="🏦 СБП Сбербанк", callback_data="select_payment_sber_sbp")
        ],
        [InlineKeyboardButton(text="📝 Посмотреть отзывы", url=REVIEWS_LINK)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="choose_subscription")]
    ])
    
    await callback_query.message.edit_text(summary_text, parse_mode="Markdown", reply_markup=payment_keyboard)
    await callback_query.answer()

# Выбор метода оплаты (остается без изменений)
@dp.callback_query(lambda c: c.data in ["select_payment_tinkoff", "select_payment_sber_sbp"])
async def process_payment_method(callback_query: types.CallbackQuery, state: FSMContext):
    payment_method = callback_query.data.replace("select_payment_", "")
    
    if payment_method not in ["tinkoff", "sber_sbp"]:
        await callback_query.answer("Неверный выбор!")
        return
    
    data = await state.get_data()
    device_name = data.get("device_name")
    period_name = data.get("period_name")
    period_price = data.get("period_price")
    period_days = data.get("period_days")
    
    await state.update_data(payment_method=payment_method)
    await state.set_state(PurchaseStates.waiting_for_receipt)
    
    payment_details = PAYMENT_DETAILS[payment_method]
    
    if payment_method == "tinkoff":
        payment_text = (
            f"💳 **Вы выбрали оплату через {payment_details['name']}**\n\n"
            f"📱 **Устройство:** {device_name}\n"
            f"⏳ **Срок подписки:** {period_name}\n"
            f"💰 **Сумма к оплате:** {period_price} RUB\n"
            f"📅 **Действует:** {period_days} дней\n\n"
            f"🔢 **Реквизиты для оплаты:**\n"
            f"Номер карты: `{payment_details['card_number']}`\n\n"
            f"ℹ️ **{payment_details['instructions']}**\n\n"
            f"📋 **Инструкция по оплате:**\n"
            f"1. Переведите {period_price} RUB на указанную карту\n"
            f"2. Сохраните чек об оплате (скриншот или фото)\n"
            f"3. Отправьте чек в этот чат\n\n"
            f"✅ **Товар выдается сразу после подтверждения платежа!**\n\n"
            f"⚠️ **ВНИМАНИЕ:** Обязательно отправьте чек для подтверждения оплаты!"
        )
    else:  # sber_sbp
        payment_text = (
            f"🏦 **Вы выбрали оплату через {payment_details['name']}**\n\n"
            f"📱 **Устройство:** {device_name}\n"
            f"⏳ **Срок подписки:** {period_name}\n"
            f"💰 **Сумма к оплате:** {period_price} RUB\n"
            f"📅 **Действует:** {period_days} дней\n\n"
            f"📱 **Реквизиты для оплаты:**\n"
            f"Номер телефона для СБП: `{payment_details['phone_number']}`\n\n"
            f"ℹ️ **{payment_details['instructions']}**\n\n"
            f"📋 **Инструкция по оплате через СБП:**\n"
            f"1. Откройте приложение вашего банка\n"
            f"2. Найдите раздел 'СБП' или 'Быстрые платежи'\n"
            f"3. Введите номер телефона: {payment_details['phone_number']}\n"
            f"4. Укажите сумму: {period_price} RUB\n"
            f"5. Подтвердите платеж\n"
            f"6. Сохраните чек об оплате (скриншот)\n"
            f"7. Отправьте чек в этот чат\n\n"
            f"✅ **Товар выдается сразу после подтверждения платежа!**\n\n"
            f"⚠️ **ВНИМАНИЕ:** Обязательно отправьте чек для подтверждения оплаты!"
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Посмотреть отзывы", url=REVIEWS_LINK)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="choose_subscription")]
    ])
    
    await callback_query.message.edit_text(payment_text, parse_mode="Markdown", reply_markup=keyboard)
    await callback_query.answer()

# Обработка чека
@dp.message(PurchaseStates.waiting_for_receipt)
async def process_receipt(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Проверяем, не забанен ли пользователь
    if is_user_banned(user_id):
        await message.answer("❌ Вы заблокированы в этом боте. Для разблокировки свяжитесь с администратором.")
        await state.clear()
        return
    
    if not (message.photo or message.document):
        await message.answer("❌ Пожалуйста, отправьте фото или скриншот чека об оплате!")
        return
    
    await send_receipt_to_admin(message, state)
    await process_order_for_user(message, state)

async def send_receipt_to_admin(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        device_name = data.get("device_name")
        period_name = data.get("period_name")
        period_price = data.get("period_price")
        payment_method = data.get("payment_method")
        
        payment_details = PAYMENT_DETAILS.get(payment_method, {})
        payment_name = payment_details.get("name", "Неизвестный метод")
        
        admin_text = (
            f"📸 **Новый чек получен!**\n\n"
            f"👤 **Пользователь:**\n"
            f"ID: {message.from_user.id}\n"
            f"Username: @{message.from_user.username or 'нет'}\n"
            f"Имя: {message.from_user.full_name}\n\n"
            f"📋 **Информация о заказе:**\n"
            f"📱 Устройство: {device_name}\n"
            f"⏳ Срок: {period_name}\n"
            f"💰 Сумма: {period_price} RUB\n"
            f"💳 Метод оплаты: {payment_name}\n"
            f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        
        if message.photo:
            photo = message.photo[-1]
            await bot.send_photo(
                ADMIN_ID, 
                photo.file_id,
                caption=f"📸 Чек от @{message.from_user.username or 'пользователя'}"
            )
        elif message.document:
            await bot.send_document(
                ADMIN_ID,
                message.document.file_id,
                caption=f"📄 Чек от @{message.from_user.username or 'пользователя'}"
            )
            
    except Exception as e:
        print(f"Ошибка при отправке чека админу: {e}")

async def process_order_for_user(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        data = await state.get_data()
        device_name = data.get("device_name")
        period_name = data.get("period_name")
        period_price = data.get("period_price")
        payment_method = data.get("payment_method")
        period_days = data.get("period_days")
        device_type = data.get("device_type", "apk")
        
        order_id = generate_order_id()
        payment_details = PAYMENT_DETAILS.get(payment_method, {})
        payment_name = payment_details.get("name", "Неизвестный метод")
        
        order_info = {
            "user_id": user_id,
            "username": message.from_user.username,
            "full_name": f"{message.from_user.first_name} {message.from_user.last_name or ''}",
            "device_name": device_name,
            "device_type": device_type,
            "period_name": period_name,
            "period_price": period_price,
            "period_days": period_days,
            "payment_method": payment_method,
            "payment_method_name": payment_name,
            "order_id": order_id,
            "status": "pending",
            "timestamp": datetime.now().isoformat(),
            "key": None
        }
        
        orders = load_data(ORDERS_FILE)
        orders[order_id] = order_info
        save_data(ORDERS_FILE, orders)
        
        user_data = get_user_data(user_id)
        user_data["total_spent"] = user_data.get("total_spent", 0) + period_price
        user_data["orders_count"] = user_data.get("orders_count", 0) + 1
        update_user_data(user_id, user_data)
        
        confirmation_text = (
            f"✅ **Чек получен!**\n\n"
            f"📋 **Детали заказа:**\n"
            f"🆔 **Номер заказа:** {order_id}\n"
            f"📱 Устройство: {device_name}\n"
            f"⏳ Срок подписки: {period_name}\n"
            f"💰 Сумма: {period_price} RUB\n"
            f"💳 Метод оплаты: {payment_name}\n\n"
            f"⏳ **Чек отправлен на проверку администратору...**\n\n"
            f"✅ **Товар будет отправлен вам сразу после подтверждения платежа!**"
        )
        
        await message.answer(confirmation_text, parse_mode="Markdown")
        
        # Отправляем уведомление администратору
        admin_text = (
            f"🆔 **НОВЫЙ ЗАКАЗ: {order_id}**\n\n"
            f"👤 **Пользователь:**\n"
            f"ID: {user_id}\n"
            f"Username: @{message.from_user.username or 'нет'}\n"
            f"Имя: {message.from_user.full_name}\n\n"
            f"📋 **Детали заказа:**\n"
            f"📱 Устройство: {device_name}\n"
            f"⏳ Срок: {period_name}\n"
            f"💰 Сумма: {period_price} RUB\n"
            f"💳 Метод оплаты: {payment_name}\n"
            f"📅 Создан: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять заказ", callback_data=f"approve_{order_id}"),
                InlineKeyboardButton(text="❌ Отклонить заказ", callback_data=f"reject_{order_id}")
            ]
        ])
        
        await bot.send_message(
            ADMIN_ID, 
            admin_text, 
            parse_mode="Markdown",
            reply_markup=admin_keyboard
        )
        
        await state.clear()
        
    except Exception as e:
        print(f"Ошибка при обработке заказа: {e}")
        await message.answer("❌ Произошла ошибка при обработке заказа. Попробуйте еще раз.")

# Обновленная функция process_admin_action для выдачи общего ключа
@dp.callback_query(lambda c: c.data.startswith("approve_") or c.data.startswith("reject_"))
async def process_admin_action(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Проверка прав администратора
    if user_id != ADMIN_ID:
        await callback_query.answer("У вас нет прав для этого действия!")
        return
    
    # Разбираем callback_data
    if callback_query.data.startswith("approve_"):
        action = "approve"
        order_id = callback_query.data.replace("approve_", "")
    else:  # reject_
        action = "reject"
        order_id = callback_query.data.replace("reject_", "")
    
    print(f"Обработка действия администратора: {action} для заказа {order_id}")
    
    orders = load_data(ORDERS_FILE)
    if order_id not in orders:
        await callback_query.answer("Заказ не найден!")
        return
    
    order_info = orders[order_id]
    order_user_id = order_info["user_id"]
    payment_name = order_info.get("payment_method_name", "Неизвестный метод")
    period_price = order_info.get("period_price", 0)
    
    if action == "approve":
        # Используем общий ключ
        key = COMMON_KEY
        period_days = order_info.get("period_days", 7)
        device_type = order_info.get("device_type", "apk")
        
        if period_days == "навсегда":
            period_days_for_key = 9999
        else:
            period_days_for_key = period_days
        
        # Сохраняем информацию о выдаче ключа
        keys = load_data(KEYS_FILE)
        if key not in keys:
            keys[key] = {
                "order_id": order_id,
                "created_at": datetime.now().isoformat(),
                "expires_at": None if period_days == "навсегда" else (
                    datetime.now() + timedelta(days=period_days_for_key)
                ).isoformat(),
                "is_used": False,
                "period_days": period_days_for_key,
                "device_type": device_type,
                "is_common": True
            }
        save_data(KEYS_FILE, keys)
        
        # Обновляем заказ
        orders[order_id]["status"] = "approved"
        orders[order_id]["approved_at"] = datetime.now().isoformat()
        orders[order_id]["key"] = key
        orders[order_id]["approved_by"] = user_id
        save_data(ORDERS_FILE, orders)
        
        # Обновляем данные пользователя
        user_data = get_user_data(order_user_id)
        user_data["active_key"] = key
        user_data["key_expires"] = None if period_days == "навсегда" else (
            datetime.now() + timedelta(days=period_days_for_key)
        ).isoformat()
        update_user_data(order_user_id, user_data)
        
        # Обрабатываем реферальную систему
        referral_bonus = process_referral_system(order_user_id, period_price)
        
        # Определяем название товара в зависимости от типа устройства
        device_name = order_info['device_name']
        if "Android" in device_name or "APK" in device_name:
            product_name = "St2 Internal APK"
        elif "Emulator" in device_name or "ПК" in device_name:
            product_name = "St2 Internal PC"
        elif "iOS" in device_name:
            product_name = "St2 Internal iOS"
        else:
            product_name = "St2 Internal"
        
        # Отправляем сообщение пользователю в новом формате
        user_message = (
            f"💋 **Спасибо вам за покупку!**\n\n"
            f"🔑 **Ваш Ключ:** `{key}`\n"
            f"🛒 **Товар:** {product_name}\n"
            f"⏳ **Срок товара:** {period_days} дней\n\n"
            f"🎮 **Спасибо за доверие! Приятной игры!**"
        )
        
        # Кнопки для пользователя (обновленная ссылка на DLC)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬇️ СКАЧАТЬ DLC", url=DLC_DOWNLOAD_LINK)],
            [InlineKeyboardButton(text="📋 Скопировать ключ", callback_data=f"copy_key_{key}")],
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
            [InlineKeyboardButton(text="🛒 Сделать новый заказ", callback_data="choose_subscription")]
        ])
        
        try:
            await bot.send_message(order_user_id, user_message, parse_mode="Markdown", reply_markup=keyboard)
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю: {e}")
        
        # Подтверждение администратору
        bonus_text = f"\n🎁 Реферальный бонус: {referral_bonus} RUB" if referral_bonus > 0 else ""
        
        try:
            await callback_query.message.edit_text(
                f"✅ **Заказ {order_id} ПРИНЯТ**\n\n"
                f"👤 Пользователь: @{order_info['username'] or 'нет'}\n"
                f"💰 Сумма: {period_price} RUB\n"
                f"💳 Метод: {payment_name}\n"
                f"🔑 Ключ: {key}\n"
                f"{bonus_text}\n"
                f"📅 Время подтверждения: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                parse_mode="Markdown",
                reply_markup=None
            )
        except Exception as e:
            print(f"Ошибка при редактировании сообщения: {e}")
        
        await callback_query.answer(f"Заказ {order_id} принят! Ключ отправлен.")
        
    else:  # reject
        orders[order_id]["status"] = "rejected"
        orders[order_id]["rejected_at"] = datetime.now().isoformat()
        orders[order_id]["rejected_by"] = user_id
        save_data(ORDERS_FILE, orders)
        
        user_message = (
            f"❌ **Заказ отклонен**\n\n"
            f"🆔 **Номер заказа:** {order_id}\n"
            f"💳 **Метод оплаты:** {payment_name}\n\n"
            f"⚠️ **Ваш платеж не подтвержден администратором.**\n\n"
            f"💬 **Для уточнения деталей свяжитесь с поддержкой.**"
        )
        
        try:
            await bot.send_message(order_user_id, user_message, parse_mode="Markdown")
        except:
            pass
        
        try:
            await callback_query.message.edit_text(
                f"❌ **Заказ {order_id} ОТКЛОНЕН**\n\n"
                f"👤 Пользователь: @{order_info['username'] or 'нет'}\n"
                f"💰 Сумма: {period_price} RUB\n"
                f"💳 Метод: {payment_name}\n"
                f"📅 Время отклонения: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                parse_mode="Markdown",
                reply_markup=None
            )
        except:
            await callback_query.message.answer(
                f"❌ Заказ {order_id} отклонен!",
                parse_mode="Markdown"
            )
        
        await callback_query.answer(f"Заказ {order_id} отклонен!")

# Обработчик копирования ключа
@dp.callback_query(lambda c: c.data.startswith("copy_key_"))
async def copy_key_handler(callback_query: types.CallbackQuery):
    key = callback_query.data.replace("copy_key_", "")
    
    await callback_query.answer(f"Ключ скопирован: {key}")
    
    # Отправляем сообщение с ключом для копирования
    await callback_query.message.answer(
        f"🔑 **Ваш ключ для копирования:**\n"
        f"```\n{key}\n```\n\n"
        f"📋 Выделите и скопируйте ключ выше",
        parse_mode="Markdown"
    )

# Вывод средств
@dp.callback_query(lambda c: c.data == "withdraw_funds")
async def withdraw_funds(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Проверяем, не забанен ли пользователь
    if is_user_banned(user_id):
        await callback_query.message.answer("❌ Вы заблокированы в этом боте. Для разблокировки свяжитесь с администратором.")
        await callback_query.answer()
        return
    
    user_data = get_user_data(user_id)
    balance = user_data.get("balance", 0)
    
    if balance < MIN_WITHDRAWAL:
        text = (
            f"💰 **Вывод средств**\n\n"
            f"❌ Минимальная сумма для вывода: {MIN_WITHDRAWAL} RUB\n"
            f"💳 Ваш текущий баланс: {balance} RUB\n\n"
            f"💡 **Чтобы вывести средства:**\n"
            f"1. Пригласите друзей по реферальной ссылке\n"
            f"2. Когда они купят подписку, вы получите {REFERRAL_PERCENT}%\n"
            f"3. Когда баланс достигнет {MIN_WITHDRAWAL} RUB, свяжитесь с администратором\n\n"
            f"🎁 Приглашайте больше друзей, чтобы накопить нужную сумму!"
        )
    else:
        text = (
            f"💰 **Вывод средств**\n\n"
            f"✅ Доступно для вывода: {balance} RUB\n"
            f"🎯 Минимальная сумма: {MIN_WITHDRAWAL} RUB\n\n"
            f"📞 **Для вывода средств:**\n"
            f"1. Свяжитесь с администратором: @admin_username\n"
            f"2. Укажите сумму вывода (мин. {MIN_WITHDRAWAL} RUB)\n"
            f"3. Предоставьте реквизиты для перевода\n"
            f"4. Сообщите ваш ID: `{user_id}`\n\n"
            f"⚠️ **Внимание:** Вывод осуществляется вручную администратором в течение 24 часов."
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton(text="🎁 Реферальная система", callback_data="referral_system")],
        [InlineKeyboardButton(text="📝 Посмотреть отзывы", url=REVIEWS_LINK)],
        [InlineKeyboardButton(text="💬 Связаться с админом", url="https://t.me/admin_username")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback_query.answer()

# Реферальная система (с проверкой бана)
@dp.callback_query(lambda c: c.data == "referral_system")
async def referral_system(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Проверяем, не забанен ли пользователь
    if is_user_banned(user_id):
        await callback_query.message.answer("❌ Вы заблокированы в этом боте. Для разблокировки свяжитесь с администратором.")
        await callback_query.answer()
        return
    
    user_data = get_user_data(user_id)
    
    referral_link = get_referral_link(user_id)
    referrals_count = len(user_data.get("referrals", []))
    total_earned = user_data.get("total_earned", 0)
    balance = user_data.get("balance", 0)
    total_withdrawn = user_data.get("total_withdrawn", 0)
    
    # Подсчитываем доход от рефералов за последние 30 дней
    last_month_income = 0
    if os.path.exists("referral_transactions.json"):
        transactions = load_data("referral_transactions.json")
        month_ago = datetime.now() - timedelta(days=30)
        
        for transaction in transactions.values():
            if transaction.get("referrer_id") == user_id:
                transaction_date = datetime.fromisoformat(transaction.get("timestamp", datetime.now().isoformat()))
                if transaction_date > month_ago:
                    last_month_income += transaction.get("bonus", 0)
    
    # Создаем текст для кнопки "Поделиться"
    share_text = f"🎮 Привет! Заходи в бота магазина NeworkPC по моей ссылке!\n\n🔥 Получи крутые подписки на NeworkPC!\n\n🔗 {referral_link}"
    
    referral_text = (
        f"🎁 **Реферальная система**\n\n"
        f"💰 **Вы получаете {REFERRAL_PERCENT}% с каждой покупки ваших рефералов!**\n\n"
        f"📊 **Ваша статистика:**\n"
        f"👥 Приглашено пользователей: {referrals_count}\n"
        f"💵 Всего заработано: {total_earned} RUB\n"
        f"📈 За последний месяц: {last_month_income} RUB\n"
        f"💳 Текущий баланс: {balance} RUB\n"
        f"💸 Всего выведено: {total_withdrawn} RUB\n"
        f"🎯 Минимальный вывод: {MIN_WITHDRAWAL} RUB\n\n"
        f"🔗 **Ваша реферальная ссылка:**\n"
        f"`{referral_link}`\n\n"
        f"📋 **Как это работает:**\n"
        f"1. Поделитесь своей ссылкой с друзьями\n"
        f"2. Они должны перейти по ссылке и зарегистрироваться\n"
        f"3. Когда они купят подписку\n"
        f"4. Вы получите {REFERRAL_PERCENT}% от их покупки!\n\n"
        f"💡 **Совет:** Чем больше пригласите, тем больше заработаете!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться ссылкой", 
                             url=f"https://t.me/share/url?url={referral_link}&text={share_text}")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton(text="💰 Вывести средства", callback_data="withdraw_funds")],
        [InlineKeyboardButton(text="📝 Посмотреть отзывы", url=REVIEWS_LINK)],
        [InlineKeyboardButton(text="📊 Мои рефералы", callback_data="my_referrals")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    
    await callback_query.message.edit_text(referral_text, parse_mode="Markdown", reply_markup=keyboard)
    await callback_query.answer()

# Основная функция
async def main():
    # Инициализируем файлы
    init_files()
    
    print("=" * 60)
    print("🤖 БОТ NeworkPC Private Key Shop")
    print("=" * 60)
    print(f"👑 Администратор: {ADMIN_ID}")
    print(f"🔗 Приватная группа: {PRIVATE_GROUP_LINK}")
    print(f"📝 Отзывы: {REVIEWS_LINK}")
    print(f"🔍 Обзор функционала: {FUNCTIONALITY_REVIEW_LINK}")
    print(f"🔗 Скачать DLC: {DLC_DOWNLOAD_LINK}")
    print(f"🔑 Общий ключ: {COMMON_KEY}")
    print(f"💰 Реферальная комиссия: {REFERRAL_PERCENT}%")
    print(f"💸 Минимальный вывод: {MIN_WITHDRAWAL} RUB")
    print(f"🤝 Реферальные ссылки: https://t.me/{BOT_USERNAME}?start=ref_КОД")
    print("=" * 60)
    print("✅ Функции бота:")
    print("   • Личный кабинет с ключами")
    print("   • Реферальная система 15%")
    print("   • История заказов")
    print("   • Автоматическое начисление бонусов")
    print("   • Отзывы пользователей")
    print("   • Система блокировки пользователей")
    print("   • Рассылка сообщений от администратора")
    print("=" * 60)
    print("📱 Поддерживаемые устройства:")
    print("   • Android (APK)")
    print("   • Эмулятор/ПК")
    print("   • iOS (IPA)")
    print("=" * 60)
    print("✅ Поддерживаемые способы входа: Google, VK, Facebook, Game Center")
    print("=" * 60)
    print("🚀 Бот запущен и готов к работе!")
    print("Для остановки нажмите Ctrl+C")
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n⛔ Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())
