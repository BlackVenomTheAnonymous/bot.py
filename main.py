import re
import json
import requests
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

telegram_token = '6212081716:AAHcAQgIcOtW90TLyXhhuhKndAcGlBj-fQw'


def get_json_response(data):
    checkout = data
    if checkout:
        url_match = re.search(r'https?://checkout.stripe.com/c/pay/(.+?)#', checkout)
        if not url_match:
            return "❌ Invalid Link: The provided URL is not valid."

        cs = url_match.group(1)
        url = f"https://checkout.stripe.com/c/pay/{cs}"

        pk_list = re.findall(r'"apiKey":"(.+?)"', decode_xor_string(url, 5))
        if not pk_list:
            return "❌ Invalid Link: Unable to retrieve the API key."

        pk = pk_list[0]
        site = re.findall(r'"referrerOrigin":"(.+?)"', decode_xor_string(url, 5))[0]

        headers = {
            'sec-ch-ua': '"Not:A-Brand";v="99", "Chromium";v="112"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 12; M1901F7S) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }

        payload = {
            'key': pk,
            'eid': 'NA',
            'browser_locale': 'en-US',
            'redirect_type': 'stripe_js'
        }

        response = requests.post(f'https://api.stripe.com/v1/payment_pages/{cs}/init', headers=headers, auth=(pk, ''), data=payload)
        fim = response.text

        if 'No such payment_page' in fim:
            return "❌ Expired Link: The payment page associated with the link no longer exists."
        else:
            name = re.findall(r'"display_name": "(.+?)"', fim)
            email = re.findall(r'"customer_email": "(.+?)"', fim)
            cur = re.findall(r'"currency": "(.+?)"', fim)
            amt = re.findall(r'"amount": (\d+),', fim)
            if not amt:
                amt = re.findall(r'"total": (\d+),', fim)
            if not amt:
                amt = ['____']
            name = name[0] if name else '____'
            pk = pk if pk else '____'
            site = site if site else '____'
            cs = cs if cs else '____'
            cur = cur[0] if cur else '____'
            email = email[0] if email else '❗️ Email not found'

            data = {
                'name': name,
                'pklive': pk,
                'cslive': cs,
                'amount': amt[0],
                'email': email
            }

            return json.dumps(data)

    return None


def decode_xor_string(text, key):
    key = [key] if isinstance(key, int) else key
    output = ''
    for i, c in enumerate(text):
        output += chr(ord(c) ^ key[i % len(key)])
    return output


def grab(update, context):
    chat_id = update.message.chat_id
    message_text = update.message.text

    if message_text.startswith('/grab'):
        checkout_link = message_text[6:]

        print("Received checkout link:", checkout_link)  # Add this line

        json_response = get_json_response(checkout_link)

        if json_response:
            data = json.loads(json_response)

            response_message = "𝗦𝗶𝘁𝗲: {}\n\n".format(data['name'])
            response_message += "𝗣𝗞: {}\n".format(data['pklive'])
            response_message += "𝗖𝗦: {}\n".format(data['cslive'])
            response_message += "𝗘𝗺𝗮𝗶𝗹: {}\n".format(data['email'])
            response_message += "𝗔𝗺𝗼𝘂𝗻𝘁: {}\n".format(data['amount'])
            response_message += "𝗖𝘂𝗿𝗿𝗲𝗻𝗰𝘆: {}\n\n".format(data['currency'])
            response_message += "𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗯𝘆 @GodFatherAlive"

            context.bot.send_message(
                chat_id=chat_id,
                text=response_message,
                parse_mode='HTML'
            )
        else:
            context.bot.send_message(
                chat_id=chat_id,
                text='❌ Invalid Link'
            )


def start(update, context):
    chat_id = update.message.chat_id
    welcome_message = "Welcome to the Checkout Bot!\n\n"
    welcome_message += "To use this bot, send a checkout link using the /grab command.\n\n"
    welcome_message += "Example: /grab https://checkout.example.com/abcd1234\n\n"
    welcome_message += "The bot will fetch the checkout information and provide you with the details.\n\n"
    welcome_message += "Note: This bot currently supports Stripe payment pages."

    context.bot.send_message(
        chat_id=chat_id,
        text=welcome_message,
        parse_mode='HTML'
    )


def main():
    bot = Bot(token=telegram_token)
    updater = Updater(bot=bot)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('grab', grab))

    updater.start_polling()
    updater.idle()
