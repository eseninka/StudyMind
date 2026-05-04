import telebot
from telebot import types
import psycopg2
from datetime import datetime
from datetime import timedelta
from datetime import date
import logging
from config_bot import host, name_user, password, database, connect, LinkLog
from bots_token import TokenTelegramBot

bot = telebot.TeleBot(TokenTelegramBot)
add_proj = {}
answers = {}
add_task = {'add': False, 'del': False}

flag_update_deadline = False
flag_update_progress = False
flag_update = False
num_intent = None
new_deadline = None
new_progress = None
data_intent = None
data_tasks = None
add_link = {}
del_link = {}

logging.basicConfig(filename=LinkLog, level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', encoding='utf-8')
logging.info('Программа запущена')


def main_menu():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📊 Диагностика", callback_data='diagnostics')
    btn2 = types.InlineKeyboardButton("🎯 Проекты/Экзамены", callback_data='projects')
    btn3 = types.InlineKeyboardButton("📅 Планер", callback_data='planner')
    btn4 = types.InlineKeyboardButton("🧩 Переходник", callback_data='adapter')
    markup.add(btn1)
    markup.add(btn2)
    markup.add(btn3)
    markup.add(btn4)
    return markup


@bot.message_handler(['start'])
def StartCommand(message):
    logging.info(f'Пользователь с id {message.chat.id} запустил бота')
    WelcomeTxt = f'🎓 Привет, {message.chat.username}!\nЯ — StudyMind, твой цифровой помощник в учёбе.\nЯ помогу тебе:\n• 📊 Проанализировать учебную нагрузку\n• 🎯 Ставить цели и отслеживать прогресс\n• 📅 Планировать задачи на день\nВыбери раздел ниже 👇'
    bot.send_message(message.chat.id, WelcomeTxt, reply_markup=main_menu())
    try:
        connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute('select * from users where user_id=%s', (str(message.chat.id),))
            if not cursor.fetchall():
                cursor.execute('insert into users values(%s, %s, %s, %s, %s)',
                               (str(message.chat.id), message.from_user.first_name, message.from_user.last_name,
                                message.chat.username, datetime.now()))
    except Exception as e:
        print(f'[info]: Ошибка {e}')
    finally:
        if connection:
            connection.close()
            print('[info]: коннект закрыт')


@bot.callback_query_handler(func=lambda callback: True)
def callback_handler(callback):
    global answers
    global add_proj
    global flag_update
    global flag_update_deadline
    global flag_update_progress
    global new_deadline
    global new_progress
    global add_task
    global add_link
    global num_intent


    if callback.data == 'diagnostics':
        logging.info(f'Пользователь с id {callback.message.chat.id} начал проходить диагностику')
        answers[callback.message.chat.id] = {'step': 1}
        text = '📊Диагностика учебной нагрузки\nСейчас мы проведём быстрый анализ твоего учебного процесса.\nОтветь на 3 простых вопроса — и я дам персональные рекомендации!\n\nПервый вопрос:\n1/3 ⏰ Сколько часов в день ты обычно учишься? (Учитывай уроки в школе, домашку, доп. занятия)'
        bot.send_message(callback.message.chat.id, text)
    if callback.data == 'results':
        logging.info(f'Пользователь с id {callback.message.chat.id} получил результаты диагностики')

        common = f'Твои ответы:\nЧасы в день - {answers[callback.message.chat.id]['hours']}\nСамый сложный предмет - {answers[callback.message.chat.id]['subject']}\nДни с допольнительными занятиями - {answers[callback.message.chat.id]['day']}'
        recommendations = ''
        if int(answers[callback.message.chat.id]['hours']) < 4:
            recommendations += "🔼 Увеличь учебное время до 4-6 часов"
        elif int(answers[callback.message.chat.id]['hours']) > 6:
            recommendations += "🔽 Уменьши нагрузку до 4-6 часов"
        else:
            recommendations += "✅ Учебная нагрузка оптимальна"

        recommendations += f"\n📚 Удели больше внимания предмету: {answers[callback.message.chat.id]['subject']}, т.е. начни уделять ему на 30-40 минут больше"

        if int(answers[callback.message.chat.id]['day']) > 4:
            recommendations += "\n🎯 Слишком много доп. занятий, оставь 2 дня для отдыха"
        else:
            recommendations += "\n✅ Дополнительные занятия в норме"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("На главный раздел", callback_data='main'))
        bot.send_message(callback.message.chat.id, common)
        bot.send_message(callback.message.chat.id, recommendations, reply_markup=markup)
        try:
            connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute('select * from user_tips where user_id=%s', (str(callback.message.chat.id),))
                if not cursor.fetchall():
                    cursor.execute('insert into user_tips values(%s, %s, %s, %s, %s)',
                                   (str(callback.message.chat.id), int(answers[callback.message.chat.id]['hours']),
                                    answers[callback.message.chat.id]['subject'],
                                    int(answers[callback.message.chat.id]['day']), datetime.now()))
                else:
                    cursor.execute(
                        'update user_tips set hours=%s, subject=%s, extra_day=%s, diag_date=%s where user_id=%s',
                        (int(answers[callback.message.chat.id]['hours']),
                         answers[callback.message.chat.id]['subject'],
                         int(answers[callback.message.chat.id]['day']), datetime.now(), str(callback.message.chat.id)))
        except Exception as e:
            print(f'[info]: Ошибка {e}')
        finally:
            if connection:
                connection.close()
                print('[info]: коннект закрыт')
        del answers[callback.message.chat.id]
    if callback.data == 'main':
        logging.info(f'Пользователь с id {callback.message.chat.id} открыл главное меню')
        bot.send_message(callback.message.chat.id, 'Главная страница бота', reply_markup=main_menu())
    if callback.data == 'projects':
        logging.info(f'Пользователь с id {callback.message.chat.id} открыл меню управления проектами')
        if callback.message.chat.id in add_proj.keys():
            del add_proj[callback.message.chat.id]
        if flag_update or flag_update_deadline or flag_update_progress:
            flag_update = False
            flag_update_deadline = False
            flag_update_progress = False

        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Посмотреть свои проекты/цели", callback_data='show_projects')
        btn2 = types.InlineKeyboardButton("Добавить проект/цель", callback_data='add_projects')
        btn3 = types.InlineKeyboardButton("Назад", callback_data='main')
        markup.add(btn1)
        markup.add(btn2)
        markup.add(btn3)
        text = '🎯 Управление целями\nЗдесь ты можешь ставить большие учебные цели и отслеживать прогресс:\n• Подготовка к ЕГЭ/ОГЭ\n• Участие в олимпиадах\n• Исследовательские проекты\n• Долгосрочные учебные задачи\nВыбери действие:'
        bot.send_message(callback.message.chat.id, text, reply_markup=markup)
    if callback.data == 'show_projects':
        logging.info(f'Пользователь с id {callback.message.chat.id} открыл свои актуальные проекты')
        try:
            connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("select * from user_intent where user_id=%s and condition_intent='0' order by intent_num",
                               (str(callback.message.chat.id),))
                data_intent = cursor.fetchall()
            if data_intent:
                text = ''
                for number, intent in enumerate(data_intent, start=1):
                    days_left = (intent[5] - date.today()).days
                    if days_left > 0:
                        days_text = f"⏳ осталось дней: {days_left}"
                    elif days_left == 0:
                        days_text = "⏰ срок сегодня!"
                    else:
                        days_text = f"⚠️ просрочено на {-days_left} дней"
                    text += f"№{number} - {intent[2]}\nПрогресс:{intent[3]}%\n0%:{'🟩' * (intent[3] // 10)}{'⬜' * (10 - intent[3] // 10)}:100%\n{days_text}\n\n"
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("Назад", callback_data='projects')
                btn2 = types.InlineKeyboardButton('Обновить проект', callback_data='update')
                btn3 = types.InlineKeyboardButton('Посмотреть законченные проекты', callback_data='finished_projects')
                markup.add(btn1)
                markup.add(btn2)
                markup.add(btn3)
                bot.send_message(callback.message.chat.id, text, reply_markup=markup)

            else:
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton('Назад', callback_data='projects')
                btn2 = types.InlineKeyboardButton('Добавить проект', callback_data='add_projects')
                markup.add(btn1, btn2)
                bot.send_message(callback.message.chat.id, 'У тебя нет задач в процессе', reply_markup=markup)
        except Exception as e:
            print(f'[info]: Ошибка {e}')
        finally:
            if connection:
                connection.close()
                print('[info]: коннект закрыт')
    if callback.data == 'add_projects':
        logging.info(f'Пользователь с id {callback.message.chat.id} добавляет проект')
        add_proj[callback.message.chat.id] = {'step': 1}
        text = '🎯 Добавление новой цели\n\nШаг 1/3: Название цели\nНапиши свою цель одной фразой.\nНапример: "Сдать ЕГЭ по математике на 85+ баллов"'
        bot.send_message(callback.message.chat.id, text)
    if callback.data == 'save_intent':
        logging.info(f'Пользователь с id {callback.message.chat.id} сохраняет проект')
        try:
            connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
            connection.autocommit = True
            deadline = add_proj[callback.message.chat.id]['deadline']
            with connection.cursor() as cursor:
                cursor.execute(
                    'insert into user_intent(user_id,intent_name, intent_progress, intent_deadline) values (%s, %s, %s, %s)',
                    (
                        str(callback.message.chat.id),
                        add_proj[callback.message.chat.id]['intent'],
                        int(add_proj[callback.message.chat.id]['progress']),
                        deadline))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("На главный раздел", callback_data='main'))
            bot.send_message(callback.message.chat.id,
                             f'Задача {add_proj[callback.message.chat.id]['intent']} успешно добавлена! До конца её выполнения осталось {(deadline - date.today()).days} дней',
                             reply_markup=markup)
            del add_proj[callback.message.chat.id]
        except Exception as e:
            print(f'[info]: Ошибка {e}')
        finally:
            if connection:
                connection.close()
                print('[info]: коннект закрыт')
    if callback.data == 'update':
        logging.info(f'Пользователь с id {callback.message.chat.id} обновляет проект')
        flag_update = True
        text = 'Отлично! Введи номер проекта, который хочешь изменить'
        bot.send_message(callback.message.chat.id, text)
    if callback.data == 'update_deadline':
        logging.info(f'Пользователь с id {callback.message.chat.id} обновляет дедлайн проекта')
        flag_update_deadline = True
        flag_update = False
        text = 'Окей, введи новую дату в формате dd.mm.YYYY'
        bot.send_message(callback.message.chat.id, text)
    if callback.data == 'save_update_deadline':
        try:
            connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("select * from user_intent where user_id=%s and condition_intent='0' order by intent_num",
                        (str(callback.message.chat.id),))
                data_intent = cursor.fetchall()
                data = data_intent
                object_changes = data[num_intent - 1][1]
                cursor.execute("update user_intent set intent_deadline=%s where intent_num=%s and condition_intent='0'",
                               (new_deadline, object_changes))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("На раздел управления проектами", callback_data='projects'))
            bot.send_message(callback.message.chat.id, 'Дата успешно изменена!', reply_markup=markup)
            logging.info(f'Пользователь с id {callback.message.chat.id} сохранил новый дедлайн - {new_deadline}')

        except Exception as e:
            print(f'[info]: Ошибка {e}')
        finally:
            if connection:
                connection.close()
                print('[info]: коннект закрыт')
    if callback.data == 'update_progress':
        logging.info(f'Пользователь с id {callback.message.chat.id} обновляет прогресс проекта')
        flag_update_progress = True
        flag_update = False
        text = 'Окей, введи новый прогресс'
        bot.send_message(callback.message.chat.id, text)
    if callback.data == 'save_update_progress':
        try:
            connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("select * from user_intent where user_id=%s and condition_intent='0' order by intent_num",
                              (str(callback.message.chat.id),))
                data_intent = cursor.fetchall()
                data = data_intent
                object_changes = data[num_intent - 1][1]
                cursor.execute("update user_intent set intent_progress=%s where intent_num=%s and condition_intent='0'",
                               (new_progress, object_changes))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("На раздел управления проектами", callback_data='projects'))
            bot.send_message(callback.message.chat.id, 'Прогресс успешно изменён!', reply_markup=markup)
            logging.info(f'Пользователь с id {callback.message.chat.id} сохранил новый прогресс - {new_progress}')

        except Exception as e:
            print(f'[info]: Ошибка {e}')
        finally:
            if connection:
                connection.close()
                print('[info]: коннект закрыт')
    if callback.data == 'end_intent':
        try:
            connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("select * from user_intent where user_id=%s and condition_intent='0' order by intent_num",
                              (str(callback.message.chat.id),))
                data_intent = cursor.fetchall()
                data = data_intent
                object_changes = data[num_intent - 1][1]
                cursor.execute("update user_intent set intent_progress=100, condition_intent='1' where intent_num=%s",
                               (object_changes,))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("На раздел управления проектами", callback_data='projects'))
            bot.send_message(callback.message.chat.id, 'Проект закончен!', reply_markup=markup)
            logging.info(f'Пользователь с id {callback.message.chat.id} закончил проект номер {intent_num}')

        except Exception as e:
            print(f'[info]: Ошибка {e}')
        finally:
            if connection:
                connection.close()
                print('[info]: коннект закрыт')

    if callback.data == 'finished_projects':
        try:
            connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("select * from user_intent where user_id=%s and condition_intent='1'",
                               (str(callback.message.chat.id),))
                data_intent = cursor.fetchall()
            if data_intent:
                text = ''
                for number, intent in enumerate(data_intent, start=1):
                    text += f"№{number} - {intent[2]}\nПрогресс:{intent[3]}%\n0%:{'🟩' * (intent[3] // 10)}{'⬜' * (10 - intent[3] // 10)}:100%\nДедлайн {intent[5]}\n\n"
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("Назад", callback_data='show_projects')
                markup.add(btn1)
                bot.send_message(callback.message.chat.id, text, reply_markup=markup)
            else:
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton('Назад', callback_data='show_projects')
                markup.add(btn1)
                bot.send_message(callback.message.chat.id, 'У тебя нет завершённых задач', reply_markup=markup)
            logging.info(f'Пользователь с id {callback.message.chat.id} посмотрел завершённые проекты')

        except Exception as e:
            print(f'[info]: Ошибка {e}')
        finally:
            if connection:
                connection.close()
                print('[info]: коннект закрыт')
    if callback.data == 'planner':
        logging.info(f'Пользователь с id {callback.message.chat.id} открыл управление задачами на сегодня')
        if callback.message.chat.id in add_task.keys():
            del add_task[callback.message.chat.id]
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Посмотреть свои цели на сегодня", callback_data='show_tasks')
        btn2 = types.InlineKeyboardButton("Добавить цель на сегодня", callback_data='add_tasks')
        btn3 = types.InlineKeyboardButton("Назад", callback_data='main')
        markup.add(btn1)
        markup.add(btn2)
        markup.add(btn3)
        bot.send_message(callback.message.chat.id,
                         '📅 Планировщик учебного дня\nЗдесь ты можешь:\n• 📝 Добавить задачу на сегодня\n• 📋 Посмотреть текущий список\n• ✅ Отметить выполненное\n• 🕐 Посмотреть вчерашние задачи\n\nПростой способ организовать день и не забыть о важном! ✨',
                         reply_markup=markup)

    if callback.data == 'show_tasks':
        logging.info(f'Пользователь с id {callback.message.chat.id} открыл свои задачи на сегодня')
        try:
            connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("select * from user_tasks where user_id=%s and task_create_at=%s and del_tasks='0' order by task_num",
                               (str(callback.message.chat.id), date.today()))
                data_tasks = cursor.fetchall()
            if data_tasks:
                text = f'Задачи на {date.today()}\n'
                for number, task in enumerate(data_tasks, start=1):
                    text += f"№{number} - {task[2]}\n"
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton('Удалить задачу', callback_data='del_task')
                btn2 = types.InlineKeyboardButton('Посмотреть вчерашние задачи', callback_data='yesterday_task')
                btn3 = types.InlineKeyboardButton("Назад", callback_data='planner')
                markup.add(btn1)
                markup.add(btn2)
                markup.add(btn3)
                bot.send_message(callback.message.chat.id, text, reply_markup=markup)
            else:
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton('Назад', callback_data='planner')
                btn2 = types.InlineKeyboardButton('Посмотреть вчерашние задачи', callback_data='yesterday_task')
                markup.add(btn1)
                markup.add(btn2)
                bot.send_message(callback.message.chat.id, 'У тебя нет задач на сегодня', reply_markup=markup)
        except Exception as e:
            print(f'[info]: Ошибка {e}')
        finally:
            if connection:
                connection.close()
                print('[info]: коннект закрыт')
    if callback.data == 'add_tasks':
        logging.info(f'Пользователь с id {callback.message.chat.id} добавляет задачу')
        add_task[callback.message.chat.id] = {'add': True, 'del': False}
        text = 'Хорошо! Давай добавим новую задачу на сегодня. Сначала введи название типа (например: "Решить домашнее задание по математике")'
        bot.send_message(callback.message.chat.id, text)
    if callback.data == 'save_task':
        logging.info(f'Пользователь с id {callback.message.chat.id} сохранил задачу')
        try:
            connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute('insert into user_tasks(user_id,task_name, task_create_at) values (%s, %s, %s)', (
                    str(callback.message.chat.id), add_task[callback.message.chat.id]['task'], date.today()))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("На раздел управления задачами", callback_data='planner'))
            bot.send_message(callback.message.chat.id, 'Задача на сегодня упешно добавлена!', reply_markup=markup)
        except Exception as e:
            print(f'[info]: Ошибка {e}')
        finally:
            if connection:
                connection.close()
                print('[info]: коннект закрыт')
    if callback.data == 'del_task':
        add_task[callback.message.chat.id] = {'add': False, 'del': True}
        text = 'Хорошо! Давай удалим задачу, введи её номер'
        bot.send_message(callback.message.chat.id, text)
    if callback.data == 'delete_task':
        try:
            connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("select * from user_tasks where user_id=%s and task_create_at=%s and del_tasks='0' order by task_num",
                           (str(callback.message.chat.id), date.today()))
                data_tasks = cursor.fetchall()
            del_task = data_tasks[add_task[callback.message.chat.id]['del_task'] - 1][1]
            logging.info(f'Пользователь с id {callback.message.chat.id} удалил задачу номер {del_task}')
            with connection.cursor() as cursor:
                cursor.execute("update user_tasks set del_tasks='1' where user_id=%s and task_num=%s",
                               (str(callback.message.chat.id), del_task))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("На раздел управления задачами", callback_data='planner'))
            bot.send_message(callback.message.chat.id, 'Задача на сегодня упешно удалена!', reply_markup=markup)
        except Exception as e:
            print(f'[info]: Ошибка {e}')
        finally:
            if connection:
                connection.close()
                print('[info]: коннект закрыт')
    if callback.data == 'yesterday_task':
        logging.info(f'Пользователь с id {callback.message.chat.id} открыл свои вчерашние задачи')
        try:
            connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("select * from user_tasks where user_id=%s and task_create_at=%s and del_tasks='0' order by task_num",
                               (str(callback.message.chat.id), date.today() - timedelta(days=1)))
                data_tasks = cursor.fetchall()
            if data_tasks:
                text = f'Задачи на {date.today() - timedelta(days=1)}\n'
                for number, task in enumerate(data_tasks, start=1):
                    text += f"№{number} - {task[2]}\n"
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("Назад", callback_data='show_tasks')
                markup.add(btn1)
                bot.send_message(callback.message.chat.id, text, reply_markup=markup)
            else:
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton('Назад', callback_data='show_tasks')
                markup.add(btn1)
                bot.send_message(callback.message.chat.id, 'У тебя нет вчерашних задач', reply_markup=markup)
        except Exception as e:
            print(f'[info]: Ошибка {e}')
        finally:
            if connection:
                connection.close()
                print('[info]: коннект закрыт')
    if callback.data == 'adapter':
        if callback.message.chat.id in add_link.keys():
            del add_link[callback.message.chat.id]
        text = "В этот раздел вы можете поместить рабочие ссылки для учебы/проектов или посмотреть существующие"
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Добавить вкладку', callback_data='add_link')
        btn2 = types.InlineKeyboardButton('Посмотреть текущие вкладки', callback_data='show_link')
        btn3 = types.InlineKeyboardButton('Назад', callback_data='main')
        markup.add(btn1)
        markup.add(btn2)
        markup.add(btn3)
        bot.send_message(callback.message.chat.id, text, reply_markup=markup)

    if callback.data == 'add_link':
        text = 'Пожалуйста, введите ссылку сайта или диска, на котором вы работаете'
        add_link[callback.message.chat.id] = {'step': 1}
        bot.send_message(callback.message.chat.id, text)

    if callback.data == 'save_link':
        logging.info(f'Пользователь с id {callback.message.chat.id} сохраняет ccылку')
        try:
            connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
            connection.autocommit = True
            name = add_link[callback.message.chat.id]['name_link_users']
            link = add_link[callback.message.chat.id]['link_from_users']
            emoj = add_link[callback.message.chat.id]['emo_link_users']
            with connection.cursor() as cursor:
                cursor.execute(
                    'insert into user_href(user_id, name_link, links, emoj) values (%s, %s, %s, %s)',
                    (str(callback.message.chat.id), name, link, emoj))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("На главный раздел", callback_data='adapter'))
            bot.send_message(callback.message.chat.id,
                             f'Ссылка {name} успешно добавлена! Теперь ты можешь быстро по ней переходить',reply_markup=markup)
            del add_link[callback.message.chat.id]
        except Exception as e:
            print(f'[info]: Ошибка {e}')
        finally:
            if connection:
                connection.close()
                print('[info]: коннект закрыт')
    if callback.data == 'show_link':
        logging.info(f'Пользователь с id {callback.message.chat.id} открыл свои ссылки')
        try:
            connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("select * from user_href where user_id=%s and del_link='0'",
                               (str(callback.message.chat.id),))
                link_data = cursor.fetchall()

            markup = types.InlineKeyboardMarkup()
            if link_data:
                text = 'Ваши вкладки'
                for link in link_data:
                    text_link = link[2] + ' ' + link[4]
                    url = link[3]
                    new_but = types.InlineKeyboardButton(text_link, url=url)
                    markup.add(new_but)
                last_but = types.InlineKeyboardButton('Назад', callback_data='adapter')
                markup.add(last_but)
                bot.send_message(callback.message.chat.id, text, reply_markup=markup)
            else:
                text = 'Ошибка! У вас нет актуальных ссылок'
                btn1 = types.InlineKeyboardButton('Добавить ссылку', callback_data='add_link')
                btn2 = types.InlineKeyboardButton('Назад', callback_data='adapter')
                markup.add(btn1)
                markup.add(btn2)
                bot.send_message(callback.message.chat.id, text, reply_markup=markup)
        except Exception as e:
            print(f'[info]: Ошибка {e}')
        finally:
            if connection:
                connection.close()
                print('[info]: коннект закрыт')

