# CryptoTrackerBot - check cryptocurrencies prices on telegram
# Copyright (C) 2018  Dario 91DarioDev <dariomsn@hotmail.it> <github.com/91dariodev>
#
# CryptoTrackerBot is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CryptoTrackerBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with CryptoTrackerBot.  If not, see <http://www.gnu.org/licenses/>.

from telegram.ext.dispatcher import run_async
from configparser import SafeConfigParser
import datetime
import time
from matplotlib.dates import date2num
from cryptotrackerbot import cryptoapi
from cryptotrackerbot import utils
from cryptotrackerbot import emoji
import matplotlib
matplotlib.use('TKAgg')


@run_async
def evmos_command(bot, update, args ,job_queue ):
    print(args)
    response = cryptoapi.get_evmos()
    # print(response)
    # if 'Response' in response and response['Response'] == 'Error':  # return if response from api is error
    #     text = "<b>Error!</b>"
    #     text += "\n{}".format(response['Message']) if 'Message' in response else ''
    #     utils.send_autodestruction_message(bot, update, job_queue, text)
    #     return
#    text=str(response)
    text = ""
    coin = "EVMOS"
    text += "<b>— {}:</b>".format(coin)
    prices = response[coin]
    for fiat in prices:
        emoji_coin = emoji.USD if fiat.upper() == 'USD' else emoji.CNY if fiat.upper(
        ) == 'CNY' else emoji.NT if fiat.upper() == 'NT' else ""
        text += "\n  - {}{}: {}".format(emoji_coin,
                                        fiat, utils.sep(prices[fiat]))
    text += "\n\n"
    if args == None:
        limit = 480
    else:
        limit = args

    send_evmosgraph(bot, update, job_queue, limit)
    
    utils.send_autodestruction_message(
        bot, update, job_queue, text)


@run_async
def price_command(bot, update, args, job_queue):

    if "cosmos" in args or "COSMOS" in args:  # return if no args added
        args += ["atom", "evmos", "osmo", "scrt",
                 "juno", "kava", "inj", "huahua", "dvpn"]
    if "evm" in args or "EVM" in args:  # return if no args added
        args += ["eth", "evmos", "avax", "near", "ftm", "kava", "inj", "tlos"]
    args = list(set(args))

    if "EVMOS" in args or "evmos" in args:  # return if no args added
        text = "溫馨提示：查詢evmos價格可直接 使用 /e \n"
    else:
        text = ""
    response = cryptoapi.get_price(args)
    # print(response)
    # return if response from api is error
    if 'Response' in response and response['Response'] == 'Error':
        text = "<b>Error!</b>"
        text += "\n{}".format(response['Message']
                              ) if 'Message' in response else ''
        utils.send_autodestruction_message(bot, update, job_queue, text)
        return

    for coin in response:
        text += "<b>— {}:</b>".format(coin)
        prices = response[coin]
        for fiat in prices:
            emoji_coin = emoji.CNY if fiat.upper() == 'CNY' else emoji.USD if fiat.upper(
            ) == 'USD' else emoji.EUR if fiat.upper() == 'EUR' else ""
            text += "\n  - {}{}: {}".format(emoji_coin,
                                            fiat, utils.sep(prices[fiat]))
        text += "\n\n"
    utils.send_autodestruction_message(bot, update, job_queue, text)


@run_async
def help(bot, update, job_queue):
    text = (
        "<b>SUPPORTED COMMANDS:</b>\n"
        "/price - <i>return price of crypto</i>\n"
        "/help - <i>return help message</i>\n"
        "/rank - <i>return coins rank</i>\n"
        "/graph - <i>return coins graph</i>\n"
        "\n"
        "Note: If this bot is added in groups as admin, in order to keep the chat clean of spam, after few seconds it deletes both "
        "the command issued by the user and the message sent by the bot."
        "\n"
        "This bot is <a href=\"https://github.com/91DarioDev/CryptoTrackerBot\">released under the terms of AGPL 3.0 LICENSE</a>."
    )
    utils.send_autodestruction_message(
        bot, update, job_queue, text, destruct_in=120, disable_web_page_preview=True)


