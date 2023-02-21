from discord_messages import start_threads_discord, stop_threads_discord
import config, database
import threading
import time, datetime


import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot(config.token_telegram, parse_mode="html", threaded=False)


# каналы в дискорде

channel_discord_id = database.get_data_channels()

threads_discord = []

def restart_threads():

    global threads_discord
    stop_threads_discord(threads_discord)
    channel_discord_id = database.get_data_channels()
    threads_discord = start_threads_discord(bot, channel_discord_id)


# создание клавиатуры

def gen_markup(keyboard_data={}, back_button=True, keyboard_link_data={}):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for key in keyboard_data:
        markup.add(InlineKeyboardButton(key, callback_data=keyboard_data[key]))

    for key in keyboard_link_data:
        markup.add(InlineKeyboardButton(key, url=keyboard_link_data[key]))
    
    if back_button: markup.add(InlineKeyboardButton("Назад", callback_data="start"))

    return markup

start_keyboard = lambda: gen_markup({"Подписка": "subscription", "Каналы": "channels"}, back_button=False, keyboard_link_data={'Тех. поддержка': 't.me/greentradealert'})


def get_now_date():
    return datetime.datetime.now().date()

check_user = lambda data: (data.is_subscrition == True and data.next_billing_date > get_now_date()) or data.is_trial

# админка


@bot.message_handler(commands=['get'])
def command_billing_data(message):

    if message.chat.id not in config.admins_id:
        bot.send_message(message.chat.id, f'Вы не администратор')
        return

    bot.send_message(message.chat.id, "Все чаты:\n" + database.get_text_channels())

@bot.message_handler(commands=['delete'])
def command_billing_data(message):

    if message.chat.id not in config.admins_id:
        bot.send_message(message.chat.id, f'Вы не администратор')
        return

    mesg = bot.send_message(message.chat.id, f'Отправьте id канала в дискорде который хотите удалить:\n\n'+database.get_text_channels())

    bot.register_next_step_handler(mesg, channel_delete)

def channel_delete(message):

    try:

        database.delete_data_channel(message.text)
        bot.send_message(message.chat.id, "Добавление канала произошло успешно. Перезагрузка.")
        restart_threads()

    except Exception as e:

        print(e)
        bot.send_message(message.chat.id, "Ошибка.")


@bot.message_handler(commands=['add'])
def command_billing_data(message):

    if message.chat.id not in config.admins_id:
        bot.send_message(message.chat.id, f'Вы не администратор')
        return
    
    mesg = bot.send_message(message.chat.id, f'Отправьте id канала в дискорде и в телеграме, название канала, и ссылку через пробел:')

    bot.register_next_step_handler(mesg, channel_add)

def channel_add(message):

    try:

        discord_id, telegram_id, name, link = message.text.split(' ')
        database.add_data_channel(discord_id, telegram_id, name, link)
        bot.send_message(message.chat.id, "Добавление канала произошло успешно. Перезагрузка.")
        restart_threads()

    except Exception as e:

        print(e)
        bot.send_message(message.chat.id, "Ошибка.")



@bot.message_handler(commands=['billing'])
def command_billing_data(message):

    if message.chat.id not in config.admins_id:
        bot.send_message(message.chat.id, f'Вы не администратор')
        return
    
    
    mesg = bot.send_message(message.chat.id, f'Отправьте новые реквизиты:')

    bot.register_next_step_handler(mesg, refactored_billing_data)


def refactored_billing_data(message):

    with open('bill_data.txt', 'w') as f:
        f.write(message.text)
    
    bot.send_message(message.chat.id, f'Реквизиты обновлены.')



# пользовательская часть

@bot.message_handler(commands=['start'])
def command_start(message):
    database.add_user(message.chat.first_name, message.chat.id)
    
    bot.send_message(message.chat.id, config.start_text, reply_markup=start_keyboard())


