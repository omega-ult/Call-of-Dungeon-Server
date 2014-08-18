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
import CoDServerLogic
import CoDMessage



class IOService(object):
	def process(self, timeout):
		#process network
		raise NotImplementedError 

	def run(self):
		while 1:
			self.process(self._timeout)
			CoDTaskManager.TaskManager.scheduler()
		return

class GameServer(IOService):
	def __init__(self, tickTime = 0.1):
		super(GameServer, self).__init__()
		self._timeout = tickTime
		self._tickTimer = CoDTaskManager.TaskManager.addSustainTask(tickTime, self.tick)
		return

	def tick(self):
		raise NotImplementedError

	def run(self):
		super(GameServer, self).run()



"""
Main server body
"""
SERVER_PORT  = 10305

class CoDServer(GameServer):
	"""
	Initialize.
	"""
	def __init__(self):
		super(CoDServer, self).__init__(0.5)
		self._tickStartTime = time.time()
		# Database 
		self._dbMgr = CoDDatabaseManager.CoDDatabaseManager()
		self._dbMgr.openDatabase(".\\cod.db")
		# Network 
		self._network = CoDNetwork.NetHost()
		self._network.startup(SERVER_PORT)
		self._network.setTimer(1000)
		# Game logic
		self._clientMsgList = []
		self._serviceDispatcher = CoDServerLogic.Dispatcher()
		self._gameLogic = CoDServerLogic.CoDServerLogic(self._network, self._dbMgr, self._serviceDispatcher)

		
	"""self._mapSizeHeight
	Network handling
	"""
	def process(self, timeOut):
		# receive msgs from clients, then push them to the _clientMsgList
		self._network.process()
		_event, _clientHid, _clientTag, _data = self._network.read()
		_time = time.time()
		if _event != -1:
			if _event != CoDNetwork.NET_TIMER:
				self._clientMsgList.append((_time, _event, _clientHid, _clientTag, _data))

		#if time.time() - self._tickStartTime > 50.0:
		#	CoDTaskManager.TaskManager.cancel(self._tickTimer)
		#	print 'stop test now'
		#	sys.exit(1)
	"""
	Start logic loop
	"""
	def tick(self):
		for n in self._clientMsgList:
			_rqst = CoDServerLogic.getRequest(n[0], n[1], n[4])
			if _rqst != None:
				try:
					self._serviceDispatcher.dispatch(_rqst, n[2])
				except:
					raise
		self._clientMsgList = []
		self._gameLogic.updateGame()

import struct
if __name__ == '__main__':
	svr = CoDServer()
	svr.run()