#======================================================================
#
# CoDLogic.py - handle the game state.
#
#
#======================================================================

import sys


"""
Service is a manager class that handle actual requesting message, it will find 
a registered handler (using aid) to do specified work
"""
class Service(object):
	def __init__(self, sid = 0):
		self.serviceID = sid
		self._commandMap = {}

	"""
	The msg should contain a aid to indicate its action id(aid)
	"""
	def execute(self, msg, owner):
		_aid = msg.aid
		if not _aid in self._commandMap:
			raise Exception("Bad commmand %s" %_aid)
		_func = self._commandMap[_aid]
		return _func(msg, owner)

	def registerHandler(self, aid, func):
		self._commandMap[aid] = func

	def registerHandle(self, cmdDict):
		self._commandMap = {}
		for aid, func in cmdDict.items():
			self._commandMap[aid] = func
		return 0

"""
Dispatch service according to the request's service id(sid).
"""
class Dispatcher(object):
	def __init__(self):
		self._serviceMap = {}

	def dispatch(self, msg, owner):
		_sid = msg.sid
		if not _sid in self._serviceMap:
			raise Exception("Bad request %s" %_sid)
		_svc = self._serviceMap[_sid]
		_svc.execute(msg, ownder)

	def register(self, sid, svc):
		self._serviceMap[sid] = svc


"""
Parse and handle every service request.
"""
class CoDLogic(object):
	def __init__(self):
		pass
	def handleMessage(self, msg):
		pass
	def update(self):
		pass
