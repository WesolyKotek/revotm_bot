from aiogram import types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from dispatcher import dp
import config
import random
from revotm_bot import BotDB
import cv2
import xlsxwriter
import datetime
from shutil import make_archive
from zipfile import ZipFile

import hashlib  # MD5 hash


class UserState(StatesGroup):
    login = State()
    password = State()
    menu = State()
    isloggedin = State()
    chg_pass = State()
    reports_act = State()
    bonuses_edit = State()
    bonuses_edit_act = State()
    bonuses_edit_act_use = State()
    bonuses_edit_act_use_summ = State()
    bonuses_edit_act_use_pay = State()
    cafe_edit = State()
    cafe_edit_act = State()
    cafe_edit_act_add = State()
    cafe_edit_act_add_name = State()
    cafe_edit_act_add_sd = State()
    cafe_edit_act_add_desc = State()
    cafe_edit_act_rename = State()
    findby_fio = State()
    findby_dep = State()
    addemp_fio = State()
    addemp_login = State()
    addemp_dep = State()
    emp_edit = State()
    emp_edit_act = State()
    emp_edit_act_bonuse = State()
    emp_edit_act_bonuse_add = State()
    emp_edit_act_bonuse_del = State()
    emp_edit_act_fio = State()
    emp_edit_act_login = State()
    emp_edit_act_pass = State()


@dp.message_handler(commands='start')
async def start(message: types.Message, state: FSMContext):

    if not BotDB.user_exists(message.from_user.id):

        btn = KeyboardButton('Авторизация')
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(btn)

        await message.bot.send_message(
            message.chat.id,
            'Ваш аккаунт не найден в системе, пожалуйста, авторизуйтесь.', reply_markup=kb)
    else:
        BotDB.update_last_login(message.from_user.id)
        await login(message, state)


@dp.message_handler(text='Авторизация')
async def message_handler_login(message: types.Message, state: FSMContext):
    try:
        if (await state.get_data())['isloggedin'] is True:
            return
    except:
        pass
    finally:
        await message.bot.send_message(
            message.chat.id,
            'Введите логин:')
        await UserState.login.set()


@dp.message_handler(state=UserState.login)
async def check_login(message: types.Message, state: FSMContext):
    if not BotDB.user_exists_bylogin(message.text):
        await message.bot.send_message(
            message.chat.id,
            'Неверно указан логин.')
        await message_handler_login(message, state)
    else:
        await state.update_data(login=message.text)
        await message.bot.send_message(
            message.chat.id,
            'Введите пароль:')
        await UserState.password.set()


@dp.message_handler(state=UserState.password)
async def check_password(message: types.Message, state: FSMContext):
    userlogin = (await state.get_data())['login']
    password = hashlib.md5(f'{message.text}'.encode('utf-8')).hexdigest().upper()
    if not (BotDB.get_password(userlogin) == password):
        await message.bot.send_message(
            message.chat.id,
            f'Неверно указан пароль.')

        BotDB.write_log('user', message.from_user.id, userlogin, f"Неудачная попытка войти в аккаунт "
                                                                 f"'{userlogin}' (user_id:{message.from_user.id}).")

        await message.bot.send_message(
            message.chat.id,
            'Введите пароль:')
        await UserState.password.set()
    else:
        BotDB.update_user_id(message.from_user.id, userlogin)
        BotDB.update_last_login(message.from_user.id)
        await write_log(message, 'user', f"вошёл в аккаунт.")
        await reset_state(state, message)
        await state.update_data(isloggedin=True)
        message.text = '/start'
        await login(message, state)


async def login(message: types.Message, state: FSMContext):
    userdata = BotDB.get_userdata(message.from_user.id)
    role = config.roles.get(userdata[5])
    await state.update_data(isloggedin=True)
    await state.update_data(role=userdata[5])
    await state.update_data(login1=userdata[2])
    # личный кабинет
    btn = KeyboardButton('Личный кабинет')
    btn_hr = KeyboardButton('Панель управления HR')
    btn_quit = KeyboardButton('Выйти из аккаунта')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(btn)

    if role == 'HR':
        kb.add(btn_hr)

    kb.add(btn_quit)
    if message.text == '/start':
        await message.bot.send_message(
            message.chat.id,
            f'Добро пожаловать, {userdata[4]}! Вы авторизованы как {role}!', reply_markup=kb)
    else:
        await message.bot.send_message(
            message.chat.id,
            f'{userdata[4]}, Вы авторизованы как {role}!', reply_markup=kb)


async def write_log(message: types.Message, type, action):
    try:
        userdata = BotDB.get_userdata(message.from_user.id)
        BotDB.write_log(type, userdata[1], userdata[2], f'{userdata[4]} {action}')
    except:
        print(f'Unable to write log!')
        return


async def write_bonuse_log(message: types.Message, type, action, bonuse, file_id):
    try:
        userdata = BotDB.get_userdata(message.from_user.id)
        BotDB.write_bonuse_log(type, userdata[1], userdata[2], f"{userdata[4]} ('{config.departs.get(userdata[6])}')"
                                                               f" {action}", bonuse, file_id)
    except:
        print(f'Unable to write log!')
        return


async def isloggedin(message: types.Message, state: FSMContext):
    try:
        islogged = (await state.get_data())['isloggedin']
        if islogged is False:
            return False
        else:
            if BotDB.get_user_id((await state.get_data())['login1']) != message.from_user.id:
                await state.update_data(isloggedin=False)
                return False
            else:
                return True
    except:
        return False


async def getstate(message, state: FSMContext):
    if not await isloggedin(message, state):
        await start(message, state)
        return
    return (await state.get_data())['menu']


async def setstate(new_state, state: FSMContext, message):
    if not await isloggedin(message, state):
        await start(message, state)
        return False
    else:
        await state.update_data(menu=new_state)
        return True


async def reset_state(state: FSMContext, message):
    if not await isloggedin(message, state):
        await state.reset_state()
    else:
        menu_state = (await state.get_data())['menu']
        role = (await state.get_data())['role']
        login = (await state.get_data())['login1']
        await state.reset_state()
        await state.update_data(menu=menu_state)
        await state.update_data(isloggedin=True)
        await state.update_data(role=role)
        await state.update_data(login1=login)


@dp.message_handler(text='Назад')
async def message_handler_back(message: types.Message, state: FSMContext):

    match (await getstate(message, state)):
        case 'Список льгот':
            message.text = 'Личный кабинет'
            await message_handler_office(message, state)
        case 'Изменить пароль':
            message.text = 'Личный кабинет'
            await message_handler_office(message, state)
        case 'Сотрудники':
            message.text = 'Панель управления HR'
            await message_handler_hr_office(message, state)
        case 'Кафетерий льгот':
            message.text = 'Панель управления HR'
            await message_handler_hr_office(message, state)
        case 'Личный кабинет':
            await login(message, state)
        case 'Панель управления HR':
            await login(message, state)
        case 'bonuses_edit_act_use':
            message.text = (await state.get_data())['bonuses_edit'][1]
            await bonuses_edit(message, state)
        case _:
            message.text = 'Личный кабинет'


