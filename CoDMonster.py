#======================================================================
#
# CoDMonster.py - a monster entity used in game.
#
#
#======================================================================

import sys
import CoDTaskManager

MONSTER_TYPE_UNKNOWN	= 0xffff
MONSTER_TYPE_A			= 0x0001
MONSTER_TYPE_B			= 0x0002

MONSTER_FACE_UP			= 0x1001
MONSTER_FACE_DOWN		= 0x1002
MONSTER_FACE_LEFT		= 0x1003
MONSTER_FACE_RIGHT		= 0x1004

MONSTER_ACTION_MOVE		= 0x1050
MONSTER_ACTION_ATTACK	= 0x1051
MONSTER_ACTION_DIE		= 0x10ff

class Monster(object):
	def __init__(self, seed, typ):
		self._seed = seed
		self._type = typ
		self._HP = 0
		self._posX = 0
		self._posY = 0

		self._target = None

		self._state = MONSTER_ACTION_MOVE

		self._chaseDelayTime = 10
		self._chaseDelay = None
		self._canMove = True
		self._moveDelayTime = 1
		self._moveDelay = None

		self._canAttack = True
		self._attackDelayTime = 2
		self._attackDelay = None

	def getSeed(self):
		return self._seed

	def getType(self):
		return self._type

	def setState(self, state):
		self._state = state

	def getState(self):
		return self._state

	def isAggressive(self):
		raise NotImplementedError
		
	def setAttackable(self, flag):
		self._canAttack = flag

	def attack(self):
		if self._canAttack:
			self._canAttack = False
			CoDTaskManager.TaskManager.cancel(self._attackDelay)
			self._attackDelay = CoDTaskManager.TaskManager.addDelayTask(self._attackDelayTime, self.setAttackable, True)
			return self.getAttck()
		return None

	def getAttck(self):
		raise NotImplementedError

	def setMovable(self, flag):
		self._canMove = flag

	def canMove(self):
		return self._canMove

	def setHP(self, hp):
		self._HP = hp

	def getHP(self):
		return self._HP

	def getPosition(self):
		return self._posX, self._posY

	def setPosition(self, x, y):
		self._posX = x
		self._posY = y
		self._canMove = False
		CoDTaskManager.TaskManager.cancel(self._moveDelay)
		self._moveDelay = CoDTaskManager.TaskManager.addDelayTask(self._moveDelayTime, self.setMovable, True)

	def resetTarget(self):
		self._target = None

	def setTargetPlayer(self, targetID):
		self._target = targetID
		if self._target != None:
			CoDTaskManager.TaskManager.cancel(self._chaseDelay)
			self._chaseDelay = CoDTaskManager.TaskManager.addDelayTask(self._chaseDelayTime, self.resetTarget)

	def getTargetPlayer(self):
		return self._target


	# if the distance between player and monster less than this
	# value, the monster will be activated and begin to chase player.
	def getCordonRadius(self):
		raise NotImplementedError

	def shutdown(self):
		CoDTaskManager.TaskManager.cancel(self._chaseDelay)
		self._chaseDelay = None
		CoDTaskManager.TaskManager.cancel(self._moveDelay)
		self._moveDelay = None
		CoDTaskManager.TaskManager.cancel(self._attackDelay)
		self._attackDelay = None
"""
Aggressive monster.
"""
class MonsterA(Monster):
	def __init__(self, seed):
		super(MonsterA, self).__init__(seed, MONSTER_TYPE_A)
		self._HP = 200

	def isAggressive(self):
		return True

	def getAttck(self):
		return 20

	def getCordonRadius(self):
		return 5

"""
Passive monster.
"""
class MonsterB(Monster):
	def __init__(self, seed):
		super(MonsterB, self).__init__(seed, MONSTER_TYPE_B)
		self._HP = 250

	def isAggressive(self):
		return False


	def getAttck(self):
		return 15


	def getCordonRadius(self):
		return 0