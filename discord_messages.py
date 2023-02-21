import requests, time
from telebot.types import InputMediaPhoto
import multiprocessing
import config


def get_messages(token, channel_id):

    try:
    
        headers = {
            'authorization': token
        }

        r = requests.get(f'https://discord.com/api/v9/channels/{channel_id}/messages?limit=3', headers=headers)
        data = r.json()
        return data

    except:
        time.sleep(20) 
        return False

def get_new_messages(bot, token, channel_id_discord, channel_id_telegram, handler):

    prev_value = get_messages(token=token, channel_id=channel_id_discord)
    now_value = []

    while True:

        now_value = get_messages(token=token, channel_id=channel_id_discord)

        if now_value == False:
            now_value = prev_value

        if now_value != prev_value:
            
            handler(bot, now_value[0], channel_id_telegram)

        prev_value = now_value

        time.sleep(5)


def handler_message(bot, message, channel_id):
    try:

        attachments = message.get('attachments')

        message_content_filter = message['content']
        message_content_filter.replace("<@&1067836073440448543>", "")


        if attachments:
            
            media = []
            for idx, attachment in enumerate(attachments):

                link_photo = InputMediaPhoto(attachment['url'])

                if idx == 0:
                    media.append(InputMediaPhoto(attachment['url'], caption=message_content_filter))
                else:
                    media.append(link_photo)

            bot.send_media_group(channel_id, media)

        else:

            bot.send_message(channel_id, message_content_filter)

        print(f'[+] Handler and send message')


    except Exception as e:
        print(e)


def start_threads_discord(bot, channels_discord_id):

    threads_discord = []

    for channel_data in channels_discord_id:

        print('[+] Starting thread for channel: ' + str(channel_data))

        thread = multiprocessing.Process(target=get_new_messages, args=(bot, config.token_discord, int(channel_data['id_discord']), int(channel_data['id_telegram']), handler_message))
        thread.start()
        threads_discord.append(thread)

    return threads_discord


def stop_threads_discord(threads_discord):

    for channels_discord_thread in threads_discord:

        print('[+] Stopping thread')

        channels_discord_thread.terminate()
        channels_discord_thread.join()
