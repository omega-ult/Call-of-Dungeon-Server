#======================================================================
#
# CoDPlayer.py - a player entity used in game.
#
#
#======================================================================

import sys


"""
Player entity, pid is the same as the key in database
hid is the net handle.
"""
class Player(object):
	def __init__(self, pid, hid):
		self._playerID = pid
		self._hid = hid
		self._commandMap = {}

	def getPlayerID(self):
		return self._playerID

	def getPlayerNetHandle(self):
		return self._hid

	

