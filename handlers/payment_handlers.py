import requests
from telegram import Update
from telegram.ext import CallbackContext
from bot_states import OrderStages


def start_payment(update: Update, context: CallbackContext):
	context.bot.send_message(
		chat_id=update.effective_chat.id,
		text='Представьтесь пожалуйста!'
	)
	return OrderStages.WAITING_NAME


def get_buyers_details(update: Update, context: CallbackContext):
	context.user_data['user_name'] = update.message.text
	context.bot.send_message(
		chat_id=update.effective_chat.id,
		text='Укажите ваш email'
	)
	return OrderStages.WAITING_EMAIL


def end_payment(update: Update, context: CallbackContext):
	url = context.bot_data.get('url')
	params = context.bot_data.get('url_params')

	response = requests.get(f'{url}/api/carts', params=params)
	response.raise_for_status()
	carts = response.json()['data']

	user_name = context.user_data.get('user_name')
	user_mail = update.message.text

	if '@' not in user_mail or '.' not in user_mail.split('@')[-1]:
		update.message.reply_text('В email ошибка, попробуйте ещё раз.')
		return OrderStages.WAITING_EMAIL

	for cart in carts:
		if cart['tg_id'] == str(update.effective_chat.id):
			data = {
				'data': {
					'name': user_name,
					'email': user_mail,
					'carts': {
						'connect': [cart['documentId']]
					}
				}
			}

			response = requests.post(f'{url}/api/buyers', json=data)
			response.raise_for_status()

			update.message.reply_text(f'{user_name}, Ваш заказ оформлен!')
			return OrderStages.BUYER
