#======================================================================
#
# CoDServerLogic.py - handle the game state.
#
#
#======================================================================

import sys
import time
import struct
import math
import random
import CoDMessage
import CoDNetwork
import CoDDatabaseManager
import CoDTaskManager
import CoDPlayer
import CoDMonster
import CoDItems
import CoDGameMap

SERVICE_PLAYER_CONNECT = 0x0000
ACTION_PLAYER_CONNECT = 0x0000
ACTION_PLAYER_DISCONNECT = 0xffff

SERVICE_PLAYER_ACCOUNT	= 0x0001
ACTION_PLAYER_LOGIN = 0x0001
ACTION_PLAYER_ENTER = 0x0002

SERVICE_GAME			= 0x0002
ACTION_PLAYER_REPORT	= 0x0001
ACTION_PLAYER_ATTACK = 0x0003
ACTION_PLAYER_GET_ITEM	= 0x0004
ACTION_PLAYER_USE_ITEM	= 0x0005
ACTION_PLAYER_CHAT		= 0x1fff

ACTION_PLAYER_USE_FIRE_BALL	= 0x0006
ACTION_PLAYER_USE_DEAD_ZONE	= 0x0007


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
	# out game requrests
	_msg = struct.unpack('<H', msg[0:2])[0]
	_peeledmsg = msg[2:]
	if _msg == CoDMessage.MSG_CS_LOGIN:
		return Requrest(time, event, SERVICE_PLAYER_ACCOUNT, ACTION_PLAYER_LOGIN, _peeledmsg)
	if _msg == CoDMessage.MSG_CS_TRY_ENTER:
		return Requrest(time, event, SERVICE_PLAYER_ACCOUNT, ACTION_PLAYER_ENTER, _peeledmsg)
	# in game requests.
	if _msg == CoDMessage.MSG_CS_PLAYER_STATE_REPORT:
		return Requrest(time, event, SERVICE_GAME, ACTION_PLAYER_REPORT, _peeledmsg)
	if _msg == CoDMessage.MSG_CS_PLAYER_DO_ATTACK:
		return Requrest(time, event, SERVICE_GAME, ACTION_PLAYER_ATTACK, _peeledmsg)
	if _msg == CoDMessage.MSG_CS_PLAYER_GET_ITEM:
		return Requrest(time, event, SERVICE_GAME, ACTION_PLAYER_GET_ITEM, _peeledmsg)
	if _msg == CoDMessage.MSG_CS_PLAYER_USE_ITEM:
		return Requrest(time, event, SERVICE_GAME, ACTION_PLAYER_USE_ITEM, _peeledmsg)
	if _msg == CoDMessage.MSG_CS_CHAT:
		return Requrest(time, event, SERVICE_GAME, ACTION_PLAYER_CHAT, _peeledmsg)
	if _msg == CoDMessage.MSG_CS_PLAYER_USE_FIRE_BALL:
		return Requrest(time, event, SERVICE_GAME, ACTION_PLAYER_USE_FIRE_BALL, _peeledmsg)
	if _msg == CoDMessage.MSG_CS_PLAYER_USE_DEAD_ZONE:
		return Requrest(time, event, SERVICE_GAME, ACTION_PLAYER_USE_DEAD_ZONE, _peeledmsg)
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
		self.registerHandler(ACTION_PLAYER_ENTER, logic.handleEnter)

