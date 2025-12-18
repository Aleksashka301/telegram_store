from enum import Enum


class OrderStages(Enum):
	MENU = 1
	DESCRIPTION = 2
	ADDITION = 3
	CART = 4
	WAITING_NAME = 5
	WAITING_EMAIL = 6
	BUYER = 7