@dp.message_handler(text='Личный кабинет')
async def message_handler_office(message: types.Message, state: FSMContext):
    if not await setstate(message.text, state, message):
        return

    userdata = BotDB.get_userdata(message.from_user.id)
    role = config.roles.get(userdata[5])
    dep = config.departs.get(userdata[6])

    # получаем список бонусов
    bonuses_names = {}
    for bonuse in BotDB.get_bonuses_names():
        bonuses_names.update({bonuse[1]: bonuse[2]})

    # получаем список желаний пользователя
    user_bonuses = (userdata[9])[2:len(userdata[9])-2].split('", "')
    user_bonuses1 = []
    if not(user_bonuses == ['']):
        for bonuse in user_bonuses:
            if bonuses_names.get(bonuse) is not None:
                user_bonuses1.append(bonuses_names.get(bonuse))
        if not (user_bonuses1 == ['']):
            text_wishlist = "\n-" + "\n-".join(user_bonuses1)
        else:
            text_wishlist = "Нет"
    else:
        text_wishlist = "Нет"

    # кнопки
    btn_bonuses = KeyboardButton('Список льгот')
    btn_chgpass = KeyboardButton('Изменить пароль')
    btn_quit = KeyboardButton('Выйти из аккаунта')
    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_bonuses).add(btn_chgpass).add(btn_quit).add(btn_back)

    year = ''
    last_year = int(str(userdata[7])[-1])
    if last_year == 1:
        year = 'год'
    elif last_year > 1 and last_year < 5:
        year = 'года'
    elif last_year == 0 or last_year < 9:
        year = 'лет'



    await message.bot.send_message(
        message.chat.id,
        f'Личный кабинет\n'
        f'<i><b>{userdata[4]}</b></i> - {role}, {dep}, стаж {userdata[7]} {year}'
        f'\n<i><b>Баланс:</b></i> {userdata[8]}'
        f'\n<i><b>Ваш список желаний:</b></i> {text_wishlist}', reply_markup=kb)


@dp.message_handler(text='Изменить пароль')
async def message_handler_chg_pass(message: types.Message, state: FSMContext):
    if not await setstate(message.text, state, message):
        return

    # кнопки
    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'Введите новый пароль: ', reply_markup=kb)
    await UserState.chg_pass.set()


@dp.message_handler(state=UserState.chg_pass)
async def message_handler_chg_pass_en(message: types.Message, state: FSMContext):
    if not await setstate('chg_pass', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Личный кабинет'
        await reset_state(state, message)
        await message_handler_office(message, state)
        return

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    kb.add(btn_back)

    loginn = BotDB.get_userdata(message.from_user.id)[2]
    password = message.text
    if any(char not in config.password_chars for char in set(password)):
        await message.bot.send_message(
            message.chat.id,
            f'Ошибка. Введены недопустимые символы!')
        await reset_state(state, message)
        await message_handler_chg_pass(message, state)
    else:
        try:
            password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest().upper()
            BotDB.set_password(password_md5, loginn)
            await write_log(message, 'user', f"изменил пароль.")
            await message.bot.send_message(
                message.chat.id,
                f'Новый пароль - {password}')
        except:
            await message.bot.send_message(
                message.chat.id,
                f'Что-то пошло не так...')
        finally:
            message.text = 'Личный кабинет'
            await reset_state(state, message)
            await message_handler_office(message, state)


@dp.message_handler(text='Панель управления HR')
async def message_handler_hr_office(message: types.Message, state: FSMContext):
    if not await setstate(message.text, state, message):
        return

    if (await state.get_data())['role'] != 'hr':
        await message.bot.send_message(
            message.chat.id,
            f'Доступ запрещён!')
        await message_handler_office(message, state)
        return

    # кнопки
    btn_employees = KeyboardButton('Сотрудники')
    btn_cafe = KeyboardButton('Кафетерий льгот')
    btn_reports = KeyboardButton('Выгрузка отчётов')
    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_employees).add(btn_cafe).add(btn_reports).add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'Панель управления HR', reply_markup=kb)


@dp.message_handler(text='Список льгот')
async def message_handler_bonuses(message: types.Message, state: FSMContext):
    if not await setstate(message.text, state, message):
        return

    userdata = BotDB.get_userdata(message.from_user.id)

    # получаем список бонусов
    bonuses_names = {}
    for bonuse in BotDB.get_bonuses_names():
        bonuses_names.update({bonuse[1]: bonuse[2]})

    # получаем список желаний пользователя
    user_bonuses = (userdata[9])[2:len(userdata[9])-2].split('", "')
    user_bonuses1 = []
    if not(user_bonuses == ['']):
        for bonuse in user_bonuses:
            if bonuses_names.get(bonuse) is not None:
                user_bonuses1.append(bonuses_names.get(bonuse))
        if not (user_bonuses1 == ['']):
            text_wishlist = "\n-" + "\n-".join(user_bonuses1)
        else:
            text_wishlist = "Нет"
    else:
        text_wishlist = "Нет"

    # кнопки
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    wishlist = []
    bonuses = []
    for bonuse in bonuses_names.values():
        try:
            user_bonuses1.index(bonuse)
            wishlist.append(bonuse)
        except:
            bonuses.append(bonuse)
    for bonuse in wishlist:
        kb.add(KeyboardButton(f'{bonuse} ❤'))
    for bonuse in bonuses:
        kb.add(KeyboardButton(f'{bonuse}'))
    btn_back = KeyboardButton('Назад')
    kb.add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'\n<i><b>Ваш список желаний:</b></i> {text_wishlist}\n', reply_markup=kb)
    await UserState.bonuses_edit.set()


@dp.message_handler(state=UserState.bonuses_edit)
async def bonuses_edit(message: types.Message, state: FSMContext):
    if not await setstate('bonuses_edit', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Личный кабинет'
        await reset_state(state, message)
        await message_handler_office(message, state)
        return

    # получаем список бонусов
    bonuses_info = {}
    for bonuse in BotDB.get_bonuses_names():
        bonuses_info.update({bonuse[1]: [bonuse[2], bonuse[3]]})

    in_fav = False
    if message.text[len(message.text)-1] == '❤':
        message.text = message.text[:len(message.text)-2]
        in_fav = True
    bonuse = [[data, nd[0], nd[1]] for data, nd in bonuses_info.items() if message.text in nd[0]]
    if len(bonuse) != 1:
        bonuse = [[data, nd[0], nd[1]] for data, nd in bonuses_info.items() if message.text == nd[0]]
        if len(bonuse) != 1:
            await message.bot.send_message(
                message.chat.id,
                f'Такой льготы не существует.')
            await reset_state(state, message)
            message.text = 'Личный кабинет'
            await message_handler_bonuses(message, state)
            return
    bonuse = bonuse[0]

    await state.update_data(bonuses_edit=bonuse)

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_bonuses_edit_act_add = KeyboardButton('Добавить в избранное')
    btn_bonuses_edit_act_del = KeyboardButton('Удалить из избранного')
    btn_bonuses_edit_act_use = KeyboardButton('Применить льготу')

    if in_fav:
        kb.add(btn_bonuses_edit_act_del)
    else:
        kb.add(btn_bonuses_edit_act_add)
    kb.add(btn_bonuses_edit_act_use).add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'<i><b>{bonuse[1]}</b></i>\n'
        f'<i><b>Описание:</b></i> {bonuse[2]}\n'
        f'Выберите действие:', reply_markup=kb)
    await UserState.bonuses_edit_act.set()


