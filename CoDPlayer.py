#======================================================================
#
# CoDPlayer.py - a player entity used in game.
#
#
#======================================================================

import sys

PLAYER_TYPE_LIDDELL	= 0x0000

PLAYER_STATE_ALIVE		= 0x0100
PLAYER_STATE_DEAD		= 0x0101

PLAYER_FACE_UP			= 0x1001
PLAYER_FACE_DOWN		= 0x1002
PLAYER_FACE_LEFT		= 0x1003
PLAYER_FACE_RIGHT		= 0x1004

PLAYER_ACTION_MOVE		= 0x1050
PLAYER_ACTION_ATTACK	= 0x1051
PLAYER_ACTION_DIE		= 0x1fff


"""
Player entity, pid is the same as the key in database
hid is the net handle.
"""
class Player(object):
	def __init__(self, pid, hid, account):
		self._playerID = pid
		self._hid = hid
		self._type = PLAYER_TYPE_LIDDELL

		self._state = PLAYER_STATE_ALIVE
		self._account = account
		self._speed = 0
		self._posX = 0
		self._posY = 0

		self._action = PLAYER_ACTION_MOVE
		self._actorData = {}

		self._hp = 0
		self._mp = 0
		self._atk = 0

		self._items = []

	def getPlayerID(self):
		return self._playerID

	def getPlayerNetHandle(self):
		return self._hid

	def enterGameAs(self, data):
		self._actorData = data
		self._posX = data['Position'][0]
		self._posY = data['Position'][1]
		self._hp = data['HP']
		self._mp = data['MP']
		self._atk = data['Atk']

	def leaveGame(self):
		self._actorData = {}

	def isLeaved(self):
		return self._actorData == {}

	"""
	those functions are available when player entered game.
	"""
	def getPlayerType(self):
		return self._type

	def getPlayerState(self):
		return self._state

	def setPlayerState(self, state):
		self._state = state

	def getPlayerAction(self):
		return self._action
	
	def setPlayerPosition(self, x, y):
		self._posX = x
		self._posY = y

	def getPlayerPosition(self):
		return self._posX, self._posY

	def getPlayerName(self):
		pass

	def getActorData(self):
		ret = self._actorData
		ret['Position'][0] = self._posX
		ret['Position'][1] = self._posY
		ret['State'] = self._state
		return ret

	def setPlayerHP(self, hp):
		self._hp = hp

	def getPlayerHP(self):
		return self._hp

	def setPlayerMP(self, mp):
		self._mp = mp

	def getPlayerMP(self):
		return self._mp

	def getPlayerATK(self):
		return self._atk


	def appendItem(self, item):
		self._items.append(item)

	def getItem(self, seed):
		for i in self._items:
			if i.getSeed() == seed:
				return i
		return None

	def removeItem(self, seed):
		for i in self._items:
			if i.getSeed() == seed:
				self._items.remove(i)

