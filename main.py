import requests
from environs import Env
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler, Filters, MessageHandler, Updater

from config import OrderStages
from handlers.cart_handlers import remove_product_cart, show_cart
from handlers.payment_handlers import start_payment, get_buyers_details, end_payment
from handlers.product_handlers import get_product_info, get_weight, add_to_card_product
from handlers.start_handlers import start


if __name__ == '__main__':
	env = Env()
	env.read_env()
	telegram_token = env.str('TELEGRAM_TOKEN')

	response = requests.get('http://localhost:1337/api/products?populate=*')
	response.raise_for_status()

	updater = Updater(token=telegram_token, use_context=True)
	dispatcher = updater.dispatcher
	dispatcher.bot_data['products'] = response.json()['data']

	conv_handler = ConversationHandler(
		entry_points=[
			CommandHandler('start', start)
		],
		states={
			OrderStages.MENU: [
				CallbackQueryHandler(get_product_info, pattern='^product_'),
				CallbackQueryHandler(show_cart, pattern='^cart'),
			],
			OrderStages.DESCRIPTION: [
				CallbackQueryHandler(get_weight, pattern='^add_to_card'),
				CallbackQueryHandler(show_cart, pattern='^cart'),
				CallbackQueryHandler(start, pattern='^back'),
			],
			OrderStages.ADDITION: [
				CallbackQueryHandler(add_to_card_product, pattern='^(200|500|1000)$'),
				CallbackQueryHandler(start, pattern='^menu'),
				CallbackQueryHandler(show_cart, pattern='^cart'),
			],
			OrderStages.CART: [
				CallbackQueryHandler(remove_product_cart, pattern='^remove_'),
				CallbackQueryHandler(start_payment, pattern='^payment'),
				CallbackQueryHandler(start, pattern='^menu')
			],
			OrderStages.WAITING_NAME: [
				MessageHandler(Filters.text & ~Filters.command, get_buyers_details),
			],
			OrderStages.WAITING_EMAIL: [
				MessageHandler(Filters.text & ~Filters.command, end_payment),
			],
			OrderStages.BUYER: [
				CallbackQueryHandler(end_payment),
			],
		},
		fallbacks=[]
	)
	dispatcher.add_handler(conv_handler)

	updater.start_polling()
	updater.idle()
