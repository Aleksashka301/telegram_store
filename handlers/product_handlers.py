import requests
from io import BytesIO
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from bot_states import OrderStages


def get_product_info(update: Update, context: CallbackContext):
	url = context.bot_data.get('url')
	products = context.bot_data.get('products')

	keyboard = [
		[InlineKeyboardButton('Добавить в корзину', callback_data='add_to_card')],
		[InlineKeyboardButton('Корзина', callback_data='cart')],
		[InlineKeyboardButton('Назад', callback_data='back')]
	]
	reply_markup = InlineKeyboardMarkup(keyboard)

	query = update.callback_query
	query.answer()

	for product in products:
		select_product_id = query.data.split('_')[1]
		if int(select_product_id) == int(product['id']):
			context.user_data['selected_product_id'] = product['id']
			response = requests.get(f'{url}{product["picture"]["url"]}')
			response.raise_for_status()

			with BytesIO(response.content) as image:
				image.name = product['title']
				context.bot.send_photo(
					chat_id=update.effective_chat.id,
					photo=image,
					caption=f'{product["title"]} \n\n {float(product["price"])} руб. кг \n\n {product["description"]}',
					reply_markup=reply_markup
				)
			return OrderStages.DESCRIPTION


def get_weight(update: Update, context: CallbackContext):
	query = update.callback_query
	query.answer()

	keyboard = [
		[
			InlineKeyboardButton('200гр', callback_data='200'),
			InlineKeyboardButton('500гр', callback_data='500'),
			InlineKeyboardButton('1кг', callback_data='1000'),
		],
		[
			InlineKeyboardButton('Меню', callback_data='menu'),
		],
	]
	reply_markup = InlineKeyboardMarkup(keyboard)

	context.bot.send_message(
		chat_id=update.effective_chat.id,
		text='Укажите пожалуйста желаемый вес',
		reply_markup=reply_markup
	)
	return OrderStages.ADDITION


def add_to_card_product(update: Update, context: CallbackContext):
	url = context.bot_data.get('url')
	query = update.callback_query
	query.answer()

	keyboard = [
		[InlineKeyboardButton('Меню', callback_data='menu')],
		[InlineKeyboardButton('Корзина', callback_data='cart')],
	]
	reply_markup = InlineKeyboardMarkup(keyboard)

	products = context.bot_data.get('products')
	product_id = context.user_data.get('selected_product_id')
	weight = int(query.data)

	for product in products:
		if product['id'] == product_id:
			cost = weight / 1000 * int(product["price"])
			product_card = {
				'data': {
					'amount': weight,
					'cost': cost,
					'product': {
						'connect': [product['documentId']]
					}
				}
			}
			response = requests.post(f'{url}/api/cart-products', json=product_card)
			response.raise_for_status()
			context.user_data['cart_product'] = response.json()['data']

			context.bot.send_message(
				chat_id=update.effective_chat.id,
				text=f'товар: "{product["title"]}" \n вес: {weight} гр. \n'
				     f'стоимость: {float(cost)} руб. \n добавлен в корзину',
				reply_markup=reply_markup
			)
			add_to_cart(update, context)
			return OrderStages.ADDITION


def add_to_cart(update: Update, context: CallbackContext):
	url = context.bot_data.get('url')
	params = context.bot_data.get('url_params')

	response = requests.get(f'{url}/api/carts', params=params)
	response.raise_for_status()

	carts = response.json()['data']
	cart_product = context.user_data.get('cart_product')

	update_cart_data = {
		'data': {
			'tg_id': str(update.effective_chat.id),
			'cart_products': {
				'connect': [cart_product['documentId']],
			}
		}
	}

	for cart in carts:
		if cart['tg_id'] == str(update.effective_chat.id):
			response = requests.put(f'{url}/api/carts/{cart["documentId"]}', json=update_cart_data)
			response.raise_for_status()
			return OrderStages.ADDITION

	response = requests.post(f'{url}/api/carts', json=update_cart_data)
	response.raise_for_status()
	return OrderStages.ADDITION
