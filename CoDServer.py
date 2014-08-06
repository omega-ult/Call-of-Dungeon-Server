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

SERVER_PORT  = 10305

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
		self._network = CoDNetwork.NetHost(CoDNetwork.HEAD_DWORD_LSB_EXCLUDE)
		self._network.startup(SERVER_PORT)
		self._network.setTimer(1000)
		# Game logic
		self._clientMsgList = []
		self._gameLogic = CoDLogic.CoDLogic()

		# test case
		"""
		self.client = CoDNetwork.NetStream(CoDNetwork.HEAD_DWORD_LSB_EXCLUDE)
		self.client.connect('127.0.0.1', SERVER_PORT)
		self.client.send('yoooo');
		self.client.noDelay(0)
		self.client.noDelay(1)
		"""
	"""
	Network handling
	"""
	def process(self, timeOut):
		# receive msgs from clients, then push them to the _clientMsgList
		self._network.process()
		_event, _clientHid, _clientTag, _data = self._network.read()
		if _event > 0:
			self._clientMsgList.append((_event, _clientHid, _clientTag, _data))
		if time.time() - self._tickStartTime > 5.0:
			CoDTaskManager.TaskManager.cancel(self._tickTimer)
			print 'stop test now'
			sys.exit(1)
	"""
	Start logic loop
	"""
	def tick(self):
		# update game logic every 0.1 sec.
		#print "called every ?"
		for _msg in self._clientMsgList:
			self._gameLogic.handleMessage(_msg);
		self._clientMsgList = []

if __name__ == '__main__':
	svr = CoDServer()
	svr.run(0.1)
