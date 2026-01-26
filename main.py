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
# ID администратора
ADMIN_ID = 7165501889
# Ссылка на приватную группу
PRIVATE_GROUP_LINK = "https://t.me/+iL5qzjdLjjM4YTMy"
# Реферальная комиссия (15%)
REFERRAL_PERCENT = 15
# Username вашего бота (ВАЖНО: без @)
BOT_USERNAME = "NeworkPCprivatekeybot"

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
            "🔍 Функционал APK версии: посмотреть - \n\n"
            "✅ **Поддерживаются такие способы входа:**\n"
            "• Google аккаунт\n"
            "• VK\n"
            "• Facebook\n"
            "• Любой удобный способ!\n\n"
            "Выберите срок подписки ниже ⬇️"
        )
    },
    "emulator": {
        "name": "NeworkPC Emulator - БЕЗ рут прав",
        "description": (
            "💻 NeworkPC Emulator - БЕЗ рут прав\n\n"
            "🔥 Поддержка последней версии игры (0.37.0)\n\n"
            "🖥️ Работает на ПК через эмулятор Android\n\n"
            "🗽 Без рут прав!\n\n"
            "🔍 Функционал эмулятора: посмотреть - \n\n"
            "✅ **Поддерживаются такие способы входа:**\n"
            "• Google аккаунт\n"
            "• VK\n"
            "• Facebook\n"
            "• Любой удобный способ!\n\n"
            "Выберите срок подписки ниже ⬇️"
        )
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

# Функции для работы с данными
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_data(user_id):
    users = load_data(USERS_FILE)
    if str(user_id) not in users:
        users[str(user_id)] = {
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
            "last_activity": datetime.now().isoformat()
        }
        save_data(USERS_FILE, users)
    return users[str(user_id)]

def update_user_data(user_id, data):
    users = load_data(USERS_FILE)
    if str(user_id) not in users:
        get_user_data(user_id)
        users = load_data(USERS_FILE)
    
    users[str(user_id)].update(data)
    users[str(user_id)]["last_activity"] = datetime.now().isoformat()
    save_data(USERS_FILE, users)

def generate_order_id():
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

def generate_key(order_id, period_days):
    base_key = f"EU_NEWORKPC_{order_id.split('-')[1]}"
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    key = f"{base_key}_{random_part}"
    
    if period_days == "навсегда":
        expires_at = None
    else:
        expires_at = (datetime.now() + timedelta(days=period_days)).isoformat()
    
    keys = load_data(KEYS_FILE)
    keys[key] = {
        "order_id": order_id,
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at,
        "is_used": False,
        "period_days": period_days
    }
    save_data(KEYS_FILE, keys)
    
    return key

def generate_referral_code(user_id):
    code = f"REF{user_id % 10000:04d}{random.randint(100, 999)}"
    return code

def get_referral_link(user_id):
    user_data = get_user_data(user_id)
    referral_code = user_data["referral_code"]
    return f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}"

def process_referral_system(user_id, amount):
    """Обработка реферальной системы при покупке"""
    users = load_data(USERS_FILE)
    user_data = users.get(str(user_id), {})
    
    if "referrer_id" in user_data and user_data["referrer_id"]:
        referrer_id = user_data["referrer_id"]
        referrer_data = users.get(str(referrer_id), {})
        
        if referrer_data and not referrer_data.get("is_banned", False):
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
            
            users[str(referrer_id)] = referrer_data
            save_data(USERS_FILE, users)
            
            # Записываем реферальную транзакцию
            referrals_data = load_data("referral_transactions.json") if os.path.exists("referral_transactions.json") else {}
            transaction_id = f"TRX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            referrals_data[transaction_id] = {
                "referrer_id": referrer_id,
                "user_id": user_id,
                "amount": amount,
                "bonus": referral_bonus,
                "percent": REFERRAL_PERCENT,
                "timestamp": datetime.now().isoformat(),
                "order_id": None
            }
            save_data("referral_transactions.json", referrals_data)
            
            return referral_bonus
    
    return 0