@dp.message_handler(state=UserState.bonuses_edit_act)
async def bonuses_edit_act(message: types.Message, state: FSMContext):
    if not await setstate('bonuses_edit_act', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Список льгот'
        await reset_state(state, message)
        await message_handler_bonuses(message, state)
        return

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    bonuse = (await state.get_data())['bonuses_edit']

    # получаем список желаний пользователя
    userdata = BotDB.get_userdata(message.from_user.id)
    user_bonuses = (userdata[9])[2:len(userdata[9])-2].split('", "')
    if not(user_bonuses == ['']):
        user_bonuses = list(user_bonuses)
    else:
        user_bonuses = []

    match message.text:
        case 'Добавить в избранное':
            user_bonuses.append(bonuse[0])
            bonuses = '", "'.join(user_bonuses)
            bonuses = f'["{bonuses}"]'
            BotDB.set_wishlist(message.from_user.id, bonuses)
            await write_bonuse_log(message, 'bonuses_add', f"добавил в избранное льготу '{bonuse[1]}'", bonuse[0], None)
            await message.bot.send_message(
                message.chat.id,
                f'Льгота <i><b>{bonuse[1]}</b></i> добавлена в избранное.')
            await reset_state(state, message)
            await message_handler_bonuses(message, state)
            return
        case 'Удалить из избранного':
            user_bonuses.remove(bonuse[0])
            bonuses = '", "'.join(user_bonuses)
            bonuses = f'["{bonuses}"]'
            BotDB.set_wishlist(message.from_user.id, bonuses)
            await write_bonuse_log(message, 'bonuses_del', f"удалил из избранного льготу '{bonuse[1]}'", bonuse[0], None)
            await message.bot.send_message(
                message.chat.id,
                f'Льгота <i><b>{bonuse[1]}</b></i> удалена из избранного.')
            await reset_state(state, message)
            await message_handler_bonuses(message, state)
            return
        case 'Применить льготу':
            if userdata[8] < 1:
                await write_bonuse_log(message, 'bonuses', f"попытался применить льготу '{bonuse[1]}'"
                                                    f" (balance: {userdata[8]}).", bonuse[0], None)
                await message.bot.send_message(
                    message.chat.id,
                    f'У вас недостаточно бонусов!')
                await reset_state(state, message)
                await message_handler_bonuses(message, state)
                return
            kb.add(btn_back)
            await message.bot.send_message(
                message.chat.id,
                f'Прикрепите чек:', reply_markup=kb)
            await reset_state(state, message)
            await state.update_data(bonuses_edit=bonuse)
            await setstate('bonuses_edit_act_use', state, message)
            return
        case _:
            message.text = bonuse[1]
            await bonuses_edit(message, state)


@dp.message_handler(content_types=['document', 'photo'])
async def bonuses_edit_act_use(message: types.Message, state: FSMContext):
    if (await getstate(message, state)) != 'bonuses_edit_act_use':
        return

    userdata = BotDB.get_userdata(message.from_user.id)
    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        await state.update_data(bonuses_edit_act_use_message=message)
    elif message.content_type == 'document':
        file_id = message.document.file_id
        await state.update_data(bonuses_edit_act_use_message=message)
    file_info = await dp.bot.get_file(file_id)
    file_format = file_info.file_path[(file_info.file_path.index(".")):]
    if file_format not in config.file_formats:
        await message.bot.send_message(
            message.chat.id,
            f'Неверный формат файла!')
        message.text = 'Применить льготу'
        await bonuses_edit_act(message, state)
        return

    file_name = f'{file_info.file_unique_id}{file_info.file_path[(file_info.file_path.index(".")):]}'
    download_path = f'{config.file_path}{file_name}'
    await dp.bot.download_file(file_info.file_path, download_path)
    await state.update_data(bonuses_edit_act_use_check=file_name)
    # считывание qr кода
    img = cv2.imread(download_path)
    detector = cv2.QRCodeDetector()
    # обнаружить и декодировать
    data = detector.detectAndDecode(img)[0]
    data = data.split('&')
    if len(data) > 1:
        summ = int(data[1][2:][:-3])
        bonuse_pay = userdata[8]
        if bonuse_pay > summ:
            bonuse_pay = summ
        await state.update_data(bonuses_edit_act_use_summ=summ)
        await state.update_data(bonuses_edit_act_use_pay=bonuse_pay)
        btn_payall = KeyboardButton(f'Списать максимум бонусов ({bonuse_pay})')
        kb.add(btn_payall).add(btn_back)
        await message.bot.send_message(
            message.chat.id,
            f'<i><b>Сумма:</b></i> {data[1][2:]}\n'
            f'<i><b>Доступно:</b></i> {userdata[8]} бонусов\n'
            f'Введите количество бонусов для списания:',
            reply_markup=kb)
        await UserState.bonuses_edit_act_use_pay.set()
    else:
        kb.add(btn_back)
        await message.bot.send_message(
            message.chat.id,
            f'Не удалось считать qr-code, введите сумму в чеке:', reply_markup=kb)
        await UserState.bonuses_edit_act_use_summ.set()


@dp.message_handler(state=UserState.bonuses_edit_act_use_summ)
async def bonuses_edit_act_use_summ(message: types.Message, state: FSMContext):
    if not await setstate('bonuses_edit_act_use_summ', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Список льгот'
        await reset_state(state, message)
        await message_handler_bonuses(message, state)
        return

    userdata = BotDB.get_userdata(message.from_user.id)
    try:
        summ = int(message.text)
    except:
        await message.bot.send_message(
            message.chat.id,
            f'Неверная сумма!\n'
            f'Введите количество бонусов для списания:')
        await bonuses_edit_act_use((await state.get_data())['bonuses_edit_act_use_message'], state)
        return
    bonuse_pay = userdata[8]
    if bonuse_pay > summ:
        bonuse_pay = summ
    await state.update_data(bonuses_edit_act_use_summ=summ)
    await state.update_data(bonuses_edit_act_use_pay=bonuse_pay)

    btn_payall = KeyboardButton(f'Списать максимум бонусов ({bonuse_pay})')
    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_payall).add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'<i><b>Сумма</b></i> - {summ}\n'
        f'<i><b>Доступно:</b></i> {userdata[8]} бонусов\n'
        f'Введите количество бонусов для списания:',
        reply_markup=kb)
    await UserState.bonuses_edit_act_use_pay.set()


@dp.message_handler(state=UserState.bonuses_edit_act_use_pay)
async def bonuses_edit_act_use_pay(message: types.Message, state: FSMContext):
    if not await setstate('bonuses_edit_act_use_pay', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Список льгот'
        await reset_state(state, message)
        await message_handler_bonuses(message, state)
        return

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_back)

    userdata = BotDB.get_userdata(message.from_user.id)
    bonuse = (await state.get_data())['bonuses_edit']
    check = (await state.get_data())['bonuses_edit_act_use_check']
    summ = (await state.get_data())['bonuses_edit_act_use_summ']
    bonuses = (await state.get_data())['bonuses_edit_act_use_pay']
    if 'Списать максимум бонусов' not in message.text:
        try:
            bonuses = int(message.text)
        except:
            await message.bot.send_message(
                message.chat.id,
                f'Неверная сумма!\n'
                f'Введите количество бонусов для списания:')
            await bonuses_edit_act_use((await state.get_data())['bonuses_edit_act_use_message'], state)
            return
    if bonuses > summ or bonuses > userdata[8]:
        btn_payall = KeyboardButton(f'Списать максимум бонусов ({bonuses})')
        kb.add(btn_payall).add(btn_back)
        await message.bot.send_message(
            message.chat.id,
            f'Неверное количество бонусов!\n'
            f'Доступно: {userdata[8]} бонусов\n'
            f'Введите количество бонусов для списания:', reply_markup=kb)
        await UserState.bonuses_edit_act_use_pay.set()
        return
    BotDB.user_set_points(userdata[2], userdata[8] - int(bonuses))
    await write_bonuse_log(message, 'bonuses_use', f"применил льготу '{bonuse[1]}'"
                                     f" (old balance: {userdata[8]}) (new balance: {userdata[8] - int(bonuses)})"
                                     f" Списано: {int(bonuses)}.",
                           bonuse[0],
                           check)
    await message.bot.send_message(
        message.chat.id,
        f'Списано {bonuses} бонусов за льготу <i><b>{bonuse[1]}</b></i>. Ожидайте возврата на карту.')
    await reset_state(state, message)
    await message_handler_bonuses(message, state)


