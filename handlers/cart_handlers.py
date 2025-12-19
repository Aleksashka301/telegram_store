import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from bot_states import OrderStages


def get_cart(tg_id, url, populate, include):
	response = requests.get(f'{url}/api/carts', params={populate: include})
	response.raise_for_status()
	carts = response.json()['data']

	user_cart = None
	keyboard = []

	for cart in carts:
		if cart['tg_id'] == tg_id:
			user_cart = cart
			break

	if user_cart and user_cart['cart_products']:
		response = requests.get(f'{url}/api/cart-products', params={populate: include})
		response.raise_for_status()
		cart_products = response.json()['data']

		orders = ''
		cost = 0

		for product in cart_products:
			if product['cart']['tg_id'] == user_cart['tg_id']:
				orders += (
					f'{product["product"]["title"]} \n {float(product["product"]["price"])} руб. кг. \n'
				    f'{product["amount"]} гр {float(product["cost"])} руб. \n\n'
				)
				cost += product["cost"]

				keyboard.append(
					[InlineKeyboardButton(
						f'Убрать из корзины "{product["product"]["title"]}"',
						callback_data=f'remove_{product["documentId"]}'
					)]
				)

		orders += f'Итого: {float(cost)} руб.'
		keyboard.append([InlineKeyboardButton('Меню', callback_data='menu')])
		keyboard.append([InlineKeyboardButton('Оплатить', callback_data='payment')])
		reply_markup = InlineKeyboardMarkup(keyboard)
		return orders, reply_markup

	else:
		keyboard.append([InlineKeyboardButton('Меню', callback_data='menu')])
		reply_markup = InlineKeyboardMarkup(keyboard)
		return None, reply_markup


def show_cart(update: Update, context: CallbackContext):
	url = context.bot_data.get('url')
	params = context.bot_data.get('url_params')

	for key, value in params.items():
		populate = key
		include = value

	tg_id = str(update.effective_chat.id)
	orders, reply_markup = get_cart(tg_id, url, populate, include)

	if orders:
		query = update.callback_query
		query.answer()

		context.bot.send_message(
			chat_id=update.effective_chat.id,
			text=orders,
			reply_markup=reply_markup,
		)
		return OrderStages.CART
	else:
		context.bot.send_message(
			chat_id=update.effective_chat.id,
			text='Корзина пуста, вы можете добавить туда продукты из меню',
			reply_markup=reply_markup
		)
		return OrderStages.CART


def remove_product_cart(update: Update, context: CallbackContext):
	url = context.bot_data.get('url')
	params = context.bot_data.get('url_params')

	for key, value in params.items():
		populate = key
		include = value

	query = update.callback_query
	query.answer()

	product_document_id = query.data.split('_')[1]
	response = requests.delete(f'{url}/api/cart-products/{product_document_id}')
	response.raise_for_status()

	tg_id = str(update.effective_chat.id)
	orders, reply_markup = get_cart(tg_id, url, populate, include)

	context.bot.send_message(
		chat_id=update.effective_chat.id,
		text=orders,
		reply_markup=reply_markup,
	)
	return OrderStages.CART