@bot.message_handler(func=lambda message: True)
def text_handler(message):
    global answers
    global add_proj
    global flag_update_deadline
    global flag_update_progress
    global flag_update
    global num_intent
    global new_deadline
    global new_progress
    global add_task
    global add_link

    if message.chat.id in answers:
        step = answers[message.chat.id]['step']

        if step == 1:
            if message.text.strip().isdigit() and (int(message.text.strip()) < 24):
                answers[message.chat.id]['hours'] = message.text.strip()
                answers[message.chat.id]['step'] = 2
                bot.send_message(message.chat.id,
                                 "2/3 📚 Какой предмет даётся сложнее всего?\nВыбери или напиши свой вариант")
            else:
                bot.send_message(message.chat.id, "Введи число часов, типа '5'")

        elif step == 2:
            answers[message.chat.id]['subject'] = message.text.strip()
            answers[message.chat.id]['step'] = 3
            bot.send_message(message.chat.id,
                             "3/3 📅 Сколько дней в неделю у тебя дополнительные занятия?(Кружки, репетиторы, секции)")
        elif step == 3:
            if message.text.strip().isdigit() and (int(message.text.strip()) < 8):
                answers[message.chat.id]['day'] = message.text.strip()
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Подвести итоги диагностики", callback_data='results'))
                bot.send_message(message.chat.id, "Отлично! Давай подведм итоги", reply_markup=markup)
            else:
                bot.send_message(message.chat.id, "Введи число дней в неделю, типа '3'")
    if message.chat.id in add_proj:
        step = add_proj[message.chat.id]['step']
        if step == 1:
            add_proj[message.chat.id]['intent'] = message.text.strip()
            add_proj[message.chat.id]['step'] = 2
            text = '📊 Шаг 2/3: Текущий прогресс\nНа сколько процентов цель уже выполнена?\nВведи число от 0 до 100 (можно со знаком %)'
            bot.send_message(message.chat.id, text)
        elif step == 2:
            progr = message.text.strip('%')
            if progr.isdigit() and (int(progr) <= 99 and int(progr) >= 0):
                add_proj[message.chat.id]['progress'] = progr
                add_proj[message.chat.id]['step'] = 3
                text = '📅 Шаг 3/3: Срок выполнения\nДо какого числа планируешь достичь цель?\nВведи дату в формате ДД.ММ.ГГГГ\nНапример: 25.06.2026'
                bot.send_message(message.chat.id, text)
            else:
                bot.send_message(message.chat.id, 'Ошибка! Введи от 0% до 99%')
        elif step == 3:
            try:
                add_proj[message.chat.id]['deadline'] = datetime.strptime(message.text.strip(), '%d.%m.%Y').date()
                if add_proj[message.chat.id]['deadline'] >= date.today():
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("Отменить", callback_data='projects'),
                               types.InlineKeyboardButton("Записать", callback_data='save_intent'))
                    bot.send_message(message.chat.id, "Записать задачу?", reply_markup=markup)
                else:
                    bot.send_message(message.chat.id, "Ошибка! Введи дату в будущем!")
            except Exception:
                bot.send_message(message.chat.id, "Ошибка! Введи дату в правильном формате -> dd.mm.YYYY")
    if flag_update:
        if message.text.strip().isdigit():
            try:
                connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
                connection.autocommit = True
                with connection.cursor() as cursor:
                    cursor.execute(
                        "select * from user_intent where user_id=%s and condition_intent='0' order by intent_num",
                        (str(message.chat.id),))
                    data_intent = cursor.fetchall()
                if int(message.text.strip()) <= len(data_intent):
                    num_intent = int(message.text.strip())
                    text = f'🔄 Обновление цели №{num_intent}\nЧто ты хочешь изменить?\n• Дедлайн — если срок изменился\n• Прогресс — если продвинулся в выполнении'
                    markup = types.InlineKeyboardMarkup()
                    btn1 = types.InlineKeyboardButton("Дедлайн", callback_data='update_deadline')
                    btn2 = types.InlineKeyboardButton("Прогресс", callback_data='update_progress')
                    markup.add(btn1, btn2)
                    bot.send_message(message.chat.id, text, reply_markup=markup)
                else:
                    bot.send_message(message.chat.id, "Нет такой задачи! Введи корректный номер задачи")
            except Exception as e:
                print(f'[info]: Ошибка {e}')
            finally:
                if connection:
                    connection.close()
                    print('[info]: коннект закрыт')
        else:
            bot.send_message(message.chat.id, 'Введите корректный номер задачи! - просто цифра или число')
    if flag_update_deadline:
        try:
            new_deadline = datetime.strptime(message.text.strip(), '%d.%m.%Y').date()
            if new_deadline >= date.today():
                markup = types.InlineKeyboardMarkup()
                text = f'Изменить дату на {new_deadline}?'
                btn1 = types.InlineKeyboardButton("Да", callback_data='save_update_deadline')
                btn2 = types.InlineKeyboardButton("Отмена", callback_data='projects')
                markup.add(btn1, btn2)
                bot.send_message(message.chat.id, text, reply_markup=markup)
            else:
                bot.send_message(message.chat.id, "Ошибка! Введи дату в будущем!")
        except Exception:
            bot.send_message(message.chat.id, "Ошибка! Введи новую дату в правильном формате -> dd.mm.YYYY")
    if flag_update_progress:
        new_progress = message.text.strip('%')
        if new_progress.isdecimal():
            if new_progress.isdigit() and (int(new_progress) < 100 and int(new_progress) >= 0):
                markup = types.InlineKeyboardMarkup()
                text = f'Изменить прогресс на {new_progress}?'
                btn1 = types.InlineKeyboardButton("Да", callback_data='save_update_progress')
                btn2 = types.InlineKeyboardButton("Отмена", callback_data='projects')
                markup.add(btn1, btn2)
                bot.send_message(message.chat.id, text, reply_markup=markup)
            elif int(new_progress) == 100:
                markup = types.InlineKeyboardMarkup()
                text = f'Изменить прогресс на {new_progress}?'
                btn1 = types.InlineKeyboardButton("Да", callback_data='end_intent')
                btn2 = types.InlineKeyboardButton("Отмена", callback_data='projects')
                markup.add(btn1, btn2)
                bot.send_message(message.chat.id, text, reply_markup=markup)
            else:
                bot.send_message(message.chat.id, 'Ошибка! Введи новый прогресс от 0% до 100%')
        else:
            bot.send_message(message.chat.id,
                             'Ошибка! Введи новый прогресс от 0% до 100% (обязательно десятичное число)')

    if message.chat.id in add_task.keys():
        if add_task[message.chat.id]['add']:
            add_task[message.chat.id]['task'] = message.text.strip()
            text = f'Добавить задачу? - {add_task[message.chat.id]['task']}'
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("Да", callback_data='save_task')
            btn2 = types.InlineKeyboardButton("Отмена", callback_data='planner')
            markup.add(btn1, btn2)
            bot.send_message(message.chat.id, text, reply_markup=markup)
        elif add_task[message.chat.id]['del']:
            try:
                connection = psycopg2.connect(host=host, user=name_user, password=password, database=database)
                connection.autocommit = True
                with connection.cursor() as cursor:
                    cursor.execute(
                        "select * from user_tasks where user_id=%s and task_create_at=%s and del_tasks='0' order by task_num",
                        (str(message.chat.id), date.today()))
                    data_tasks = cursor.fetchall()
                if int(message.text.strip()) <= len(data_tasks):
                    add_task[message.chat.id]['del_task'] = int(message.text.strip())
                    text = f'Удалить задачу №{add_task[message.chat.id]['del_task']}'
                    markup = types.InlineKeyboardMarkup()
                    btn1 = types.InlineKeyboardButton("Да", callback_data='delete_task')
                    btn2 = types.InlineKeyboardButton("Отмена", callback_data='planner')
                    markup.add(btn1, btn2)
                    bot.send_message(message.chat.id, text, reply_markup=markup)
                else:
                    bot.send_message(message.chat.id, "Нет такой задачи! Введи корректный номер задачи")
            except Exception as e:
                print(f'[info]: Ошибка {e}')
            finally:
                if connection:
                    connection.close()
                    print('[info]: коннект закрыт')
    if message.chat.id in add_link.keys():
        if add_link[message.chat.id]['step'] == 1:
            link_from_users = message.text.strip()
            if link_from_users.startswith('https://'):
                add_link[message.chat.id]['link_from_users'] = link_from_users
                add_link[message.chat.id]['step'] = 2
                text = 'Пожалуйста, подпишите ссылку (вы будете видеть этот текст, а не саму ссылку)'
                bot.send_message(message.chat.id, text)
            else:
                bot.send_message(message.chat.id, "! Неправильный формат ссылки (ссылка должна начинаться на https)")
        elif add_link[message.chat.id]['step'] == 2:
            name_link_users = message.text.strip()
            add_link[message.chat.id]['name_link_users'] = name_link_users
            add_link[message.chat.id]['step'] = 3
            text = 'Пожалуйста, присвойте ссылке эмодзи'
            bot.send_message(message.chat.id, text)
        elif add_link[message.chat.id]['step'] == 3:
            emo_link_users = message.text.strip()
            add_link[message.chat.id]['emo_link_users'] = emo_link_users
            text = 'Отлично! Сохранить ссылку?'
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("Да", callback_data='save_link')
            btn2 = types.InlineKeyboardButton("Отмена", callback_data='adapter')
            markup.add(btn1, btn2)
            bot.send_message(message.chat.id, text, reply_markup=markup)


bot.infinity_polling()