async def send_referral_notification(referrer_id, new_user_id, bonus, amount):
    """Отправка уведомления о реферальном бонусе"""
    users = load_data(USERS_FILE)
    new_user_data = users.get(str(new_user_id), {})
    new_user_name = new_user_data.get("first_name", "Пользователь")
    
    message = (
        f"🎉 **Новый реферал совершил покупку!**\n\n"
        f"👤 Пользователь: {new_user_name}\n"
        f"💰 Сумма покупки: {amount} RUB\n"
        f"🎁 Ваш бонус: {bonus} RUB ({REFERRAL_PERCENT}%)\n\n"
        f"💳 Ваш баланс пополнен на {bonus} RUB!\n"
        f"📊 Текущий баланс: {users[str(referrer_id)].get('balance', 0)} RUB\n\n"
        f"🔗 Приглашайте больше друзей и зарабатывайте!"
    )
    
    try:
        await bot.send_message(referrer_id, message, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка при отправке уведомления рефереру: {e}")

# Вывод средств (ПЕРЕМЕЩЕНО ВПЕРЕД!)
@dp.callback_query(lambda c: c.data == "withdraw_funds")
async def withdraw_funds(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    balance = user_data.get("balance", 0)
    
    if balance < 100:
        text = (
            f"💰 **Вывод средств**\n\n"
            f"❌ Минимальная сумма для вывода: 100 RUB\n"
            f"💳 Ваш текущий баланс: {balance} RUB\n\n"
            f"💡 **Чтобы вывести средства:**\n"
            f"1. Пригласите друзей по реферальной ссылке\n"
            f"2. Когда они купят подписку, вы получите {REFERRAL_PERCENT}%\n"
            f"3. Когда баланс достигнет 100 RUB, свяжитесь с администратором\n\n"
            f"🎁 Приглашайте больше друзей, чтобы накопить нужную сумму!"
        )
    else:
        text = (
            f"💰 **Вывод средств**\n\n"
            f"✅ Доступно для вывода: {balance} RUB\n\n"
            f"📞 **Для вывода средств:**\n"
            f"1. Свяжитесь с администратором: @admin_username\n"
            f"2. Укажите сумму вывода (мин. 100 RUB)\n"
            f"3. Предоставьте реквизиты для перевода\n"
            f"4. Сообщите ваш ID: `{user_id}`\n\n"
            f"⚠️ **Внимание:** Вывод осуществляется вручную администратором в течение 24 часов."
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton(text="🎁 Реферальная система", callback_data="referral_system")],
        [InlineKeyboardButton(text="💬 Связаться с админом", url="https://t.me/admin_username")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback_query.answer()

# Команда /start с обработкой реферальных ссылок
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
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
            
            # Отправляем уведомление рефереру о новом реферале
            try:
                await bot.send_message(
                    referrer_id,
                    f"🎉 **У вас новый реферал!**\n\n"
                    f"👤 Пользователь: {message.from_user.first_name}\n"
                    f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"💰 Теперь вы будете получать {REFERRAL_PERCENT}% с его покупок!",
                    parse_mode="Markdown"
                )
            except:
                pass
            
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
        [InlineKeyboardButton(text="🎁 Реферальная система", callback_data="referral_system")]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard)

# Личный профиль пользователя
@dp.callback_query(lambda c: c.data == "my_profile")
async def my_profile(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    
    # Получаем информацию о активном ключе
    active_key_info = ""
    if user_data.get("active_key"):
        keys = load_data(KEYS_FILE)
        key_info = keys.get(user_data["active_key"], {})
        
        if key_info:
            if key_info.get("expires_at"):
                expires_date = datetime.fromisoformat(key_info["expires_at"])
                now = datetime.now()
                
                if expires_date > now:
                    days_left = (expires_date - now).days
                    hours_left = (expires_date - now).seconds // 3600
                    active_key_info = f"⏳ Осталось: {days_left} дн. {hours_left} ч.\n"
                    expires_text = f"📅 Истекает: {expires_date.strftime('%d.%m.%Y %H:%M')}"
                else:
                    active_key_info = "❌ Ключ истек\n"
                    expires_text = "📅 Истек"
            else:
                active_key_info = "✅ Ключ активен\n"
                expires_text = "📅 Истекает: НИКОГДА"
        else:
            active_key_info = "❌ Ключ не найден\n"
            expires_text = ""
    else:
        active_key_info = "❌ Нет активных ключей\n"
        expires_text = ""
    
    # Получаем информацию о реферере
    referrer_info = ""
    if user_data.get("referrer_id"):
        referrer_data = get_user_data(user_data["referrer_id"])
        referrer_name = referrer_data.get("first_name", "Пользователь")
        referrer_info = f"👤 Вас пригласил: {referrer_name}\n"
    
    # Формируем текст профиля
    profile_text = (
        f"👤 **Ваш профиль**\n\n"
        f"🆔 ID: {user_id}\n"
        f"👋 Имя: {user_data.get('first_name', 'Неизвестно')}\n"
        f"📅 Дата регистрации: {datetime.fromisoformat(user_data['join_date']).strftime('%d.%m.%Y %H:%M')}\n\n"
        f"{referrer_info}"
        f"💰 **Баланс:** {user_data.get('balance', 0)} RUB\n"
        f"💵 Всего заработано: {user_data.get('total_earned', 0)} RUB\n"
        f"💸 Всего потрачено: {user_data.get('total_spent', 0)} RUB\n"
        f"📦 Заказов: {user_data.get('orders_count', 0)}\n\n"
        f"🔑 **Активная подписка:**\n"
        f"{active_key_info}"
    )
    
    if user_data.get("active_key"):
        profile_text += f"🔐 Ключ: `{user_data['active_key']}`\n{expires_text}\n\n"
    
    if user_data.get("referrals"):
        referrals_count = len(user_data["referrals"])
        profile_text += f"👥 Рефералов: {referrals_count} чел.\n"
        
        # Подсчитываем доход от рефералов
        referrals_income = 0
        if os.path.exists("referral_transactions.json"):
            transactions = load_data("referral_transactions.json")
            for transaction in transactions.values():
                if transaction.get("referrer_id") == user_id:
                    referrals_income += transaction.get("bonus", 0)
        
        if referrals_income > 0:
            profile_text += f"💰 Заработано с рефералов: {referrals_income} RUB\n"
    else:
        profile_text += "👥 Рефералов: 0 чел.\n"
    
    # Кнопки профиля
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="my_profile")],
        [InlineKeyboardButton(text="🎁 Реферальная система", callback_data="referral_system")],
        [InlineKeyboardButton(text="🛒 Купить подписку", callback_data="choose_subscription")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu")]
    ])
    
    await callback_query.message.edit_text(profile_text, parse_mode="Markdown", reply_markup=keyboard)
    await callback_query.answer()

