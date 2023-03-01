token = "NjQzMTI0NjA1NjA2NjkwODM5.GM1wuE.LZOrS0YOe45ty3PN5H3qM7nGivy0CVHbXWLgX4"

import discum     
bot = discum.Client(token=token, log=False)

bot.sendMessage("1073665209849352205", "Hello :)")

@bot.gateway.command
def helloworld(resp):
    if resp.event.ready_supplemental: #ready_supplemental is sent after ready
        user = bot.gateway.session.user
        print("Logged in as {}#{}".format(user['username'], user['discriminator']))
    if resp.event.message:
        m = resp.parsed.auto()
        print(m)
        channelID = m['channel_id']
        content = m['content']

bot.gateway.run(auto_reconnect=True)