@dp.message_handler(text='Выгрузка отчётов')
async def message_handler_reports(message: types.Message, state: FSMContext):
    if not await setstate(message.text, state, message):
        return

    if (await state.get_data())['role'] != 'hr':
        await message.bot.send_message(
            message.chat.id,
            f'Доступ запрещён!')
        await message_handler_office(message, state)
        return

    # кнопки
    btn_use_bonuse = KeyboardButton('Отчёт по списанию льгот')
    btn_fav_bonuse = KeyboardButton('Отчёт по статистике льгот')
    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_use_bonuse).add(btn_fav_bonuse).add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'Выберите действие:', reply_markup=kb)
    await UserState.reports_act.set()


@dp.message_handler(state=UserState.reports_act)
async def reports_act(message: types.Message, state: FSMContext):
    if not await setstate('reports_act', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Панель управления HR'
        await reset_state(state, message)
        await message_handler_hr_office(message, state)
        return

    # кнопки
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_back = KeyboardButton('Назад')
    kb.add(btn_back)

    match message.text:
        case 'Отчёт по статистике льгот':

            bonuse_uses = dict()
            # получаем названия бонусов
            bonuses_names = dict()
            for bonuse in BotDB.get_bonuses_names():
                bonuses_names.update({bonuse[1]: bonuse[2]})
                bonuse_uses.update({bonuse[1]: {'name': bonuse[2],
                                                'count_fav': 0,
                                                'count_use': 0,
                                                'all': 0,
                                                'average': 0}})

            date = datetime.datetime.today()
            month = datetime.datetime.today().month
            userdatas = BotDB.get_all_userdata()
            user_bonuses = []
            for userdata in userdatas:
                if userdata != '':
                    user_bonuses.append((userdata[9])[2:len(userdata[9]) - 2].split('", "'))
            if len(user_bonuses) != 0:
                for bonuses in user_bonuses:
                    for bonuse in bonuses:
                        if bonuses_names.get(bonuse) is not None:
                            bonuse_uses[bonuse]['count_fav'] += 1
            bonuse_logs = BotDB.get_all_bonuses_log()
            for bonuse_use in bonuse_logs:
                if bonuse_uses.get(bonuse_use[5]) is not None:
                    if datetime.datetime.strptime(bonuse_use[7], "%Y-%m-%d %H:%M:%S").month == month:
                        bonuse_uses[bonuse_use[5]]['count_use'] += 1
                        bonuse_uses[bonuse_use[5]]['all'] += int(bonuse_use[4][bonuse_use[4].find('Списано:')+9:-1])
            for bonuse in bonuse_uses.values():
                if bonuse['count_use'] > 0:
                    bonuse['average'] = bonuse['all'] / bonuse['count_use']
            sorted_bonuse_uses = dict(reversed(sorted(bonuse_uses.items(), key=lambda item: item[1]['count_use'])))
            if sorted_bonuse_uses == {}:
                await message.bot.send_message(
                    message.chat.id,
                    f'Действий за этот месяц не найдено.', reply_markup=kb)
                return
            # открываем новый файл на запись
            filename = f'Otchet_stat_{date.strftime("%Y-%m-%d_%H-%M-%S")}'
            workbook = xlsxwriter.Workbook(f'{config.reports_path}{filename}.xlsx')
            worksheet = workbook.add_worksheet()
            merge_format = workbook.add_format({'align': 'center'})
            thick_top_format = workbook.add_format({'top': 1})
            thick_bottom_format = workbook.add_format({'bottom': 1})
            thick_bottom_right_format = workbook.add_format({'bottom': 1, 'right': 1})
            thick_border_merge_format = workbook.add_format({'align': 'center', 'border': 2})
            money_format = workbook.add_format({'num_format': '# ##0.00 ₽'})
            money_thick_right_format = workbook.add_format({'num_format': '# ##0.00 ₽', 'right': 1})
            worksheet.merge_range('A1:F1', f'Отчёт {filename}.xlsx', merge_format)
            worksheet.merge_range('A2:F2', config.months[month - 1], thick_border_merge_format)
            worksheet.write('A3', '№', thick_bottom_format)
            worksheet.write('B3', 'Наименование', thick_bottom_format)
            worksheet.write('C3', 'Избранное', thick_bottom_format)
            worksheet.write('D3', 'Число списаний', thick_bottom_format)
            worksheet.write('E3', 'Сумма списаний', thick_bottom_format)
            worksheet.write('F3', 'Средняя сумма списаний', thick_bottom_right_format)
            worksheet.set_column('A:A', 5)
            worksheet.set_column('B:B', 30)
            worksheet.set_column('C:C', 15)
            worksheet.set_column('D:D', 16)
            worksheet.set_column('E:E', 16)
            worksheet.set_column('F:F', 25)
            i = 0
            for i, bonuse in enumerate(sorted_bonuse_uses.values(), start=4):
                worksheet.write(f'A{i}', i - 3)
                worksheet.write(f'B{i}', bonuse['name'])
                worksheet.write(f'C{i}', bonuse['count_fav'])
                worksheet.write(f'D{i}', bonuse['count_use'])
                worksheet.write(f'E{i}', bonuse['all'], money_format)
                worksheet.write(f'F{i}', bonuse['average'], money_thick_right_format)
                i += 1
            for n in range(0, 6):
                worksheet.write(i - 1, n, '', thick_top_format)
            workbook.close()

            await message.bot.send_message(
                message.chat.id,
                f'Отчёт формируется...')
            file = open(f'{config.reports_path}{filename}.xlsx', 'rb')
            await message.bot.send_document(message.chat.id, file)
        case 'Отчёт по списанию льгот':

            # получаем названия бонусов
            bonuses_names = dict()
            for bonuse in BotDB.get_bonuses_names():
                bonuses_names.update({bonuse[1]: bonuse[2]})

            date = datetime.datetime.today()
            month = datetime.datetime.today().month
            bonuse_logs = BotDB.get_all_bonuses_log()
            bonuse_uses = dict()
            for bonuse_use in bonuse_logs:
                if datetime.datetime.strptime(bonuse_use[7], "%Y-%m-%d %H:%M:%S").month == month:
                    if bonuse_uses.get(bonuse_use[3]) is None:
                        bonuse_uses.update({bonuse_use[3]: []})
                    bonuse_uses[bonuse_use[3]].append({
                        'fio': bonuse_use[4][:bonuse_use[4].find("('")],
                        'dep': bonuse_use[4][bonuse_use[4].find("('") + 2:bonuse_use[4].find("')")],
                        'bonuse': bonuse_use[5],
                        'summ': int(bonuse_use[4][bonuse_use[4].find('Списано:')+9:-1]),
                        'file_id': bonuse_use[6],
                        'date': bonuse_use[7]})
            if bonuse_uses == {}:
                await message.bot.send_message(
                    message.chat.id,
                    f'Действий за этот месяц не найдено.', reply_markup=kb)
                return
            # открываем новый файл на запись
            filename = f'Otchet_log_{date.strftime("%Y-%m-%d_%H-%M-%S")}'
            workbook = xlsxwriter.Workbook(f'{config.reports_path}{filename}.xlsx')
            worksheet = workbook.add_worksheet()
            merge_format = workbook.add_format({'align': 'center'})
            date_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
            thick_top_format = workbook.add_format({'top': 1})
            thick_bottom_format = workbook.add_format({'bottom': 1})
            thick_bottom_right_format = workbook.add_format({'bottom': 1, 'right': 1})
            thick_right_format = workbook.add_format({'right': 1})
            thick_border_merge_format = workbook.add_format({'align': 'center', 'border': 2})
            worksheet.merge_range('A1:G1', f'Отчёт {filename}.xlsx', merge_format)
            worksheet.merge_range('A2:G2', config.months[month - 1], thick_border_merge_format)
            worksheet.write('A3', '№', thick_bottom_format)
            worksheet.write('B3', 'ФИО сотрудника', thick_bottom_format)
            worksheet.write('C3', 'Отдел', thick_bottom_format)
            worksheet.write('D3', 'Льгота', thick_bottom_format)
            worksheet.write('E3', 'Сумма списания', thick_bottom_format)
            worksheet.write('F3', 'Дата', thick_bottom_format)
            worksheet.write('G3', 'Подтверждение', thick_bottom_right_format)
            worksheet.set_column('A:A', 5)
            worksheet.set_column('B:B', 30)
            worksheet.set_column('C:C', 22)
            worksheet.set_column('D:D', 20)
            worksheet.set_column('E:E', 16)
            worksheet.set_column('F:F', 20)
            worksheet.set_column('G:G', 30)

            archive = ZipFile(f'{config.reports_path}{filename}.zip', mode='w')
            i = 4
            for bonuses in bonuse_uses.items():
                for bonuse in bonuses[1]:
                    worksheet.write(f'A{i}', i - 3)
                    worksheet.write(f'B{i}', bonuse['fio'])
                    worksheet.write(f'C{i}', bonuse['dep'])
                    worksheet.write(f'D{i}', bonuses_names[bonuse['bonuse']])
                    worksheet.write(f'E{i}', bonuse['summ'])
                    worksheet.write(f'F{i}', bonuse['date'], date_format)
                    worksheet.write(f'G{i}', config.file_path + bonuse['file_id'], thick_right_format)
                    try:
                        archive.write(config.file_path + bonuse['file_id'])
                    finally:
                        pass
                    i += 1
            archive.close()
            for n in range(0, 7):
                worksheet.write(i - 1, n, '', thick_top_format)
            workbook.close()

            await message.bot.send_message(
                message.chat.id,
                f'Отчёт формируется...')
            file = open(f'{config.reports_path}{filename}.xlsx', 'rb')
            archive1 = open(f'{config.reports_path}{filename}.zip', 'rb')
            await message.bot.send_document(message.chat.id, file)
            await message.bot.send_document(message.chat.id, archive1)
    message.text = 'Выгрузка отчётов'
    await reset_state(state, message)
    await message_handler_reports(message, state)


@dp.message_handler(text='Сотрудники')
async def message_handler_employees(message: types.Message, state: FSMContext):
    if not await setstate(message.text, state, message):
        return

    if (await state.get_data())['role'] != 'hr':
        await message.bot.send_message(
            message.chat.id,
            f'Доступ запрещён!')
        await message_handler_office(message, state)
        return

    # кнопки
    btn_addemp = KeyboardButton('Добавить нового сотрудника')
    btn_findbyfio = KeyboardButton('Поиск по ФИО')
    btn_findbydep = KeyboardButton('Поиск по отделам')
    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_addemp).add(btn_findbyfio).add(btn_findbydep).add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'Выберите действие:', reply_markup=kb)


