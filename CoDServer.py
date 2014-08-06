#======================================================================
#
# CoDServer.py - the entry of the game server program.
#
#
#======================================================================


import sys
import time
import socket
import CoDNetwork
import CoDDatabaseManager
import CoDTaskManager
import CoDLogic

class IOService(object):
	def process(self, timeout):
		#process network
		raise NotImplementedError 

	def run(self, timeout = 0.5):
		while 1:
			self.process(timeout)
			CoDTaskManager.TaskManager.scheduler()
		return

class GameServer(IOService):
	def __init__(self, tickTime = 0.1):
		super(GameServer, self).__init__()
		self._tickTimer = CoDTaskManager.TaskManager.addSustainTask(tickTime, self.tick)
		return

	def tick(self):
		raise NotImplementedError

	def run(self, timeOut = 0.5):
		super(GameServer, self).run(timeOut)

class CoDServer(GameServer):
	"""
	Initialize.
	"""
	def __init__(self):
		super(CoDServer, self).__init__(0.1)
		self._tickStartTime = time.time()
		# Database 
		self._dbMgr = CoDDatabaseManager.CoDDatabaseManager()
		self._dbMgr.openDatabase(".\\cod.db")
		# Network 
		self._network = CoDNetwork.NetHost(8)
		self._network.startup(10305)
		# Game logic
		self._clientMsgList = []
		self._gameLogic = CoDLogic.CoDLogic()

	"""
	Network handling
	"""
	def process(self, timeOut):
		# receive msgs from clients, then push them to the _clientMsgList

		if time.time() - self._tickStartTime > 10.0:
			CoDTaskManager.TaskManager.cancel(self._tickTimer)
			print 'stop test now'
			sys.exit(1)
	"""
	Start logic loop
	"""
	def tick(self):
		# update game logic every 0.1 sec.
		print "called every ?"
		for _msg in self._clientMsgList:
			self._gameLogic.handleMessage(_msg);
		self._clientMsgList = []

if __name__ == '__main__':
	svr = CoDServer()
	svr.run(0.1)