# Реферальная система
@dp.callback_query(lambda c: c.data == "referral_system")
async def referral_system(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    
    referral_link = get_referral_link(user_id)
    referrals_count = len(user_data.get("referrals", []))
    total_earned = user_data.get("total_earned", 0)
    balance = user_data.get("balance", 0)
    
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
        f"🎯 Минимальный вывод: 100 RUB\n\n"
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
        [InlineKeyboardButton(text="📊 Мои рефералы", callback_data="my_referrals")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    
    await callback_query.message.edit_text(referral_text, parse_mode="Markdown", reply_markup=keyboard)
    await callback_query.answer()

# Просмотр моих рефералов
@dp.callback_query(lambda c: c.data == "my_referrals")
async def my_referrals(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    
    referrals = user_data.get("referrals", [])
    
    if not referrals:
        text = (
            f"📊 **Мои рефералы**\n\n"
            f"👥 У вас пока нет рефералов.\n\n"
            f"💡 Пригласите друзей по своей реферальной ссылке и начните зарабатывать {REFERRAL_PERCENT}% с их покупок!"
        )
    else:
        text = f"📊 **Мои рефералы**\n\n"
        text += f"👥 Всего рефералов: {len(referrals)}\n\n"
        
        # Показываем первых 10 рефералов
        for i, ref_id in enumerate(referrals[:10], 1):
            ref_data = get_user_data(ref_id)
            ref_name = ref_data.get("first_name", "Пользователь")
            ref_orders = ref_data.get("orders_count", 0)
            ref_spent = ref_data.get("total_spent", 0)
            
            text += f"{i}. {ref_name}\n"
            text += f"   📦 Заказов: {ref_orders}\n"
            text += f"   💰 Потратил: {ref_spent} RUB\n\n"
        
        if len(referrals) > 10:
            text += f"📝 ... и еще {len(referrals) - 10} рефералов\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Реферальная система", callback_data="referral_system")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback_query.answer()

# Главное меню
@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu(callback_query: types.CallbackQuery):
    welcome_text = (
        f"👋 Добро пожаловать, {callback_query.from_user.first_name}!\n\n"
        f"👇 Выберите действие:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Выбрать подписку", callback_data="choose_subscription")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton(text="🎁 Реферальная система", callback_data="referral_system")]
    ])
    
    await callback_query.message.edit_text(welcome_text, reply_markup=keyboard)
    await callback_query.answer()