def edit_call_message(call, text, reply_markup=gen_markup()):
    bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.id, text=text, reply_markup=reply_markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    if call.data == "start":
        edit_call_message(call, text=config.start_text, reply_markup=start_keyboard())

    elif call.data == "channels":
        edit_call_message(call, text="Все доступные каналы:\n" + database.get_text_channels(1), reply_markup=gen_markup({}))

    elif call.data == "subscription":

        user_info = database.get_current_user(call.from_user.id)

        if user_info.is_subscrition == True and user_info.next_billing_date > get_now_date():
            edit_call_message(call, text=f"У тебя активирована платная подписка, которая заканчивается: {user_info.next_billing_date}.", reply_markup=gen_markup({"Продлить подписку": "choice_buy_ext"}))
        elif user_info.is_trial:
            edit_call_message(call, text=f"У тебя активирован пробный период, который заканчивается: {user_info.next_billing_date}.", reply_markup=gen_markup({"Купить подписку": "choice_buy"}))
        else:
            edit_call_message(call, text=f"На данный момент у тебя нет подписки, ее можно купить.", reply_markup=gen_markup({"Купить подписку": "choice_buy"}))

    elif "choice_buy" in call.data:

        choice_keyboard = {
            "1 неделя": "buy_7",
            "1 месяц": "buy_30",
            "3 месяца": "buy_90",
            "6 месяцев": "buy_180",
            "1 год": "buy_365",
        }
                
        edit_call_message(call, text=f"Выберите тариф подписки:", reply_markup=gen_markup(choice_keyboard))


    elif "buy_" in call.data:

        time_subc = call.data.split("_")[1]
        user_info = database.get_current_user(call.from_user.id)
  
        with open('bill_data.txt', 'r') as f:
            edit_call_message(
                call, 
                text=f"Оплатите подписку.\nСтоимость подписки на {time_subc} дней - {config.prices[int(time_subc)]}р.: реквизиты:\n\n{f.read()}", reply_markup=gen_markup({"Оплатил": f"buyed_{time_subc}"})
            )

    elif "buyed_" in call.data:

        time_subc = call.data.split("_")[1]

        bot.send_message(call.from_user.id, config.buy_text)

        for admin_id in config.admins_id:

            bot.send_message(admin_id, f"Пользователь t.me/{call.from_user.username}, ID: {call.from_user.id} вроде оплатил подписку!", reply_markup=gen_markup({"Подтвердить": f"confirm_{call.from_user.id}_{time_subc}"}))



    elif "confirm" in call.data:

        if call.from_user.id not in config.admins_id:
            bot.send_message(call.from_user.id, f'Вы не администратор')
            return

        _, id_user, time_subc, = call.data.split('_')
        next_billing = database.add_subc_user(int(id_user), int(time_subc))

        bot.send_message(int(id_user), f'Оплата принята.\nВаша подписка действует до {next_billing}')
        edit_call_message(call, text=f"Готово! Участник был одобрен!")


def ban_member_channels(user_id):
    for channel in database.get_data_channels():
        try:

            bot.kick_chat_member(
                chat_id=channel['id_telegram'], 
                user_id=user_id,
            )
        except:
            pass

def unban_member_channels(user_id):
    for channel in database.get_data_channels():
        try:

            bot.unban_chat_member(
                chat_id=channel['id_telegram'], 
                user_id=user_id,
            )
        except:
            pass


@bot.chat_join_request_handler()
def handle_join_request(message):

    from_user_id = message.from_user.id

    user = database.get_current_user(from_user_id)

    if check_user(user):
        print(f'approve user {user.profile_id}')

        unban_member_channels(message.from_user.id)

        bot.approve_chat_join_request(message.chat.id, message.from_user.id)
    else:

        ban_member_channels(message.from_user.id)


        bot.decline_chat_join_request(message.chat.id, message.from_user.id)

        print(f'decline user {user.profile_id}')

        bot.send_message(message.from_user.id, 'У тебя нет подписки для вступления в канал!')
        

# запуск всех потоков

start_bot = lambda: bot.polling(none_stop=True)
bot_thread = threading.Thread(target=start_bot)



def start_auto_user_delete():
    while True:
        
        all_users = database.get_all_users()

        for user in all_users:
            
            if check_user(user):
                unban_member_channels(int(user.profile_id))
            else:
                ban_member_channels(int(user.profile_id))
                
        
        time.sleep(86400)




start_auto_user_delete_thread = threading.Thread(target=start_auto_user_delete)

threads_discord = start_threads_discord(bot, channel_discord_id)

start_auto_user_delete_thread.start()
bot_thread.start()