@run_async
def rank_command(bot, update, job_queue):
    text = ""
    response = cryptoapi.get_rank()
    for coin in response:
        text += "<b>{}){}:</b>".format(coin['rank'], coin['symbol'])
        text += " {}".format("+" if utils.string_to_number(
            coin["percent_change_24h"]) > 0 else "")
        text += "{}%{}".format(coin["percent_change_24h"], utils.arrow_up_or_down(
            utils.string_to_number(coin["percent_change_24h"])))
        text += " {}{}".format(
            utils.sep(round(utils.string_to_number(coin['price_usd']), 2)), emoji.USD)
        text += "\n"
    utils.send_autodestruction_message(
        bot, update, job_queue, text, destruct_in=120)


@run_async
def graph_command(bot, update, job_queue, args):
    if len(args) != 1:
        text = "Error: You have to append to the command as parameters the code of only one crypto you want\n\nExample:<code>/graph btc</code>"
        utils.send_autodestruction_message(bot, update, job_queue, text)
        return
    coin = args[0]
    intervals = ['1d', '1w']  # , 'day']
    for interval in intervals:
        send_graph(bot, update, job_queue, coin, interval)


def send_graph(bot, update, job_queue, coin, interval):
    if interval == '1d':
        limit = 600
        interval_string = 'minute'
        aggregate = 10
    elif interval == '1w':
        limit = 600
        interval_string = 'hour'
        aggregate = 1
    response = cryptoapi.get_history(
        coin, aggregate=aggregate, limit=limit, interval=interval_string)
    # return if response from api is error
    if 'Response' in response and response['Response'] == 'Error':
        text = "<b>Error!</b>"
        text += "\n{}".format(response['Message']
                              ) if 'Message' in response else ''
        utils.send_autodestruction_message(bot, update, job_queue, text)
        return
    # so user knows the bot is running
    utils.send_sending_photo_alert(bot, update)
    data = response['Data']
    cut_data = []
    for i in data:
        # stats blocked 1 day
        if interval == '1d' and i['time'] < (time.time() - 60*60*24):
            continue
        # stats blocked 1w
        if interval == '1w' and i['time'] < (time.time() - 60*60*24*7):
            continue
        cut_data.append(i)
    caption = "{} - USD. INTERVAL: {}".format(
        coin.upper(),
        "1 day" if interval == '1d' else "1 week" if interval == '1w' else ''
    )
    pic = utils.build_graph(cut_data, title=caption)
    utils.send_autodestruction_photo(
        bot, update, pic, caption, job_queue, destruct_in=600, quote=False)


def send_evmosgraph(bot, update, job_queue, limit):
    # if interval == '1d':
    #     limit = 600
    #     interval_string = 'minute'
    #     aggregate = 10
    # elif interval == '1w':
    #     limit = 600
    #     interval_string = 'hour'
    #     aggregate = 1
    response = cryptoapi.get_evmosgraph(limit)
    # return if response from api is error
    if 'Response' in response and response['Response'] == 'Error':
        text = "<b>Error!</b>"
        text += "\n{}".format(response['Message']
                              ) if 'Message' in response else ''
        utils.send_autodestruction_message(bot, update, job_queue, text)
        return
    # so user knows the bot is running
    # utils.send_sending_photo_alert(bot, update)
    data = response['Data']["Data"]
    # cut_data = []
    # for i in data:
    #     # stats blocked 1 day
    #     cut_data.append(i)
    caption = "{} - USD. interval: {}".format(
        "EVMOS", "{} hours".format(str(limit)))
    pic = utils.build_graph(data, title=caption)
    utils.send_autodestruction_photo(
        bot, update, pic, caption, job_queue, destruct_in=600, quote=False)
