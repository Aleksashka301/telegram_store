import requests
from enum import Enum
from environs import Env
from io import BytesIO
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler, Filters, \
	MessageHandler, Updater
from pprint import pprint


def start(update: Update, context: CallbackContext):
	products = context.bot_data.get('products')

	keyboard = [
		[InlineKeyboardButton(product['title'], callback_data=product['id'])]
		for product in products
	]
	keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
	reply_markup = InlineKeyboardMarkup(keyboard)

	context.bot.send_message(
		chat_id=update.effective_chat.id,
		text='Пожалуйста, выберите товар',
		reply_markup=reply_markup
	)

	return OrderStages.MENU


def get_product_info(update: Update, context: CallbackContext):
	products = context.bot_data.get('products')
	keyboard = [
		[InlineKeyboardButton('Добавить в корзину', callback_data='add_to_card')],
		[InlineKeyboardButton('Корзина', callback_data='cart')],
		[InlineKeyboardButton('Назад', callback_data='back')]
	]
	reply_markup = InlineKeyboardMarkup(keyboard)

	query = update.callback_query
	query.answer()

	if query.data == 'add_to_card':
		return get_weight(update, context)

	if query.data == 'cart':
		show_cart(update, context)
		return OrderStages.CART

	if query.data == 'back':
		start(update, context)
		return OrderStages.MENU

	for product in products:
		if int(query.data) == int(product['id']):
			context.user_data['selected_product_id'] = product['id']
			url = f'http://localhost:1337{product["picture"]["url"]}'
			response = requests.get(url)
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

	if query.data == 'menu':
		start(update, context)
		return OrderStages.MENU

	context.bot.send_message(
		chat_id=update.effective_chat.id,
		text='Укажите пожалуйста желаемый вес',
		reply_markup=reply_markup
	)

	return OrderStages.ADDITION


def add_to_card_product(update: Update, context: CallbackContext):
	query = update.callback_query
	query.answer()

	keyboard = [
		[InlineKeyboardButton('Меню', callback_data='menu')],
		[InlineKeyboardButton('Корзина', callback_data='cart')],
	]
	reply_markup = InlineKeyboardMarkup(keyboard)

	if query.data == 'menu':
		start(update, context)
		return OrderStages.MENU

	products = context.bot_data.get('products')
	product_id = context.user_data.get('selected_product_id')
	weight = int(query.data)

	for product in products:
		if product['id'] == product_id:
			cost = weight / 1000 * int(product["price"])
			data = {
				'data': {
					'amount': weight,
					'cost': cost,
					'product': {
						'connect': [product['documentId']]
					}
				}
			}
			response = requests.post('http://localhost:1337/api/cart-products', json=data)
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
	response = requests.get('http://localhost:1337/api/carts?populate=*')
	response.raise_for_status()
	cart_product = context.user_data.get('cart_product')

	carts = response.json()['data']
	data = {
		'data': {
			'tg_id': str(update.effective_chat.id),
			'cart_products': {
				'connect': [cart_product['documentId']],
			}
		}
	}

	for cart in carts:
		if cart['tg_id'] == str(update.effective_chat.id):
			requests.put(f'http://localhost:1337/api/carts/{cart["documentId"]}', json=data)
			return OrderStages.ADDITION

	requests.post('http://localhost:1337/api/carts', json=data)
	return OrderStages.ADDITION


def get_cart(tg_id):
	response = requests.get('http://localhost:1337/api/carts?populate=*')
	response.raise_for_status()
	carts = response.json()['data']
	user_cart = None
	keyboard = []

	for cart in carts:
		if cart['tg_id'] == tg_id:
			user_cart = cart
			break

	if user_cart and user_cart['cart_products']:
		response = requests.get('http://localhost:1337/api/cart-products?populate=*')
		response.raise_for_status()
		cart_products = response.json()['data']
		orders = ''
		cost = 0

		for product in cart_products:
			if product['cart']['tg_id'] == user_cart['tg_id']:
				orders += (f'{product["product"]["title"]} \n {float(product["product"]["price"])} руб. кг. \n'
				         f'{product["amount"]} гр {float(product["cost"])} руб. \n\n')
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
	tg_id = str(update.effective_chat.id)
	orders, reply_markup = get_cart(tg_id)

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
			text='Корзина пуста, вы можете добавить туда товары из меню',
			reply_markup=reply_markup
		)
		return OrderStages.CART


def remove_product_cart(update: Update, context: CallbackContext):
	query = update.callback_query
	query.answer()

	product_document_id = query.data.split('_')[1]
	requests.delete(f'http://localhost:1337/api/cart-products/{product_document_id}')
	tg_id = str(update.effective_chat.id)
	orders, reply_markup = get_cart(tg_id)

	context.bot.send_message(
		chat_id=update.effective_chat.id,
		text=orders,
		reply_markup=reply_markup,
	)
	return OrderStages.CART


def start_payment(update: Update, context: CallbackContext):
	context.bot.send_message(
		chat_id=update.effective_chat.id,
		text='Представьтесь пожалуйста!'
	)

	return OrderStages.WAITING_NAME


def get_name(update: Update, context: CallbackContext):
	context.user_data['user_name'] = update.message.text
	context.bot.send_message(
		chat_id=update.effective_chat.id,
		text='Укажите ваш email'
	)

	return OrderStages.WAITING_EMAIL


def receive_email(update: Update, context: CallbackContext):
	response = requests.get('http://localhost:1337/api/carts?populate=*')
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

			requests.post('http://localhost:1337/api/buyers', json=data)
			update.message.reply_text(f'{user_name} Ваш заказ оформлен!')

			return OrderStages.BUYER


if __name__ == '__main__':
	env = Env()
	env.read_env()

	telegram_token = env.str('TELEGRAM_TOKEN')
	url = 'http://localhost:1337/api/products?populate=*'

	response = requests.get(url)
	response.raise_for_status()

	updater = Updater(token=telegram_token, use_context=True)
	dispatcher = updater.dispatcher
	dispatcher.bot_data['products'] = response.json()['data']

	class OrderStages(Enum):
		MENU = 1
		DESCRIPTION = 2
		GET_WEIGHT = 3
		ADDITION = 4
		CART = 5
		WAITING_NAME = 6
		WAITING_EMAIL = 7
		BUYER = 8


	conv_handler = ConversationHandler(
		entry_points=[
			CommandHandler('start', start)
		],
		states={
			OrderStages.MENU: [
				CallbackQueryHandler(get_product_info),
			],
			OrderStages.DESCRIPTION: [
				CallbackQueryHandler(get_product_info),
			],
			OrderStages.GET_WEIGHT: [
				CallbackQueryHandler(get_weight),
			],
			OrderStages.ADDITION: [
				CallbackQueryHandler(add_to_card_product),
			],
			OrderStages.CART: [
				CallbackQueryHandler(remove_product_cart, pattern='^remove_'),
				CallbackQueryHandler(start_payment, pattern='^payment'),
			],
			OrderStages.WAITING_NAME: [
				MessageHandler(Filters.text & ~Filters.command, get_name),
			],
			OrderStages.WAITING_EMAIL: [
				MessageHandler(Filters.text & ~Filters.command, receive_email),
			],
			OrderStages.BUYER: [
				CallbackQueryHandler(receive_email),
			],
		},
		fallbacks=[]
	)

	dispatcher.add_handler(conv_handler)

	# pprint(response.json()['data'][0])

	updater.start_polling()
	updater.idle()