# Начало выбора подписки
@dp.callback_query(lambda c: c.data == "choose_subscription")
async def start_subscription_choice(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    device_text = "📱 **На какое устройство нужен DLC?**"
    
    device_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Android устройство (APK)", callback_data="select_device_apk")],
        [InlineKeyboardButton(text="💻 Эмулятор/ПК", callback_data="select_device_emulator")]
    ])
    
    await callback_query.message.edit_text(device_text, parse_mode="Markdown", reply_markup=device_keyboard)
    await callback_query.answer()

# Выбор устройства (APK)
@dp.callback_query(lambda c: c.data == "select_device_apk")
async def process_device_apk(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(
        device_type="apk",
        device_name=DEVICES["apk"]["name"]
    )
    await state.set_state(PurchaseStates.waiting_for_period)
    
    period_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{period_info['name']} - {period_info['price']} RUB", 
            callback_data=f"select_period_{period_id}"
        )]
        for period_id, period_info in SUBSCRIPTION_PERIODS.items()
    ])
    
    await callback_query.message.edit_text(
        DEVICES["apk"]["description"],
        reply_markup=period_keyboard
    )
    await callback_query.answer()

# Выбор устройства (Emulator)
@dp.callback_query(lambda c: c.data == "select_device_emulator")
async def process_device_emulator(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(
        device_type="emulator",
        device_name=DEVICES["emulator"]["name"]
    )
    await state.set_state(PurchaseStates.waiting_for_period)
    
    period_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{period_info['name']} - {period_info['price']} RUB", 
            callback_data=f"select_period_{period_id}"
        )]
        for period_id, period_info in SUBSCRIPTION_PERIODS.items()
    ])
    
    await callback_query.message.edit_text(
        DEVICES["emulator"]["description"],
        reply_markup=period_keyboard
    )
    await callback_query.answer()

# Выбор срока подписки
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
        [InlineKeyboardButton(text="💳 Тинькофф", callback_data="select_payment_tinkoff")],
        [InlineKeyboardButton(text="🏦 СБП Сбербанк", callback_data="select_payment_sber_sbp")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="choose_subscription")]
    ])
    
    await callback_query.message.edit_text(summary_text, parse_mode="Markdown", reply_markup=payment_keyboard)
    await callback_query.answer()

# Выбор метода оплаты
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
            f"✅ **После проверки чека мы отправим вам товар в течение 15 минут!**\n\n"
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
            f"✅ **После проверки чека мы отправим вам товар в течение 15 минут!**\n\n"
            f"⚠️ **ВНИМАНИЕ:** Обязательно отправьте чек для подтверждения оплаты!"
        )
    
    await callback_query.message.edit_text(payment_text, parse_mode="Markdown")
    await callback_query.answer()

