#======================================================================
#
# CoDServerLogic.py - handle the game state.
#
#
#======================================================================

import sys
import struct
import CoDMessage
import CoDNetwork
import CoDDatabaseManager
import CoDPlayer

SERVICE_PLAYER_CONNECT = 0x0000
ACTION_PLAYER_CONNECT = 0x0000
ACTION_PLAYER_DISCONNECT = 0xffff

SERVICE_PLAYER_ACCOUNT	= 0x0001
ACTION_PLAYER_LOGIN = 0x0001

"""
A requrest contains a sid and aid to indicate its action, and a data field to contain
its message.
"""
class Requrest(object):
	def __init__(self, time, netEvent, sid, aid, msg):
		self.time = time
		self.event = netEvent
		self.sid = sid
		self.aid = aid
		self.msg = msg
"""
Service is a manager class that handle actual requesting message, it will find 
a registered handler (using aid) to do specified work
"""
class Service(object):
	def __init__(self, sid = 0):
		self.serviceID = sid
		self._commandMap = {}

	"""
	The rqst should contain a aid to indicate its action id(aid)
	"""
	def execute(self, rqst, owner):
		_aid = rqst.aid
		if not _aid in self._commandMap:
			raise Exception("Bad commmand %s" %_aid)
		_func = self._commandMap[_aid]
		return _func(rqst, owner)

	def registerHandler(self, aid, func):
		self._commandMap[aid] = func

	def registerHandlerMap(self, cmdDict):
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

	def dispatch(self, rqst, owner):
		_sid = rqst.sid
		if not _sid in self._serviceMap:
			raise Exception("Bad request %s" %_sid)
		_svc = self._serviceMap[_sid]
		_svc.execute(rqst, owner)

	def register(self, sid, svc):
		self._serviceMap[sid] = svc



def getRequest(time, event, msg):
	if event == CoDNetwork.NET_NEW :
		return Requrest(time, event, SERVICE_PLAYER_CONNECT, ACTION_PLAYER_CONNECT, msg)
	if event == CoDNetwork.NET_LEAVE :
		return Requrest(time, event, SERVICE_PLAYER_CONNECT, ACTION_PLAYER_DISCONNECT, msg)
	if len(msg) < 2:
		return None
	_msg = struct.unpack('<H', msg[0:2])[0]
	if _msg == CoDMessage.MSG_CS_LOGIN:
		req = Requrest(time, event, SERVICE_PLAYER_ACCOUNT, ACTION_PLAYER_LOGIN, msg[2:])
		return req
	if _msg == CoDMessage.MSG_CS_MOVETO:
		pass

"""
Connection service definition
"""
class CoDConnectionService(Service):
	def __init__(self, logic):
		super(CoDConnectionService, self).__init__(SERVICE_PLAYER_CONNECT)
		self.registerHandler(ACTION_PLAYER_CONNECT, logic.handleConnect)
		self.registerHandler(ACTION_PLAYER_DISCONNECT, logic.handleDisconnect)

"""
Login services definition.
"""
class CoDAccountService(Service):
	def __init__(self, logic):
		super(CoDAccountService, self).__init__(SERVICE_PLAYER_ACCOUNT)
		self.registerHandler(ACTION_PLAYER_LOGIN, logic.handleLogin)



"""
Parse and handle every service request.
"""
GAME_STATE_RUNNING = 0 	# a state variable.
GAME_STATE_FINISHED = 1

class CoDServerLogic(object):
	def __init__(self, network, dbMgr, serviceDispatcher):
		self._gameState = GAME_STATE_RUNNING
		print 'game start running'

		self._network = network
		self._dbMgr = dbMgr

		self._playerDict = {}

		self._connectService = CoDConnectionService(self)
		self._loginService = CoDAccountService(self)
		serviceDispatcher.register(SERVICE_PLAYER_CONNECT, self._connectService)
		serviceDispatcher.register(SERVICE_PLAYER_ACCOUNT, self._loginService)


	def updateGame(self):
		#print 'updating'
		pass


	def handleConnect(self, rqst, owner):
		msg = CoDMessage.CoDMSG_ClientConnect(rqst.msg)
		print msg.clientAddr + ' hid(%d)'%(owner) + ' has been connected'
		welcomMsg = CoDMessage.CoDMSG_Welcome('welcome')
		self._network.send(owner, welcomMsg.marshal())

	def handleDisconnect(self, rqst, owner):
		msg = CoDMessage.CoDMSG_ClientDisconnect(rqst.msg)
		# do with player clean up
		_playerID = None
		for _k, _v in self._playerDict.items():
			if _v.getPlayerNetHandle() == owner:
				_playerID = _k
				break
		if _playerID != None:
			# send messages to other player
			del self._playerDict[_playerID]
			print 'player %d destroyed'%(_playerID)
		print 'hid(%d)'%(owner) + ' has disconnected'


	def handleLogin(self, rqst, owner):
		msg = CoDMessage.CoDMSG_PlayerLogin(rqst.msg)
		_pid, _acc, _pwd = self._dbMgr.getPlayerAccount(msg.account)
		if _pid != None:
			if _pid not in self._playerDict:
				# detect duplicated login
				for _k, _v in self._playerDict.items():
					if _v.getPlayerNetHandle() == owner:
						return
				if _pwd == msg.password:
					_confirm = CoDMessage.CoDMSG_PlayerLoginConfirm(owner, 'login accept')
					self._network.send(owner, _confirm.marshal())
					_player = CoDPlayer.Player(_pid, owner)
					# load data from db.

					print 'player %d created'%(_pid)
					self._playerDict[_pid] = _player

