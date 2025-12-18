from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from bot_states import OrderStages


def start(update: Update, context: CallbackContext):
	products = context.bot_data.get('products')
	keyboard = [
		[InlineKeyboardButton(product['title'], callback_data=f'product_{product["id"]}')]
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
