from configparser import ConfigParser

# CONFIG INFO #
cfg = ConfigParser()
cfg.read('config.ini')

bot_token = cfg.get('Bot', 'token')
bot_prefix = cfg.get('Bot', 'command_prefix')
bot_message = cfg.get('Bot', 'status_message')
server_id = cfg.get('Bot', 'server_id')
app_id = cfg.get('Bot', 'app_id')