# Обработка чека
@dp.message(PurchaseStates.waiting_for_receipt)
async def process_receipt(message: types.Message, state: FSMContext):
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
        
        order_id = generate_order_id()
        payment_details = PAYMENT_DETAILS.get(payment_method, {})
        payment_name = payment_details.get("name", "Неизвестный метод")
        
        order_info = {
            "user_id": user_id,
            "username": message.from_user.username,
            "full_name": f"{message.from_user.first_name} {message.from_user.last_name or ''}",
            "device_name": device_name,
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
            f"✅ **Товар будет отправлен вам в течение 15 минут после подтверждения платежа!**"
        )
        
        await message.answer(confirmation_text, parse_mode="Markdown")
        await send_full_order_to_admin(order_id, order_info)
        await state.clear()
        
    except Exception as e:
        print(f"Ошибка при обработке заказа: {e}")
        await message.answer("❌ Произошла ошибка при обработке заказа. Попробуйте еще раз.")

async def send_full_order_to_admin(order_id: str, order_info: dict):
    try:
        admin_text = (
            f"🆔 **НОВЫЙ ЗАКАЗ: {order_id}**\n\n"
            f"👤 **Пользователь:**\n"
            f"ID: {order_info['user_id']}\n"
            f"Username: @{order_info['username'] or 'нет'}\n"
            f"Имя: {order_info['full_name']}\n\n"
            f"📋 **Детали заказа:**\n"
            f"📱 Устройство: {order_info['device_name']}\n"
            f"⏳ Срок: {order_info['period_name']}\n"
            f"💰 Сумма: {order_info['period_price']} RUB\n"
            f"💳 Метод оплаты: {order_info['payment_method_name']}\n"
            f"📅 Создан: {datetime.fromisoformat(order_info['timestamp']).strftime('%d.%m.%Y %H:%M:%S')}"
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
        
    except Exception as e:
        print(f"Ошибка при отправке заказа админу: {e}")

# ИСПРАВЛЕННЫЙ ОБРАБОТЧИК ДЕЙСТВИЙ АДМИНИСТРАТОРА - ВСЁ В ОДНОМ СООБЩЕНИИ
@dp.callback_query(lambda c: c.data.startswith("approve_") or c.data.startswith("reject_"))
async def process_admin_action(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
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
    user_id = order_info["user_id"]
    payment_name = order_info.get("payment_method_name", "Неизвестный метод")
    period_price = order_info.get("period_price", 0)
    
    if action == "approve":
        # Генерируем ключ
        period_days = order_info.get("period_days", 7)
        if period_days == "навсегда":
            period_days_for_key = 9999
        else:
            period_days_for_key = period_days
        
        key = generate_key(order_id, period_days_for_key)
        
        # Обновляем заказ
        orders[order_id]["status"] = "approved"
        orders[order_id]["approved_at"] = datetime.now().isoformat()
        orders[order_id]["key"] = key
        save_data(ORDERS_FILE, orders)
        
        # Обновляем данные пользователя
        user_data = get_user_data(user_id)
        user_data["active_key"] = key
        user_data["key_expires"] = None if period_days == "навсегда" else (
            datetime.now() + timedelta(days=period_days_for_key)
        ).isoformat()
        update_user_data(user_id, user_data)
        
        # Обрабатываем реферальную систему
        referral_bonus = process_referral_system(user_id, period_price)
        
        # Формируем срок действия
        if period_days == "навсегда":
            validity_text = "✅ **Срок действия: НАВСЕГДА**"
        else:
            validity_text = f"📅 **Срок действия: {period_days} дней**"
        
        # ФОРМИРУЕМ ЕДИНОЕ СООБЩЕНИЕ С ВСЕЙ ИНФОРМАЦИЕЙ
        user_message = (
            f"✅ **✅ ОПЛАТА УСПЕШНО ПОЛУЧЕНА! ✅**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 **ИНФОРМАЦИЯ О ЗАКАЗЕ:**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **Номер заказа:** {order_id}\n"
            f"📱 **Устройство:** {order_info['device_name']}\n"
            f"⏳ **Срок подписки:** {order_info['period_name']}\n"
            f"💰 **Сумма:** {period_price} RUB\n"
            f"💳 **Метод оплаты:** {payment_name}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 **ВАШ КЛЮЧ АКТИВАЦИИ:**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"```\n{key}\n```\n\n"
            f"{validity_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📱 **ССЫЛКА НА ПРИВАТНУЮ ГРУППУ:**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{PRIVATE_GROUP_LINK}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 **ИНСТРУКЦИЯ ПО АКТИВАЦИИ:**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"1. 📲 Перейдите по ссылке выше\n"
            f"2. 🔑 Вступите в приватную группу\n"
            f"3. 📝 Отправьте ключ администратору группы\n"
            f"4. 🎮 Получите доступ к NeworkPC!\n\n"
            f"✅ **Поддерживаемые способы входа:**\n"
            f"• Google аккаунт\n"
            f"• VK\n"
            f"• Facebook\n"
            f"• Любой удобный способ!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📞 **ТЕХНИЧЕСКАЯ ПОДДЕРЖКА:**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Если возникли проблемы с активацией:\n"
            f"1. Сохраните этот ключ!\n"
            f"2. Обратитесь к администратору группы\n"
            f"3. Сообщите номер заказа: {order_id}\n\n"
            f"🎉 **Спасибо за покупку! Приятной игры!** 🎮\n\n"
            f"💡 **Ключ также сохранен в вашем профиле!**\n"
            f"Чтобы посмотреть ключ, перейдите в '👤 Мой профиль'"
        )
        
        # Кнопки для пользователя
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Перейти в приватную группу", url=PRIVATE_GROUP_LINK)],
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
            [InlineKeyboardButton(text="🛒 Сделать новый заказ", callback_data="choose_subscription")]
        ])
        
        try:
            # Отправляем одно сообщение со всей информацией
            await bot.send_message(user_id, user_message, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю: {e}")
            # Если не удалось отправить длинное сообщение, пробуем разбить
            try:
                # Первая часть
                await bot.send_message(
                    user_id,
                    f"✅ **✅ ОПЛАТА УСПЕШНО ПОЛУЧЕНА! ✅**\n\n"
                    f"🆔 **Номер заказа:** {order_id}\n"
                    f"📱 **Устройство:** {order_info['device_name']}\n"
                    f"⏳ **Срок:** {order_info['period_name']}\n"
                    f"💰 **Сумма:** {period_price} RUB\n\n"
                    f"🔑 **ВАШ КЛЮЧ:**\n"
                    f"```\n{key}\n```\n\n"
                    f"{validity_text}",
                    parse_mode="Markdown"
                )
                
                # Вторая часть
                await bot.send_message(
                    user_id,
                    f"🔗 **Приватная группа:**\n"
                    f"{PRIVATE_GROUP_LINK}\n\n"
                    f"✅ **Способы входа:** Google, VK, Facebook\n\n"
                    f"📋 **Инструкция:**\n"
                    f"1. Перейдите по ссылке\n"
                    f"2. Отправьте ключ админу группы\n"
                    f"3. Получите доступ!\n\n"
                    f"🎮 **Приятной игры!**",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            except:
                pass
        
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
            await callback_query.message.answer(
                f"✅ Заказ {order_id} принят!\n"
                f"Ключ: {key}",
                parse_mode="Markdown"
            )
        
        await callback_query.answer(f"Заказ {order_id} принят! Ключ отправлен.")
        
    else:  # reject
        orders[order_id]["status"] = "rejected"
        orders[order_id]["rejected_at"] = datetime.now().isoformat()
        save_data(ORDERS_FILE, orders)
        
        user_message = (
            f"❌ **Заказ отклонен**\n\n"
            f"🆔 **Номер заказа:** {order_id}\n"
            f"💳 **Метод оплаты:** {payment_name}\n\n"
            f"⚠️ **Ваш платеж не подтвержден администратором.**\n\n"
            f"💬 **Для уточнения деталей свяжитесь с поддержкой.**"
        )
        
        try:
            await bot.send_message(user_id, user_message, parse_mode="Markdown")
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

# Команды администратора
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    admin_text = (
        f"🛠️ **Панель администратора**\n\n"
        f"📊 **Статистика:**\n"
        f"👥 Пользователей: {len(load_data(USERS_FILE))}\n"
        f"📦 Заказов: {len(load_data(ORDERS_FILE))}\n"
        f"🔑 Ключей: {len(load_data(KEYS_FILE))}\n\n"
        f"📋 **Доступные команды:**\n"
        f"/orders - Все заказы\n"
        f"/users - Все пользователи\n"
        f"/stats - Статистика\n"
        f"/check_key <ключ> - Проверить ключ\n"
        f"/add_balance <id> <сумма> - Добавить баланс\n"
    )
    
    await message.answer(admin_text, parse_mode="Markdown")

@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    users = load_data(USERS_FILE)
    
    if not users:
        await message.answer("👥 Пользователей нет")
        return
    
    users_text = "👥 **Все пользователи:**\n\n"
    
    for user_id, user_data in list(users.items())[:20]:
        users_text += (
            f"🆔 ID: {user_id}\n"
            f"👤 @{user_data.get('username', 'нет')}\n"
            f"💰 Баланс: {user_data.get('balance', 0)} RUB\n"
            f"👥 Рефералов: {len(user_data.get('referrals', []))}\n"
            f"📅 Регистрация: {datetime.fromisoformat(user_data['join_date']).strftime('%d.%m.%Y')}\n\n"
        )
    
    await message.answer(users_text[:4000], parse_mode="Markdown")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    users = load_data(USERS_FILE)
    orders = load_data(ORDERS_FILE)
    keys = load_data(KEYS_FILE)
    
    total_balance = sum(user.get("balance", 0) for user in users.values())
    total_spent = sum(user.get("total_spent", 0) for user in users.values())
    total_earned = sum(user.get("total_earned", 0) for user in users.values())
    
    approved_orders = sum(1 for order in orders.values() if order.get("status") == "approved")
    pending_orders = sum(1 for order in orders.values() if order.get("status") == "pending")
    
    stats_text = (
        f"📊 **Статистика системы**\n\n"
        f"👥 **Пользователи:**\n"
        f"Всего пользователей: {len(users)}\n"
        f"Общий баланс: {total_balance} RUB\n"
        f"Всего заработано: {total_earned} RUB\n"
        f"Всего потрачено: {total_spent} RUB\n\n"
        f"📦 **Заказы:**\n"
        f"Всего заказов: {len(orders)}\n"
        f"Подтверждено: {approved_orders}\n"
        f"Ожидают: {pending_orders}\n\n"
        f"🔑 **Ключи:**\n"
        f"Всего ключей: {len(keys)}\n"
        f"Активных: {sum(1 for key in keys.values() if not key.get('is_used', False))}"
    )
    
    await message.answer(stats_text, parse_mode="Markdown")

@dp.message(Command("check_key"))
async def cmd_check_key(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /check_key <ключ>")
        return
    
    key = args[1]
    keys = load_data(KEYS_FILE)
    
    if key in keys:
        key_info = keys[key]
        order_id = key_info["order_id"]
        orders = load_data(ORDERS_FILE)
        order_info = orders.get(order_id, {})
        
        status = "✅ АКТИВЕН" if not key_info["is_used"] else "❌ ИСПОЛЬЗОВАН"
        
        if key_info["expires_at"]:
            expires_date = datetime.fromisoformat(key_info["expires_at"]).strftime('%d.%m.%Y %H:%M')
            expires_text = f"📅 Истекает: {expires_date}"
        else:
            expires_text = "📅 Истекает: НИКОГДА (вечный ключ)"
        
        response = (
            f"🔑 **Информация о ключе:**\n\n"
            f"Ключ: `{key}`\n"
            f"Статус: {status}\n"
            f"Заказ: {order_id}\n"
            f"Создан: {datetime.fromisoformat(key_info['created_at']).strftime('%d.%m.%Y %H:%M')}\n"
            f"{expires_text}\n"
            f"Срок: {key_info['period_days']} дней\n\n"
            f"👤 **Информация о пользователе:**\n"
            f"ID: {order_info.get('user_id', 'Неизвестно')}\n"
            f"Username: @{order_info.get('username', 'нет')}\n"
            f"Устройство: {order_info.get('device_name', 'Неизвестно')}"
        )
    else:
        response = "❌ Ключ не найден!"
    
    await message.answer(response, parse_mode="Markdown")

@dp.message(Command("add_balance"))
async def cmd_add_balance(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Использование: /add_balance <id> <сумма>")
        return
    
    try:
        user_id = int(args[1])
        amount = int(args[2])
        
        users = load_data(USERS_FILE)
        if str(user_id) not in users:
            await message.answer(f"❌ Пользователь с ID {user_id} не найден!")
            return
        
        users[str(user_id)]["balance"] = users[str(user_id)].get("balance", 0) + amount
        save_data(USERS_FILE, users)
        
        await message.answer(f"✅ Баланс пользователя {user_id} пополнен на {amount} RUB")
        
        try:
            await bot.send_message(
                user_id,
                f"💰 **Ваш баланс пополнен!**\n\n"
                f"💳 На ваш счет зачислено: {amount} RUB\n"
                f"📊 Текущий баланс: {users[str(user_id)]['balance']} RUB\n\n"
                f"🎁 Вы можете вывести средства через раздел реферальной системы!",
                parse_mode="Markdown"
            )
        except:
            pass
            
    except ValueError:
        await message.answer("❌ Неверный формат ID или суммы!")

@dp.message(Command("orders"))
async def cmd_orders(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    orders = load_data(ORDERS_FILE)
    
    if not orders:
        await message.answer("📭 Заказов нет")
        return
    
    orders_text = "📋 **Все заказы:**\n\n"
    
    for order_id, order_info in list(orders.items())[:15]:
        status_emoji = "⏳" if order_info["status"] == "pending" else "✅" if order_info["status"] == "approved" else "❌"
        key_info = f"🔑 {order_info.get('key', 'Нет ключа')}" if order_info.get('key') else "🔑 Нет ключа"
        
        orders_text += (
            f"{status_emoji} **{order_id}**\n"
            f"👤 @{order_info['username'] or 'нет'}\n"
            f"📱 {order_info['device_name']}\n"
            f"💰 {order_info['period_price']} RUB\n"
            f"💳 {order_info.get('payment_method_name', 'Неизвестно')}\n"
            f"{key_info}\n"
            f"📅 {datetime.fromisoformat(order_info['timestamp']).strftime('%d.%m.%Y %H:%M')}\n"
            f"🔸 Статус: {order_info['status']}\n\n"
        )
    
    await message.answer(orders_text[:4000], parse_mode="Markdown")

# ВАЖНО: Добавьте эту функцию для создания файла транзакций при первом запуске
def init_files():
    """Инициализация файлов данных при первом запуске"""
    files_to_init = [
        ORDERS_FILE, KEYS_FILE, USERS_FILE, 
        "referral_transactions.json"
    ]
    
    for file in files_to_init:
        if not os.path.exists(file):
            save_data(file, {})
            print(f"Создан файл: {file}")

# Основная функция
async def main():
    # Инициализируем файлы
    init_files()
    
    print("=" * 60)
    print("🤖 БОТ NeworkPC Private Key Shop")
    print("=" * 60)
    print(f"👑 Администратор: {ADMIN_ID}")
    print(f"🔗 Приватная группа: {PRIVATE_GROUP_LINK}")
    print(f"💰 Реферальная комиссия: {REFERRAL_PERCENT}%")
    print(f"🤝 Реферальные ссылки: https://t.me/{BOT_USERNAME}?start=ref_КОД")
    print("=" * 60)
    print("✅ Функции бота:")
    print("   • Личный кабинет с ключами")
    print("   • Реферальная система 15%")
    print("   • История заказов")
    print("   • Автоматическое начисление бонусов")
    print("   • Вывод средств от 100 RUB")
    print("=" * 60)
    print("📱 Поддерживаемые способы входа: Google, VK, Facebook")
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