@dp.message_handler(text='Поиск по ФИО')
async def message_handler_findbyfio(message: types.Message, state: FSMContext):
    if not await setstate(message.text, state, message):
        return

    if (await state.get_data())['role'] != 'hr':
        await message.bot.send_message(
            message.chat.id,
            f'Доступ запрещён!')
        await message_handler_office(message, state)
        return

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    kb.add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'Введите ФИО или логин сотрудника:', reply_markup=kb)
    await UserState.findby_fio.set()


@dp.message_handler(text='Поиск по отделам')
async def message_handler_findbydep(message: types.Message, state: FSMContext):
    if not await setstate(message.text, state, message):
        return

    if (await state.get_data())['role'] != 'hr':
        await message.bot.send_message(
            message.chat.id,
            f'Доступ запрещён!')
        await message_handler_office(message, state)
        return

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    for dep in config.departs.values():
        kb.add(KeyboardButton(dep))

    kb.add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'Выберите отдел:', reply_markup=kb)
    await UserState.findby_dep.set()


@dp.message_handler(state=UserState.findby_dep)
async def check_dep(message: types.Message, state: FSMContext):
    if not await setstate('check_dep', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)
        return

    # кнопки
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_back = KeyboardButton('Назад')

    # получаем список сотрудников
    dep = [dep for dep in config.departs.keys() if message.text == config.departs.get(dep)][0]
    if len(dep) == 0:
        kb.add(btn_back)
        await message.bot.send_message(
            message.chat.id,
            f'Отдел не найден, повторите попытку!', reply_markup=kb)
        return
    usernames = BotDB.get_usernames_bydep(dep)
    usernames1 = [name[0] for name in usernames]
    for name in usernames1:
        kb.add(KeyboardButton(name))

    kb.add(btn_back)

    usernames1 = "\n-" + "\n-".join(usernames1)

    await reset_state(state, message)
    if len(usernames1) == 2:
        await message.bot.send_message(
            message.chat.id,
            f'Сотрудники не найдены!')
        await message_handler_employees(message, state)
    else:
        await message.bot.send_message(
            message.chat.id,
            f'<i><b>Найдено:</b></i>'
            f'{usernames1}', reply_markup=kb)
        await UserState.emp_edit.set()


@dp.message_handler(state=UserState.findby_fio)
async def check_fio(message: types.Message, state: FSMContext):
    if not await setstate('check_fio', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)
        return

    # кнопки
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    # получаем список имён сотрудников
    usernames = BotDB.get_allusernames()
    usernames1 = [name[0] for name in usernames if message.text.lower() in name[0].lower() or
                  message.text.lower() in name[1].lower()]
    for name in usernames1:
        kb.add(KeyboardButton(name))
    btn_back = KeyboardButton('Назад')
    kb.add(btn_back)
    usernames1 = "\n-" + "\n-".join(usernames1)

    await reset_state(state, message)
    if len(usernames1) == 2:
        await message.bot.send_message(
            message.chat.id,
            f'Сотрудник не найден!')
        message.text = 'Поиск по ФИО'
        await message_handler_findbyfio(message, state)
    else:
        await message.bot.send_message(
            message.chat.id,
            f'<i><b>Найдено:</b></i>'
            f'{usernames1}', reply_markup=kb)
        await UserState.emp_edit.set()