"""
Game service definition.
"""
class CoDGameService(Service):
	def __init__(self, logic):
		super(CoDGameService, self).__init__(SERVICE_GAME)
		self.registerHandler(ACTION_PLAYER_REPORT, logic.handlePlayerReport)
		self.registerHandler(ACTION_PLAYER_ATTACK, logic.handlePlayerAttack)
		self.registerHandler(ACTION_PLAYER_GET_ITEM, logic.handlePlayerGetItem)
		self.registerHandler(ACTION_PLAYER_USE_ITEM, logic.handlePlayerUseItem)
		self.registerHandler(ACTION_PLAYER_CHAT, logic.handlePlayerChat)
		self.registerHandler(ACTION_PLAYER_USE_FIRE_BALL, logic.handlePlayerUseFireBall)
		self.registerHandler(ACTION_PLAYER_USE_DEAD_ZONE, logic.handlePlayerUseDeadZone)

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

		self._gameMap = CoDGameMap.GameMap('born.txt', 'path.txt', 'monster.txt', 'chest.txt')

		self._monsterDict = {}
		self._monsterSeed = 0
		self._typeALimit = 10
		self._typeBLimit = 6
		self._monsterMaxCount = 30
		self.initMonsterData()

		self._itemDict = {}
		self._itemSeed = 0
		self.initItemData()


		self._connectService = CoDConnectionService(self)
		self._loginService = CoDAccountService(self)
		self._gameService = CoDGameService(self)
		serviceDispatcher.register(SERVICE_PLAYER_CONNECT, self._connectService)
		serviceDispatcher.register(SERVICE_PLAYER_ACCOUNT, self._loginService)
		serviceDispatcher.register(SERVICE_GAME, self._gameService)

	def initMonsterData(self):
		self._monsterDict['TypeA'] = { 'lastGenTime' : 0, 'mons' : {} }
		self._monsterDict['TypeB'] = { 'lastGenTime' : 0, 'mons' : {} }

	def initItemData(self):
		itmPos = self._gameMap.getChestPosition()
		for p in itmPos:
			self._itemDict[(p[0], p[1])] = {'lastGenTime' : 0, 'item' : None}


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
			self._playerDict[_playerID].leaveGame()
			_toOther = CoDMessage.CoDMSG_PlayerExit(_playerID, "").marshal()
			for _k, _v in self._playerDict.items():
				self._network.send(_v.getPlayerNetHandle(), _toOther)


			del self._playerDict[_playerID]
			print 'player %d destroyed'%(_playerID)
		print 'hid(%d)'%(owner) + ' has disconnected'


	def handleLogin(self, rqst, owner):
		msg = CoDMessage.CoDMSG_PlayerLogin(rqst.msg)
		if msg.valid == False:
			return
		if msg.account == '':
			return
		result = self._dbMgr.getPlayerAccount(msg.account)
		if result == ():
			return
		_pid, _acc, _pwd = result
		if _pid != None:
			if _pid not in self._playerDict:
				# detect duplicated login
				for _k, _v in self._playerDict.items():
					if _v.getPlayerNetHandle() == owner:
						return
				if _pwd == msg.password:
					_confirm = CoDMessage.CoDMSG_PlayerLoginConfirm(owner, 'login accept')
					self._network.send(owner, _confirm.marshal())
					# fetch player data.
					data = self._dbMgr.getPlayerActor(_pid)
					_pdata = CoDMessage.CoDMSG_CharacterInfo('player data', data)
					self._network.send(owner, _pdata.marshal())
					print 'player %d created'%(_pid)
					self._playerDict[_pid] = CoDPlayer.Player(_pid, owner, _acc)



	def handleEnter(self, rqst, owner):
		msg = CoDMessage.CoDMSG_ClientTryEnter(rqst.msg)
		if msg.actorID != None:
			# fetch player info from db.
			data = self._dbMgr.getActorData(msg.actorID)
			data['Time'] = time.time()
			data['Position'] = self._gameMap.getBornPosition()
			# test whether this player is valid.
			_newPlayer = self._playerDict[data['PID']]
			if _newPlayer != None:
				if _newPlayer.isLeaved :
					sendData = CoDMessage.CoDMSG_EnterConfirm(data, 'confirm enter')
					self._network.send(owner, sendData.marshal())

					_newPlayer.enterGameAs(data)

					print 'player %d entered as %s'%(data['PID'], data['NickName'])
					_toExistedPlayer = CoDMessage.CoDMSG_NewPlayerEnter(owner, _newPlayer.getActorData(), 'player entered')
					# notify other players.
					for _k, _val in self._playerDict.items():
						if not _val.isLeaved() and _val != _newPlayer:
							_toNewPlayer = CoDMessage.CoDMSG_NewPlayerEnter(_val.getPlayerNetHandle(), _val.getActorData(), 'player entered')
							self._network.send(_val.getPlayerNetHandle(), _toExistedPlayer.marshal())
							self._network.send(owner, _toNewPlayer.marshal())
				
	def handlePlayerReport(self, rqst, owner):
		msg = CoDMessage.CoDMSG_PlayerStateReport(rqst.msg)
		if msg.valid:
			player = self._playerDict.get(msg.playerID)
			if player != None:
				player.setPlayerPosition(msg.posX, msg.posY)

	def handlePlayerAttack(self, rqst, owner):
		msg = CoDMessage.CoDMSG_PlayerAttack(rqst.msg)
		if msg.valid:
			player = self._playerDict.get(msg.playerID, None)
			if player != None:
				mon = self.findMonster(msg.targetMonster)
				if mon != None:
					px, py = player.getPlayerPosition()
					mx, my = mon.getPosition()
					if (abs(px-mx) < 2 and py == my) or (abs(py-my) < 2 and mx == px):
						self.dealMonsterReceiveDamage(player.getPlayerID(), mon, player.getPlayerATK())

	def handlePlayerGetItem(self, rqst, owner):
		msg = CoDMessage.CoDMSG_PlayerGetItem(rqst.msg)
		if msg.valid:
			player = self._playerDict.get(msg.playerID, None)
			if player != None:
				for ik, iv in self._itemDict.items():
					if iv['item'] != None:
						if iv['item'].getSeed() == msg.itemSeed:
							px, py = player.getPlayerPosition()
							ix, iy = ik[0], ik[1]
							if px == ix and py == iy:
								itm = iv['item']
								player.appendItem(itm)
								iv['item'] = None
								rcvMsg = CoDMessage.CoDMSG_PlayerReceiveItem(player.getPlayerID(), itm.getSeed(), itm.getType(), '')
								self._network.send(owner, rcvMsg.marshal())

	def handlePlayerUseItem(self, rqst, owner):
		msg = CoDMessage.CoDMSG_PlayerUseItem(rqst.msg)
		if msg.valid:
			player = self._playerDict.get(msg.playerID, None)
			if player != None:
				item = player.getItem(msg.itemSeed)
				if item != None:
					player.setPlayerHP(player.getPlayerHP() + item.effectOnHP())
					player.setPlayerMP(player.getPlayerMP() + item.effectOnMP())
					sendMsg = CoDMessage.CoDMSG_PlayerReceiveEffect( player.getPlayerID(), item.getSeed(),item.effectOnHP(), item.effectOnMP(),'')
					player.removeItem(item.getSeed())
					self.broadcast(sendMsg.marshal())

	def handlePlayerChat(self, rqst, owner):
		msg = CoDMessage.CoDMSG_PlayerChat(rqst.msg)
		if msg.valid:
			bc = CoDMessage.CoDMSG_BoradcastPlayerChat(msg.playerID, msg.msg)
			bc.marshal()
			self.broadcast(bc.marshal())
			if msg.msg == 'whosyourdaddy':
				player = self._playerDict.get(msg.playerID, None)
				if player != None:
					if player.getPlayerMP() >= 100:
						player.setPlayerMP(player.getPlayerMP() - 100)
						allMon = []					
						monA = self._monsterDict['TypeA']['mons']
						for _k, _v in monA.items():
							allMon.append(_v)
						monB = self._monsterDict['TypeB']['mons']
						for _k, _v in monB.items():
							allMon.append(_v)
						px, py = player.getPlayerPosition()
						for mon in allMon:
							mx, my = mon.getPosition()
							self.dealMonsterReceiveDamage(player.getPlayerID(), mon, 100)
							_sendMsg = CoDMessage.CoDMSG_PlayerFireBallPerformed(px, py, mx, my,'')
							self.broadcast(_sendMsg.marshal())



	def handlePlayerUseFireBall(self, rqst, owner):
		msg = CoDMessage.CoDMSG_PlayerUseFireBall(rqst.msg)
		if msg.valid:
			player = self._playerDict.get(msg.playerID, None)
			if player != None:
				mon = self.findMonster(msg.targetMonster)
				if mon != None:
					px, py = player.getPlayerPosition()
					mx, my = mon.getPosition()
					if math.sqrt((px-mx)*(px-mx) + (py-my)*(py-my)) < 7:
						if player.getPlayerMP() >= 20:
							player.setPlayerMP(player.getPlayerMP() - 20)
							self.dealMonsterReceiveDamage(player.getPlayerID(), mon, 80)
							_sendMsg = CoDMessage.CoDMSG_PlayerFireBallPerformed(px, py, mx, my,'')
							self.broadcast(_sendMsg.marshal())


	def handlePlayerUseDeadZone(self, rqst, owner):
		msg = CoDMessage.CoDMSG_PlayerUseDeadZone(rqst.msg)
		if msg.valid:
			player = self._playerDict.get(msg.playerID, None)
			if player != None:
				# move all monsters, or deal damage.
				if player.getPlayerMP() >= 40:
					player.setPlayerMP(player.getPlayerMP() - 40)
				_sendMsg = CoDMessage.CoDMSG_PlayerDeadZonePerformed(player.getPlayerID(),'')
				self.broadcast(_sendMsg.marshal())
				monA = self._monsterDict['TypeA']['mons']
				allMon = []
				for _k, _v in monA.items():
					allMon.append(_v)
				monB = self._monsterDict['TypeB']['mons']
				for _k, _v in monB.items():
					allMon.append(_v)
				px, py = player.getPlayerPosition()
				for mon in allMon:
					mx, my = mon.getPosition()
					if math.sqrt((px-mx)*(px-mx) + (py-my)*(py-my)) < 5:
						self.dealMonsterReceiveDamage(player.getPlayerID(), mon, 60)


	def findMonster(self, seed):
		monList = self._monsterDict['TypeA']['mons']
		mon = monList.get(seed, None)
		if mon != None:
			return mon
		monList = self._monsterDict['TypeB']['mons']
		mon = monList.get(seed, None)
		return mon

	def removeMonster(self, seed):
		monList = self._monsterDict['TypeA']['mons']
		mon = monList.get(seed, None)
		if mon != None:
			del monList[seed]
			return
		monList = self._monsterDict['TypeB']['mons']
		mon = monList.get(seed, None)
		if mon != None:
			del monList[seed]

	def dealMonsterReceiveDamage(self, playerID, mon, damage):
		curHP = mon.getHP() - damage
		mon.setTargetPlayer(playerID)
		data = {'Monster': mon.getSeed(), 'Damage':damage}
		msg = CoDMessage.CoDMSG_MonsterHurt(data, '')
		_msg = msg.marshal()
		self.broadcast(_msg)
		if curHP < 0: curHP = 0
		mon.setHP(curHP)
		if curHP == 0:
			# deal monster die.
			dieMsg = CoDMessage.CoDMSG_MonsterDie(data, '')
			_dieMsg = dieMsg.marshal()
			self.removeMonster(mon.getSeed())
			self.broadcast(_dieMsg)



	# broadcast all players' states 
	def sycPlayerStates(self):
		# send time pack.
		curTime = time.time()

		# send player states.
		# construct message packs
		_msgPack = []
		for _k, _v in self._playerDict.items():
			msg = {}
			msg['Time'] = curTime
			msg['PID'] = _v.getPlayerID()
			msg['PosX'], msg['PosY'] = _v.getPlayerPosition()
			msg['State'] = _v.getPlayerState()
			msg['HP'] = _v.getPlayerHP()
			msg['MP'] = _v.getPlayerMP()
			_msgPack.append(msg)

		# send to clients.
		_toAllPlayer = CoDMessage.CoDMSG_PlayerStateNotifictaion(_msgPack, '')
		_pmsg = _toAllPlayer.marshal()

		# construct monster message packs.
		monDataList = []
		monA = self._monsterDict['TypeA']['mons']
		for _k, _v in monA.items():
			data = {}
			data['Time'] = curTime
			data['Seed'] = _k
			data['Type'] = _v.getType()
			data['HP'] = _v.getHP()
			data['PosX'], data['PosY'] = _v.getPosition()
			monDataList.append(data)

		monB = self._monsterDict['TypeB']['mons']
		for _k, _v in monB.items():
			data = {}
			data['Time'] = curTime
			data['Seed'] = _k
			data['Type'] = _v.getType()
			data['HP'] = _v.getHP()
			data['PosX'], data['PosY'] = _v.getPosition()
			monDataList.append(data)
		_monsterState = CoDMessage.CoDMSG_MonsterStateNotification(monDataList,'')
		_mmsg = _monsterState.marshal()

		#construct item message packs.
		idata = []
		for _k, _v in self._itemDict.items():
			if _v['item'] != None:
				data = {}
				data['Time'] = curTime
				data['Seed'] = _v['item'].getSeed()
				data['Type'] = _v['item'].getType()
				data['PosX'], data['PosY'] = _k[0], _k[1]
				idata.append(data)
		_itmState = CoDMessage.CoDMSG_ItemStateNotification(idata,'')
		_imsg = _itmState.marshal()

		# notify all players.
		for _k, _v in self._playerDict.items():
			if not _v.isLeaved():
				self._network.send(_v.getPlayerNetHandle(), _pmsg)
				self._network.send(_v.getPlayerNetHandle(), _mmsg)
				self._network.send(_v.getPlayerNetHandle(), _imsg)


	def updateMonster(self):
		curTime = time.time()
		#self._monsterDict['TypeA'] = { 'lastGenTime' = 0, 'mons' = {} }
		#self._monsterDict['TypeB'] = { 'lastGenTime' = 0, 'mons' = {} }
		monA = self._monsterDict['TypeA']
		if len(monA['mons']) < self._typeALimit and self._monsterSeed < self._monsterMaxCount:
			if curTime - monA['lastGenTime'] > 5:
				monA['lastGenTime'] = curTime
				seed = self._monsterSeed
				self._monsterSeed += 1
				newA = CoDMonster.MonsterA(seed)
				# choose a pos from map.
				monBornPos = self._gameMap.getMonsterBornPosition()
				idx = math.floor(random.uniform(0, len(monBornPos)))
				pos = monBornPos[int(idx)]
				newA.setPosition(pos[0], pos[1])

				monA['mons'][seed] = newA
		
		monB = self._monsterDict['TypeB']
		if len(monB['mons']) < self._typeBLimit and self._monsterSeed < self._monsterMaxCount:
			if curTime - monB['lastGenTime'] > 5:
				monB['lastGenTime'] = curTime
				seed = self._monsterSeed
				self._monsterSeed += 1
				newB = CoDMonster.MonsterB(seed)
				# choose a pos from map.
				monBornPos = self._gameMap.getMonsterBornPosition()
				idx = math.floor(random.uniform(0, len(monBornPos)))
				pos = monBornPos[int(idx)]
				newB.setPosition(pos[0], pos[1])

				monB['mons'][seed] = newB

		# handle AI
		# since we know monA is aggressive, we just update 
		monA = self._monsterDict['TypeA']['mons']
		for _k, _v in monA.items():
			if _v.getTargetPlayer() == None:
				for _pk, _pv in self._playerDict.items():
					if _pv.getPlayerState() != CoDPlayer.PLAYER_STATE_DEAD:
						px, py = _pv.getPlayerPosition()
						mx, my = _v.getPosition()
						if math.sqrt((mx-px)*(mx-px) + (my-py)*(my-py)) < _v.getCordonRadius():
							_v.setTargetPlayer(_pv.getPlayerID())




		# move all monsters, or deal damage.
		monA = self._monsterDict['TypeA']['mons']
		allMon = []
		for _k, _v in monA.items():
			allMon.append(_v)
		monB = self._monsterDict['TypeB']['mons']
		for _k, _v in monB.items():
			allMon.append(_v)


		for m in allMon:
			target = m.getTargetPlayer()
			if target != None:
				p = self._playerDict.get(target, None)
				if p != None and p.isLeaved() != True:
					if p.getPlayerState() == CoDPlayer.PLAYER_STATE_DEAD:
						m.setTargetPlayer(None)
					else:
						px, py = p.getPlayerPosition()
						mx, my = m.getPosition()
						if px == mx and py == my:
							# deal damage:
							val = m.attack()
							if val != None:
								# broadcast monster action to all players.
								data = {'Monster':m.getSeed(), 'Action':CoDMonster.MONSTER_ACTION_ATTACK}
								actionMsg = CoDMessage.CoDMSG_MonsterDoAction(data,'' )
								self.broadcast(actionMsg.marshal())

								self.dealPlayerReceiveDamage(p, val)

								# broadcast damage to all players.
								data = {'Monster':m.getSeed(), 'PID':target, 'Damage':val}
								damageMsg = CoDMessage.CoDMSG_PlayerHurt(data, '')
								self.broadcast(damageMsg.marshal())

						elif m.canMove():
							_canMove, mx, my = self.getNextMonsterMove(mx, my, px, py)
							if _canMove:
								m.setPosition(mx, my)
			else:
				m.setTargetPlayer(None)
				# do roaming.
				if random.uniform(0,1) < 0.5:
					mx, my = m.getPosition()
					m.setPosition(mx, my)
				elif m.canMove() == True:
					mx, my = m.getPosition()
					px, py = mx, my
					idx = math.floor(random.uniform(0, 4))
					if idx == 0:
						px += 1
					elif idx == 1:
						px -= 1
					elif idx == 2:
						py += 1
					else:
						py -= 1
					_canMove, mx, my = self.getNextMonsterMove(mx, my, px, py)
					if _canMove:
						m.setPosition(mx, my)

	def updateItems(self):
		curTime = time.time()

		for _k, _v in self._itemDict.items():
			if _v['item'] == None:
				if curTime - _v['lastGenTime'] > 20:
					_v['lastGenTime'] = curTime
					seed = self._itemSeed;
					self._itemSeed += 1
					if random.uniform(0,1) < 0.5:
						_v['item']	= CoDItems.HealthPotion(seed)
					else:
						_v['item'] = CoDItems.ManaPotion(seed)
			else:
				_v['lastGenTime'] = curTime



	def dealPlayerReceiveDamage(self, player, damage):
		if player.getPlayerState() != CoDPlayer.PLAYER_STATE_DEAD:
			curHP = player.getPlayerHP() - damage
			if curHP < 0: curHP = 0
			if curHP == 0:
				player.setPlayerState(CoDPlayer.PLAYER_STATE_DEAD)
				# broadcast .
				data = {'PID':player.getPlayerID()}
				msg = CoDMessage.CoDMSG_PlayerDie(data, '')
				self.broadcast(msg.marshal())
				
			player.setPlayerHP(curHP)



	def getNextMonsterMove(self, mx, my, px, py):
		# use linear shortest path to chase.
		ydist = my - py
		xdist = mx - px
		moveX = 0
		moveY = 0
		canMove = False
		# try most efficient path.
		if abs(ydist) > abs(xdist):
			# go ydir firstly
			moveX = 0
			if ydist > 0:
				canMove = self._gameMap.getMapAvailablity(mx, my - 1)
				if canMove:	# sure we can move
					moveY = -1
			else:
				canMove = self._gameMap.getMapAvailablity(mx, my + 1)
				if canMove:	# sure we can move
					moveY = 1
			if not canMove:
				# try xdir
				moveY = 0
				if xdist > 0:
					canMove = self._gameMap.getMapAvailablity(mx - 1, my)
					if canMove:	# sure we can move
						moveX = -1
				else:
					canMove = self._gameMap.getMapAvailablity(mx + 1, my)
					if canMove:	# sure we can move
						moveX = 1

		else:
			# try ydir firstly
			moveY = 0
			if xdist > 0:
				canMove = self._gameMap.getMapAvailablity(mx - 1, my)
				if canMove:	# sure we can move
					moveX = -1
			else:
				canMove = self._gameMap.getMapAvailablity(mx + 1, my)
				if canMove:	# sure we can move
					moveX = 1
			
			if not canMove:
				# go xdir 
				moveX = 0
				if ydist > 0:
					canMove = self._gameMap.getMapAvailablity(mx, my - 1)
					if canMove:	# sure we can move
						moveY = -1
				else:
					canMove = self._gameMap.getMapAvailablity(mx, my + 1)
					if canMove:	# sure we can move
						moveY = 1
		return canMove, mx + moveX, my + moveY

	def broadcast(self, msg):
		for _pk, _pv in self._playerDict.items():
			if not _pv.isLeaved():
				self._network.send(_pv.getPlayerNetHandle(), msg)


	def updateGame(self):
		# query current time.
		curTime = time.time()

		self.updateMonster()

		self.updateItems()

		self.sycPlayerStates()

		if self._monsterSeed >= self._monsterMaxCount:
			if len(self._monsterDict['TypeA']['mons']) == 0 and len(self._monsterDict['TypeB']['mons']) == 0:
				msg = CoDMessage.CoDMSG_PlayerWin('')
				self.broadcast(msg.marshal())
