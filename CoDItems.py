#======================================================================
#
# CoDItems.py - Items used in game.
#
#
#======================================================================

import sys
import random

ITEM_TYPE_HEALTH_POTION		= 0x0001
ITEM_TYPE_MANA_POTION		= 0x0002

class Item(object):
	def __init__(self, seed, typ):
		self._seed = seed 
		self._type = typ

	def getType(self):
		return self._type

	def getSeed(self):
		return self._seed
	
	def effectOnHP(self):
		raise NotImplementedError

	def effectOnMP(self):
		raise NotImplementedError

class HealthPotion(Item):
	def __init__(self, seed):
		super(HealthPotion, self).__init__(seed, ITEM_TYPE_HEALTH_POTION)
		self._ehp = int(random.uniform(50, 100))

	def effectOnHP(self):
		return self._ehp

	def effectOnMP(self):
		return 0

class ManaPotion(Item):
	def __init__(self, seed):
		super(ManaPotion, self).__init__(seed, ITEM_TYPE_MANA_POTION)
		self._emp = int(random.uniform(50, 100))

	def effectOnHP(self):
		return 0

	def effectOnMP(self):
		return self._emp