from telebot.types import InputMediaPhoto

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