@dp.message_handler(state=UserState.emp_edit)
async def emp_edit(message: types.Message, state: FSMContext):
    if not await setstate('emp_edit', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)
        return

    # получаем логин сотрудника
    try:
        usernames = BotDB.get_allusernames()
        userdata = [name for name in usernames if message.text == name[0]][0]
        userdata1 = BotDB.get_userdata_bylogin(userdata[1])
    except:
        await message.bot.send_message(
            message.chat.id,
            f'Сотрудник не найден!')
        await reset_state(state, message)
        message.text = 'Сотрудники'
        await message_handler_employees(message, state)
        return

    if userdata1[2] == (await state.get_data())['login1']:
        await message.bot.send_message(
            message.chat.id,
            f'Вы не можете редактировать самого себя!')
        await reset_state(state, message)
        message.text = 'Сотрудники'
        await message_handler_employees(message, state)
        return

    await state.update_data(emp_edit=userdata)

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_edit_bonuse = KeyboardButton('Изменить баланс')
    btn_edit_fio = KeyboardButton('Изменить ФИО')
    btn_edit_login = KeyboardButton('Изменить логин')
    btn_edit_pass = KeyboardButton('Сбросить пароль')
    btn_del = KeyboardButton('Удалить сотрудника')

    kb.add(btn_edit_bonuse).add(btn_edit_fio).add(btn_edit_login).add(btn_edit_pass).add(btn_del).add(btn_back)

    year = ''
    last_year = int(str(userdata1[7])[-1])
    if last_year == 1:
        year = 'год'
    elif last_year > 1 and last_year < 5:
        year = 'года'
    elif last_year == 0 or last_year < 9:
        year = 'лет'

    await message.bot.send_message(
        message.chat.id,
        f'<i><b>{userdata1[4]}</b></i> - {config.roles.get(userdata1[5])}, {config.departs.get(userdata1[6])}\n'
        f'<i><b>Логин:</b></i> {userdata1[2]}\n'
        f'<i><b>Стаж:</b></i> {userdata1[7]} {year}\n'
        f'<i><b>Баланс:</b></i> {userdata1[8]}\n'
        f'Выберите действие:', reply_markup=kb)
    await UserState.emp_edit_act.set()


@dp.message_handler(state=UserState.emp_edit_act)
async def emp_edit_act(message: types.Message, state: FSMContext):
    if not await setstate('emp_edit_act', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)
        return

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    userdata = (await state.get_data())['emp_edit']
    match message.text:
        case "Изменить баланс":
            btn_addb = KeyboardButton('Добавить баланс')
            btn_minb = KeyboardButton('Отнять баланс')
            kb.add(btn_addb).add(btn_minb).add(btn_back)
            await message.bot.send_message(
                message.chat.id,
                f'<i><b>{userdata[0]}</b></i>\n'
                f'<i><b>Баланс:</b></i> {userdata[2]}\n'
                f'Выберите действие:', reply_markup=kb)
            await UserState.emp_edit_act_bonuse.set()
        case "Изменить ФИО":
            kb.add(btn_back)
            await message.bot.send_message(
                message.chat.id,
                f'Введите новое ФИО:', reply_markup=kb)
            await UserState.emp_edit_act_fio.set()
        case "Изменить логин":
            kb.add(btn_back)
            await message.bot.send_message(
                message.chat.id,
                f'Введите новый логин:', reply_markup=kb)
            await UserState.emp_edit_act_login.set()
        case "Сбросить пароль":
            kb.add(btn_back)
            password = ''
            for i in range(6):
                password += random.choice(config.password_chars)
            password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest().upper()
            BotDB.update_user_id(0, userdata[1])
            BotDB.set_password(password_md5, userdata[1])
            await write_log(message, 'hr', f"сбросил пароль сотрудника '{userdata[0]}' ('{userdata[1]}')")
            await message.bot.send_message(
                message.chat.id,
                f'Новый пароль для <i><b>{userdata[0]}</b></i> - {password}')
            message.text = 'Сотрудники'
            await reset_state(state, message)
            await message_handler_employees(message, state)
        case "Удалить сотрудника":
            try:
                BotDB.remove_user(userdata[1])
                await write_log(message, 'hr', f"удалил сотрудника '{userdata[0]}' ('{userdata[1]}')")
                await message.bot.send_message(
                    message.chat.id,
                    f'Сотрудник <i><b>{userdata[0]}</b></i> удалён.')
            except:
                await message.bot.send_message(
                    message.chat.id,
                    f'Что-то пошло не так...')
            finally:
                message.text = 'Сотрудники'
                await reset_state(state, message)
                await message_handler_employees(message, state)
        case _:
            message.text = (await state.get_data())['emp_edit'][0]
            await emp_edit(message, state)


@dp.message_handler(state=UserState.emp_edit_act_bonuse)
async def emp_edit_act_bonuse(message: types.Message, state: FSMContext):
    if not await setstate('emp_edit_act_bonuse', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)
        return

    userdata = (await state.get_data())['emp_edit']
    act = message.text

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_back)

    if act == 'Добавить баланс':
        await message.bot.send_message(
            message.chat.id,
            f'<i><b>{userdata[0]}</b></i>\n'
            f'<i><b>Баланс:</b></i> {userdata[2]}\n'
            f'Введите количество бонусов для добавления:', reply_markup=kb)
        await UserState.emp_edit_act_bonuse_add.set()
    elif act == 'Отнять баланс':
        await message.bot.send_message(
            message.chat.id,
            f'<i><b>{userdata[0]}</b></i>\n'
            f'<i><b>Баланс:</b></i> {userdata[2]}\n'
            f'Введите количество бонусов, которое надо отнять:', reply_markup=kb)
        await UserState.emp_edit_act_bonuse_del.set()
    else:
        message.text = 'Изменить баланс'
        await emp_edit_act(message, state)


@dp.message_handler(state=UserState.emp_edit_act_bonuse_add)
async def emp_edit_act_bonuse_add(message: types.Message, state: FSMContext):
    if not await setstate('emp_edit_act_bonuse_add', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)
        return

    userdata = (await state.get_data())['emp_edit']

    try:
        message.text = int(message.text)
    except:
        await message.bot.send_message(
            message.chat.id,
            f'Неверно введено число!')
        message.text = 'Добавить баланс'
        await emp_edit_act_bonuse(message, state)
        return

    if message.text < 1:
        await message.bot.send_message(
            message.chat.id,
            f'Неверно введено число!')
        message.text = 'Добавить баланс'
        await emp_edit_act_bonuse(message, state)
        return

    try:
        new_bonuses = userdata[2] + int(message.text)
        BotDB.user_set_points(userdata[1], new_bonuses)
        await write_log(message, 'hr', f"изменил баланс сотрудника '{userdata[0]}' ('{userdata[1]}')"
                                       f" (old balance: {userdata[2]}) (new balance: {new_bonuses}")
        await message.bot.send_message(
            message.chat.id,
            f'Новое количество бонусов <i><b>{userdata[0]}</b></i> - {new_bonuses}')
    except:
        await message.bot.send_message(
            message.chat.id,
            f'Что-то пошло не так...')
    finally:
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)


@dp.message_handler(state=UserState.emp_edit_act_bonuse_del)
async def emp_edit_act_bonuse_del(message: types.Message, state: FSMContext):
    if not await setstate('emp_edit_act_bonuse_del', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)
        return

    userdata = (await state.get_data())['emp_edit']

    try:
        message.text = int(message.text)
    except:
        await message.bot.send_message(
            message.chat.id,
            f'Неверно введено число!')
        message.text = 'Отнять баланс'
        await emp_edit_act_bonuse(message, state)
        return

    if message.text < 1 or message.text > userdata[2]:
        await message.bot.send_message(
            message.chat.id,
            f'Вы не можете отнять больше, чем {userdata[2]}!')
        message.text = 'Отнять баланс'
        await emp_edit_act_bonuse(message, state)
        return

    try:
        new_bonuses = userdata[2] - int(message.text)
        BotDB.user_set_points(userdata[1], new_bonuses)
        await write_log(message, 'hr', f"изменил баланс сотрудника '{userdata[0]}' ('{userdata[1]}')"
                                       f" (old balance: {userdata[2]}) (new balance: {new_bonuses}")
        await message.bot.send_message(
            message.chat.id,
            f'Новое количество бонусов {userdata[1]} - {new_bonuses}')
    except:
        await message.bot.send_message(
            message.chat.id,
            f'Что-то пошло не так...')
    finally:
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)


@dp.message_handler(state=UserState.emp_edit_act_fio)
async def emp_edit_act_fio(message: types.Message, state: FSMContext):
    if not await setstate('emp_edit_act_fio', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)
        return

    if BotDB.user_exists_byusername(message.text):
        await message.bot.send_message(
            message.chat.id,
            f'Сотрудник с таким ФИО уже существует, повторите попытку!')
        message.text = 'Изменить ФИО'
        await emp_edit_act(message, state)
        return

    userdata = (await state.get_data())['emp_edit']
    new_username = message.text

    try:
        BotDB.rename_user(userdata[1], new_username)
        await write_log(message, 'hr', f"изменил имя сотрудника '{userdata[0]}' ('{userdata[1]})' на {new_username}")
        await message.bot.send_message(
            message.chat.id,
            f'<i><b>{userdata[0]}</b></i> переименован в <i><b>{new_username}</b></i>')
    except:
        await message.bot.send_message(
            message.chat.id,
            f'Что-то пошло не так...')
    finally:
        await reset_state(state, message)
        await message_handler_employees(message, state)


@dp.message_handler(state=UserState.emp_edit_act_login)
async def emp_edit_act_login(message: types.Message, state: FSMContext):
    if not await setstate('emp_edit_act_login', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)
        return

    if BotDB.user_exists_bylogin(message.text):
        await message.bot.send_message(
            message.chat.id,
            f'Сотрудник с таким логином уже существует, повторите попытку!')
        message.text = 'Изменить логин'
        await emp_edit_act(message, state)
        return

    userdata = (await state.get_data())['emp_edit']
    new_login = message.text
    try:
        BotDB.set_login(userdata[1], new_login)
        await write_log(message, 'hr', f"изменил логин сотрудника '{userdata[0]}' ('{userdata[1]})' на '{new_login}'")
        await message.bot.send_message(
            message.chat.id,
            f'Новый логин для <i><b>{userdata[0]}</b></i> - {new_login}')
    except:
        await message.bot.send_message(
            message.chat.id,
            f'Что-то пошло не так...')
    finally:
        await reset_state(state, message)
        await message_handler_employees(message, state)


@dp.message_handler(text='Добавить нового сотрудника')
async def message_handler_addemp(message: types.Message, state: FSMContext):
    if not await setstate(message.text, state, message):
        return

    if (await state.get_data())['role'] != 'hr':
        await message.bot.send_message(
            message.chat.id,
            f'Доступ запрещён!')
        await message_handler_office(message, state)
        return

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'Введите ФИО сотрудника:', reply_markup=kb)
    await UserState.addemp_fio.set()


@dp.message_handler(state=UserState.addemp_fio)
async def addemp_fio(message: types.Message, state: FSMContext):
    if not await setstate('addemp_fio', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)
        return

    if BotDB.user_exists_byusername(message.text):
        await message.bot.send_message(
            message.chat.id,
            f'Сотрудник с таким ФИО уже существует, повторите попытку!')
        message.text = 'Добавить нового сотрудника'
        await message_handler_addemp(message, state)
        return

    await state.update_data(fio=message.text)
    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    kb.add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'Введите логин сотрудника:', reply_markup=kb)
    await UserState.addemp_login.set()


@dp.message_handler(state=UserState.addemp_login)
async def addemp_login(message: types.Message, state: FSMContext):
    if not await setstate('addemp_login', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)
        return

    if BotDB.user_exists_bylogin(message.text):
        await message.bot.send_message(
            message.chat.id,
            f'Сотрудник с таким логином уже существует, повторите попытку!')
        message.text = (await state.get_data())['fio']
        await addemp_fio(message, state)
        return

    await state.update_data(emp_login=message.text)

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    for dep in config.departs.values():
        kb.add(KeyboardButton(dep))

    kb.add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'Выберите отдел:', reply_markup=kb)
    await UserState.addemp_dep.set()


@dp.message_handler(state=UserState.addemp_dep)
async def addemp_dep(message: types.Message, state: FSMContext):
    if not await setstate('addemp_dep', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Сотрудники'
        await reset_state(state, message)
        await message_handler_employees(message, state)
        return

    fio = (await state.get_data())['fio']
    username = (await state.get_data())['emp_login']
    dep = [dep for dep in config.departs.keys() if message.text == config.departs.get(dep)]
    if len(dep) == 0:
        await message.bot.send_message(
            message.chat.id,
            f'Отдел не найден, повторите попытку!')
        message.text = (await state.get_data())['emp_login']
        await addemp_login(message, state)
        return
    password = ''
    for i in range(6):
        password += random.choice(config.password_chars)
    password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest().upper()
    try:
        BotDB.add_user(0, fio, username, password_md5, dep[0])
        await write_log(message, 'hr', f"добавил нового сотрудника '{fio}' ('{username}').")
        await message.bot.send_message(
            message.chat.id,
            f'Сотрудник успешно добавлен.\n\n'
            f'{message.text}.\n'
            f'<i><b>Логин:</b></i> {username}\n'
            f'<i><b>Пароль:</b></i> {password}')
    except:
        await message.bot.send_message(
            message.chat.id,
            f'Что-то пошло не так...')
    message.text = 'Сотрудники'
    await reset_state(state, message)
    await message_handler_employees(message, state)


@dp.message_handler(text='Кафетерий льгот')
async def message_handler_cafe(message: types.Message, state: FSMContext):
    if not await setstate(message.text, state, message):
        return

    if (await state.get_data())['role'] != 'hr':
        await message.bot.send_message(
            message.chat.id,
            f'Доступ запрещён!')
        await message_handler_office(message, state)
        return

    # кнопки
    btn_back = KeyboardButton('Назад')
    btn_add = KeyboardButton('Добавить льготу')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_add)
    # получаем список бонусов
    bonuses_names = dict()
    for bonuse in BotDB.get_bonuses_names():
        bonuses_names.update({bonuse[1]: bonuse[2]})
    bonuses = [bonuse for bonuse in bonuses_names.values()]
    for bonuse in bonuses:
        kb.add(KeyboardButton(bonuse))
    bonuses_names = "\n-" + "\n-".join(bonuses_names.values())

    kb.add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'<i><b>Список льгот:</b></i>'
        f'{bonuses_names}', reply_markup=kb)
    await UserState.cafe_edit.set()


@dp.message_handler(state=UserState.cafe_edit)
async def cafe_edit(message: types.Message, state: FSMContext):
    if not await setstate('cafe_edit', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Панель управления HR'
        await reset_state(state, message)
        await message_handler_hr_office(message, state)
        return

    if message.text == 'Добавить льготу':
        await cafe_edit_act_add(message, state)
        return

    bonuses_names = dict()
    for bonuse in BotDB.get_bonuses_names():
        bonuses_names.update({bonuse[1]: bonuse[2]})
    bonuse = [bonuse for bonuse in bonuses_names.values() if message.text in bonuse]
    if len(bonuse) != 1:
        bonuse = [bonuse for bonuse in bonuses_names.values() if message.text == bonuse]
        if len(bonuse) != 1:
            await message.bot.send_message(
                message.chat.id,
                f'Такой льготы не существует, повторите попытку!')
            await reset_state(state, message)
            message.text = 'Кафетерий льгот'
            await message_handler_cafe(message, state)
            return

    await state.update_data(cafe_edit=message.text)

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_edit = KeyboardButton('Изменить льготу')
    btn_add = KeyboardButton('Удалить льготу')
    kb.add(btn_edit).add(btn_add).add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'Льгота <i><b>{bonuse[0]}</b></i>\n'
        f'Выберите действие:', reply_markup=kb)
    await UserState.cafe_edit_act.set()


@dp.message_handler(state=UserState.cafe_edit_act)
async def cafe_edit_act(message: types.Message, state: FSMContext):
    if not await setstate('cafe_edit_act', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Кафетерий льгот'
        await reset_state(state, message)
        await message_handler_cafe(message, state)
        return

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    bonuse = (await state.get_data())['cafe_edit']
    match message.text:
        case "Изменить льготу":
            await state.update_data(cafe_edit_act=message.text)
            kb.add(btn_back)
            await message.bot.send_message(
                message.chat.id,
                f'Введите новое название льготы:', reply_markup=kb)
            await UserState.cafe_edit_act_rename.set()
        case "Удалить льготу":
            await state.update_data(cafe_edit_act=message.text)
            try:
                BotDB.remove_bonuse(bonuse)
                await write_log(message, 'hr', f"удалил льготу '{bonuse}'.")
                await message.bot.send_message(
                    message.chat.id,
                    f'Льгота <i><b>{bonuse}</b></i> удалена.')
            except:
                await message.bot.send_message(
                    message.chat.id,
                    f'Что-то пошло не так...')
            finally:
                message.text = 'Кафетерий льгот'
                await reset_state(state, message)
                await message_handler_cafe(message, state)
        case _:
            message.text = (await state.get_data())['cafe_edit']
            await cafe_edit(message, state)


@dp.message_handler(state=UserState.cafe_edit_act_add)
async def cafe_edit_act_add(message: types.Message, state: FSMContext):
    if not await setstate('cafe_edit_act_add', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Кафетерий льгот'
        await reset_state(state, message)
        await message_handler_cafe(message, state)
        return

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'Введите название льготы:', reply_markup=kb)
    await UserState.cafe_edit_act_add_name.set()


@dp.message_handler(state=UserState.cafe_edit_act_add_name)
async def cafe_edit_act_add_name(message: types.Message, state: FSMContext):
    if not await setstate('cafe_edit_act_add_name', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Кафетерий льгот'
        await reset_state(state, message)
        await message_handler_cafe(message, state)
        return

    if BotDB.get_bonuse_bydata(message.text):
        await message.bot.send_message(
            message.chat.id,
            f'Такая льгота уже существует, повторите попытку!')
        await cafe_edit_act_add(message, state)
        return

    await state.update_data(cafe_name=message.text)
    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'Введите короткое обозначение (например: Паркинг - park):', reply_markup=kb)
    await UserState.cafe_edit_act_add_sd.set()


@dp.message_handler(state=UserState.cafe_edit_act_add_sd)
async def cafe_edit_act_add_sd(message: types.Message, state: FSMContext):
    if not await setstate('cafe_edit_act_add_sd', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Кафетерий льгот'
        await reset_state(state, message)
        await message_handler_cafe(message, state)
        return

    if BotDB.get_bonuse_bydata(message.text):
        await message.bot.send_message(
            message.chat.id,
            f'Такая льгота уже существует, повторите попытку!')
        message.text = (await state.get_data())['cafe_name']
        await cafe_edit_act_add_name(message, state)
        return

    await state.update_data(cafe_sd=message.text)
    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_back)

    await message.bot.send_message(
        message.chat.id,
        f'Введите описание льготы:', reply_markup=kb)
    await UserState.cafe_edit_act_add_desc.set()


@dp.message_handler(state=UserState.cafe_edit_act_add_desc)
async def cafe_edit_act_add_desc(message: types.Message, state: FSMContext):
    if not await setstate('cafe_edit_act_add_desc', state, message):
        return

    await state.update_data(cafe_desc=message.text)
    if message.text == 'Назад':
        message.text = 'Кафетерий льгот'
        await reset_state(state, message)
        await message_handler_cafe(message, state)
        return

    btn_back = KeyboardButton('Назад')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(btn_back)

    bonuse = {"name": (await state.get_data())['cafe_name'],
              "data": (await state.get_data())['cafe_sd'],
              "desc": (await state.get_data())['cafe_desc']}
    try:
        BotDB.add_bonuse(bonuse["data"], bonuse["name"], bonuse["desc"])
        await write_log(message, 'hr', f"добавил льготу '{bonuse['name']}' ('{bonuse['data']}').")
        await message.bot.send_message(
            message.chat.id,
            f'Льгота - <i><b>{bonuse["name"]} ({bonuse["data"]})</b></i>\n'
            f'{bonuse["desc"]}\n'
            f'Добавлена успешно.')
    except:
        await message.bot.send_message(
            message.chat.id,
            f'Что-то пошло не так...')
    finally:
        message.text = 'Кафетерий льгот'
        await reset_state(state, message)
        await message_handler_cafe(message, state)


@dp.message_handler(state=UserState.cafe_edit_act_rename)
async def cafe_edit_act_rename(message: types.Message, state: FSMContext):
    if not await setstate('cafe_edit_act_rename', state, message):
        return

    if message.text == 'Назад':
        message.text = 'Кафетерий льгот'
        await reset_state(state, message)
        await message_handler_cafe(message, state)
        return

    bonuse = (await state.get_data())['cafe_edit']
    bonuse_new = message.text
    try:
        BotDB.rename_bonuse(bonuse, bonuse_new)
        await write_log(message, 'hr', f"изменил название льготы '{bonuse}' на '{bonuse_new}'.")
        await message.bot.send_message(
            message.chat.id,
            f'Льгота <i><b>{bonuse}</b></i> переименована в <i><b>{bonuse_new}</b></i>.')
    except:
        await message.bot.send_message(
            message.chat.id,
            f'Что-то пошло не так...')
    finally:
        message.text = 'Кафетерий льгот'
        await reset_state(state, message)
        await message_handler_cafe(message, state)


@dp.message_handler(text='Выйти из аккаунта')
async def message_handler_quit(message: types.Message, state: FSMContext):
    if not await setstate(message.text, state, message):
        return

    await write_log(message, 'user', f"вышел из аккаунта.")
    BotDB.update_user_id_byuserid(0, message.from_user.id)
    BotDB.update_last_login(message.from_user.id)
    btn = KeyboardButton('Авторизация')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(btn)
    await reset_state(state, message)
    await state.update_data(isloggedin=False)
    await message.bot.send_message(
        message.chat.id,
        'Вы вышли из аккаунта', reply_markup=kb)