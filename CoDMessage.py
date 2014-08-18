#======================================================================
#
# CoDMessage.py - all messages transported between server and clients are
# packed by struct. 
#
#======================================================================

import struct
import socket


MSG_CS_CONNECT  = 0x0000
MSG_SC_WELCOME  = 0x0001
MSG_CS_DISCONNECT = 0xffff

MSG_CS_LOGIN			= 0x1001
MSG_SC_LOGIN_CONFIRM	= 0x1002
MSG_CS_TRY_ENTER 		= 0x1003
MSG_SC_ENTER_CONFIRM	= 0x1004
MSG_SC_CHARACTER_DATA	= 0x20ff
MSG_SC_NEW_PLAYER_ENTER	= 0x2002
MSG_SC_PLAYER_EXIT		= 0x2003


MSG_SC_PLAYER_STATE		= 0x3001
MSG_SC_MONSTER_STATE	= 0x3002
MSG_SC_ITEM_STATE		= 0x3003

MSG_CS_PLAYER_STATE_REPORT	= 0x3101

MSG_SC_MONSTER_DO_ACTION 	= 0x4000
MSG_SC_PLAYER_DO_ACTION	= 0x4001

MSG_CS_PLAYER_DO_ATTACK		= 0x4002
MSG_CS_PLAYER_GET_ITEM		= 0x4003
MSG_SC_PLAYER_RECEIVE_ITEM	= 0x4004
MSG_CS_PLAYER_USE_ITEM		= 0x4005
MSG_SC_PLAYER_RECEIVE_EFFECT	= 0x4006

MSG_CS_PLAYER_USE_FIRE_BALL  = 0x4100
MSG_CS_PLAYER_USE_DEAD_ZONE	= 0x4101

MSG_SC_PLAYER_PERFORM_FIRE_BALL  = 0x4fff
MSG_SC_PLAYER_PERFORM_DEAD_ZONE = 0x4ffe

MSG_CS_CHAT		= 0x5003
MSG_SC_CHAT		= 0x5003



MSG_SC_PLAYER_HURT	= 0x6001
MSG_SC_MONSTER_HURT	= 0x6002
MSG_SC_PLAYER_DIE	= 0x6003
MSG_SC_MONSTER_DIE	= 0x6004

MSG_SC_PLAYER_WIN	= 0x9999

"""
Base class for all CoDMessages, those message receive from client
should implement unmashal in __init__ and those sent to client
should implement marshal() to construct a valid packed string(with message
header included)
"""
class CoDMessage(object):
	def __init__(self, _msgStr, _msgID):
		self._msgStr = _msgStr
		self._msgID = _msgID

	def getMessage(self):
		return self._msgStr
	def getMessageID(self):
		return self._msgID

	def marshal(self):
		raise NotImplementedError

"""
Connect message has no format, it only contains a sender's address.
"""
class CoDMSG_ClientConnect(CoDMessage):
	def __init__(self, _msgStr):
		super(CoDMSG_ClientConnect, self).__init__(_msgStr, MSG_CS_CONNECT)
		self.clientAddr = _msgStr



"""
Welcome message sent to client.
"""
class CoDMSG_Welcome(CoDMessage):
	def __init__(self, _msgStr):
		super(CoDMSG_Welcome, self).__init__(_msgStr, MSG_SC_WELCOME)

	def marshal(self):
		# format { ushort msgLength, char* msg }
		# '<H%ds'
		header = struct.pack('<H', self._msgID)
		strLen = len(self._msgStr)
		content = struct.pack('<H%ds'%(strLen), strLen, self._msgStr)
		return header + content

"""
Disconect message has no format.
"""
class CoDMSG_ClientDisconnect(CoDMessage):
	def __init__(self, _msgStr):
		super(CoDMSG_ClientDisconnect, self).__init__(_msgStr, MSG_CS_DISCONNECT)

"""
Player login message.
"""
class CoDMSG_PlayerLogin(CoDMessage):
	def __init__(self, _msgStr):
		super(CoDMSG_PlayerLogin, self).__init__(_msgStr, MSG_CS_LOGIN)
		# parse the string, without message header.
		# --[[
		# packing struct 
		# {
		# 	ushort  accLength
		# 	char*   accStr
		# 	ushort  pwdLength
		# 	char*   pwdStr
		# } -- '<Hcn<Hcn' 
		# ]] 
		self.valid = True
		self.account = ''
		self.password = ''
		try:
			curPos = 0
			accLength = struct.unpack('<H', _msgStr[curPos:curPos+2])[0]
			curPos += 2
			accStr = struct.unpack('%ds'%(accLength), _msgStr[curPos:curPos+accLength])[0]
			curPos += accLength
			pwdLength = struct.unpack('<H', _msgStr[curPos:curPos+2])[0]
			curPos += 2
			pwdStr = struct.unpack('%ds'%(pwdLength), _msgStr[curPos:curPos+pwdLength])[0]
			self.account = accStr
			self.password = pwdStr
		except:
			print 'failed to unpack player account'
			self.valid = False


"""
Confirm player login
"""
class CoDMSG_PlayerLoginConfirm(CoDMessage):
	def __init__(self, hid, _msgStr):
		super(CoDMSG_PlayerLoginConfirm, self).__init__(_msgStr, MSG_SC_LOGIN_CONFIRM)
		self._hid = hid

	def marshal(self):
		# format { ushort playerHandle, ushort msgLength, char* msg }
		# '<I<H%ds'
		header = struct.pack('<H', self._msgID)
		hid = struct.pack('<I', self._hid)
		strLen = len(self._msgStr)
		content = struct.pack('<H%ds'%(strLen), strLen, self._msgStr)
		return header + hid + content

"""
Send character info to client let them choose character to play.
"""
class CoDMSG_CharacterInfo(CoDMessage):
	def __init__(self, _msgStr, pdataList):
		super(CoDMSG_CharacterInfo, self).__init__(_msgStr, MSG_SC_CHARACTER_DATA)
		self.dataList = pdataList

	def marshal(self):
		# format like:
		#{
		#	ushort actorCount
		#	{
		#		uint32 actorID
		#		ushort nameLen
		#		char*  name
		#		ushort actorType
		#	}...
		#}
		# '<H[<I<H%ds<H]'
		header = struct.pack('<H', self._msgID)
		count = len(self.dataList)
		cntStr = struct.pack('<H', count)
		actStr = ''
		for data in self.dataList:
			aidStr = struct.pack('<I', data['ActorID'])
			utf8str = data['NickName'].encode('utf-8')
			strLen = len(utf8str)
			nameStr = struct.pack('<H%ds'%(strLen), strLen, utf8str)
			typStr = struct.pack('<H', data['ActorType'])
			actStr = actStr + aidStr + nameStr + typStr
		return header + cntStr + actStr

"""
Client require enter game.
"""
class CoDMSG_ClientTryEnter(CoDMessage):
	def __init__(self, _msgStr):
		super(CoDMSG_ClientTryEnter, self).__init__(_msgStr, MSG_CS_TRY_ENTER)

		# format { uint32 actorID }
		self.actorID = None
		try:
			curPos = 0
			self.actorID = struct.unpack('<I', _msgStr[curPos:curPos+4])[0]
		except:
			print 'denied requrest to enter actor'

"""
Send to client, give them required data to begin playing.
"""
class CoDMSG_EnterConfirm(CoDMessage):
	def __init__(self, data, _msgStr):
		super(CoDMSG_EnterConfirm, self).__init__(_msgStr, MSG_SC_ENTER_CONFIRM)
		# format like:
		#{
		#	double serverTime
		#	uint32 playerID
		#	uint32 actorID
		#	ushort nameLen
		#	char*  name
		#	ushort actorType
		#	ushort posX
		#	ushort posY
		#	uint32 HP
		#	uint32 MP
		#}
		# '<I<I<H%ds<H<H<H<I<I'
		self.data = data

	def marshal(self):
		header = struct.pack('<H', self._msgID)
		tStr = struct.pack('d', self.data['Time'])
		pidStr = struct.pack('<I', self.data['PID'])
		aidStr = struct.pack('<I', self.data['ActorID'])
		utf8str = self.data['NickName'].encode('utf-8')
		strLen = len(utf8str)
		nameStr = struct.pack('<H%ds'%(strLen), strLen, utf8str)
		typStr = struct.pack('<H', self.data['ActorType'])
		posStr = struct.pack('<H', self.data['Position'][0])
		posStr = posStr + struct.pack('<H', self.data['Position'][1])
		HPStr = struct.pack('<I', self.data['HP'])
		MPStr = struct.pack('<I', self.data['MP'])
		cntStr = tStr + pidStr + aidStr + nameStr + typStr + posStr + HPStr + MPStr
		return header + cntStr

"""
Notify other players that a new character entered.
"""
class CoDMSG_NewPlayerEnter(CoDMessage):
	def __init__(self, hid, data, _msgStr):
		super(CoDMSG_NewPlayerEnter, self).__init__(_msgStr, MSG_SC_NEW_PLAYER_ENTER)
		self._hid = hid
		self.data = data
		# other player just need to know these.
		# format like:
		#{
		#	uint32 playerID
		#	uint32 actorID
		#	ushort nameLen
		#	char*  name
		#	ushort actorType
		#	ushort posX
		#	ushort posY
		#	ushort state
		#}

	def marshal(self):
		header = struct.pack('<H', self._msgID)
		pidStr = struct.pack('<I', self.data['PID'])
		aidStr = struct.pack('<I', self.data['ActorID'])
		utf8str = self.data['NickName'].encode('utf-8')
		strLen = len(utf8str)
		nameStr = struct.pack('<H%ds'%(strLen), strLen, utf8str)
		typStr = struct.pack('<H', self.data['ActorType'])
		posStr = struct.pack('<H', self.data['Position'][0])
		posStr = posStr + struct.pack('<H', self.data['Position'][1])
		staStr = struct.pack('<H', self.data['State'])
		cntStr = pidStr + aidStr + nameStr + typStr + posStr + staStr
		return header + cntStr

"""
On player exited.
"""
class CoDMSG_PlayerExit(CoDMessage):
	def __init__(self, playerID, _msgStr):
		super(CoDMSG_PlayerExit, self).__init__(_msgStr, MSG_SC_PLAYER_EXIT)
		self.playerID = playerID


	def marshal(self):
		# format like:{ uint32 playerID }
		header = struct.pack('<H', self._msgID)
		pidStr = struct.pack('<I', self.playerID)
		return header + pidStr

"""
Notify every player about other player's info.
"""
class CoDMSG_PlayerStateNotifictaion(CoDMessage):
	def __init__(self, dataList, _msgStr):
		super(CoDMSG_PlayerStateNotifictaion, self).__init__(_msgStr, MSG_SC_PLAYER_STATE)
		self.dataList = dataList

	def marshal(self):
		# format like:
		#{
		#	ushort playerCount
		#	{
		#		double time
		#		uint32 playerID
		#		ushort posX
		#		ushort posY
		#		ushort state
		#		uint32 hp
		#		uint32 mp
		#	}...
		#}
		header = struct.pack('<H', self._msgID)
		count = len(self.dataList)
		cntStr = struct.pack('<H', count)
		dataStr = ''
		for data in self.dataList:
			timeStr = struct.pack('d', data['Time'])
			pidStr = struct.pack('<I', data['PID'])
			posStr = struct.pack('<H', data['PosX'])
			posStr = posStr + struct.pack('<H', data['PosY'])
			staStr = struct.pack('<H', data['State'])
			hpStr = struct.pack('<I', data['HP'])
			mpStr = struct.pack('<I', data['MP'])
			dataStr = dataStr + timeStr + pidStr + posStr + staStr + hpStr + mpStr
		return header + cntStr + dataStr

"""
Notify every player about monsters.
"""
class CoDMSG_MonsterStateNotification(CoDMessage):
	def __init__(self, dataList, _msgStr):
		super(CoDMSG_MonsterStateNotification, self).__init__(_msgStr, MSG_SC_MONSTER_STATE)
		self.dataList = dataList



	def marshal(self):
		# format like:
		#{
		#	ushort monCount
		#	{
		#		double time
		#		uint32 seed
		#		ushort type
		#		uint32 hp
		#		ushort posX
		#		ushort posY
		#	}
		#
		#} 
		# '<H[d<I<H<I<H<H]'
		header = struct.pack('<H', self._msgID)
		count = len(self.dataList)
		cntStr = struct.pack('<H', count)
		dataStr = ''
		for data in self.dataList:
			timeStr = struct.pack('d', data['Time'])
			seedStr = struct.pack('<I', data['Seed'])
			tpStr = struct.pack('<H', data['Type'])
			hpStr = struct.pack('<I', data['HP'])
			posStr = struct.pack('<H', data['PosX'])
			posStr = posStr + struct.pack('<H', data['PosY'])
			dataStr = dataStr + timeStr + seedStr + tpStr + hpStr + posStr
		return header + cntStr + dataStr

"""
Notify every player about items.
"""
class CoDMSG_ItemStateNotification(CoDMessage):
	def __init__(self, dataList, _msgStr):
		super(CoDMSG_ItemStateNotification, self).__init__(_msgStr, MSG_SC_ITEM_STATE)
		self.dataList = dataList

	def marshal(self):
		 # format 
		 #{
		 #	ushort itemCount
		 #	{
		 #		double time 
		 #		uint32 seed
		 #		ushort type 
		 #		uint32 posX
		 #		uint32 posY
		 #	}
		 #}
		header = struct.pack('<H',self._msgID)
		count = len(self.dataList)
		cntStr = struct.pack('<H', count)
		dataStr = ''
		for data in self.dataList:
			timeStr = struct.pack('d', data['Time'])
			seedStr = struct.pack('<I', data['Seed'])
			tpStr = struct.pack('<H', data['Type'])
			posStr = struct.pack('<H', data['PosX'])
			posStr = posStr + struct.pack('<H', data['PosY'])
			dataStr = dataStr + timeStr + seedStr + tpStr + posStr
		return header + cntStr + dataStr

"""
Sent from client to report player state.
"""
class CoDMSG_PlayerStateReport(CoDMessage):
	def __init__(self, _msgStr):
		super(CoDMSG_PlayerStateReport, self).__init__(_msgStr, MSG_CS_PLAYER_STATE_REPORT)
		# format like:
		#{
		#		uint32 playerID
		#		ushort action
		#		ushort posX
		#		ushort posY
		#}
		# '<H[<I<H<H<H]'
		self.valid = True
		self.playerID = 0
		self.action = 0
		self.posX = 0
		self.posY = 0
		try:
			curPos = 0
			self.playerID = struct.unpack('<I', _msgStr[curPos:curPos+4])[0]
			curPos += 4
			self.action = struct.unpack('<H', _msgStr[curPos:curPos+2])[0]
			curPos += 2
			self.posX = struct.unpack('<H', _msgStr[curPos:curPos+2])[0]
			curPos += 2
			self.posY = struct.unpack('<H', _msgStr[curPos:curPos+2])[0]
		except:
			self.valid = False

"""
Player receiving damage.
"""
class CoDMSG_PlayerHurt(CoDMessage):
	def __init__(self, data, _msgStr):
		super(CoDMSG_PlayerHurt, self).__init__(_msgStr, MSG_SC_PLAYER_HURT)

		self.data = data

	def marshal(self):
		# format like:
		#{
		#	uint32 monsterSeed
		#	uint32 playerID
		#	uint32 damage
		#}
		# '<H<I<I'
		header = struct.pack('<H', self._msgID)
		monStr = struct.pack('<I', self.data['Monster'])
		pidStr = struct.pack('<I', self.data['PID'])
		dmgStr = struct.pack('<I', self.data['Damage'])

		return header + monStr + pidStr + dmgStr

"""
Monster receiving damage.
"""
class CoDMSG_MonsterHurt(CoDMessage):
	def __init__(self, data, _msgStr):
		super(CoDMSG_MonsterHurt, self).__init__(_msgStr, MSG_SC_MONSTER_HURT)

		self.data = data

	def marshal(self):
		# format like:
		#{
		#	uint32 monsterSeed
		#	uint32 damage
		#}
		# '<H<I<I'
		header = struct.pack('<H', self._msgID)
		monStr = struct.pack('<I', self.data['Monster'])
		dmgStr = struct.pack('<I', self.data['Damage'])

		return header + monStr + dmgStr
"""
Player Die
"""
class CoDMSG_PlayerDie(CoDMessage):
	def __init__(self, data, _msgStr):
		super(CoDMSG_PlayerDie, self).__init__(_msgStr, MSG_SC_PLAYER_DIE)
		self.data = data

	def marshal(self):
		# format like:
		#{
		#	uint32 playerID
		#}
		header = struct.pack('<H', self._msgID)
		pidStr = struct.pack('<I', self.data['PID'])
		return header + pidStr

"""
Monster Die
"""
class CoDMSG_MonsterDie(CoDMessage):
	def __init__(self, data, _msgStr):
		super(CoDMSG_MonsterDie, self).__init__(_msgStr, MSG_SC_MONSTER_DIE)
		self.data = data

	def marshal(self):
		# format like:
		#{
		#	uint32 monsterSeed
		#}
		header = struct.pack('<H', self._msgID)
		monStr = struct.pack('<I', self.data['Monster'])
		return header + monStr


"""
Monster Actions
"""
class CoDMSG_MonsterDoAction(CoDMessage):
	def __init__(self, data, _msgStr):
		super(CoDMSG_MonsterDoAction, self).__init__(_msgStr, MSG_SC_MONSTER_DO_ACTION)
		self.data = data

	def marshal(self):
		# format like:
		#{
		#	uint32 monsterSeed
		#	ushort actionID
		#}
		# '<H<I<H'
		header = struct.pack('<H', self._msgID)
		monStr = struct.pack('<I', self.data['Monster'])
		actStr = struct.pack('<H', self.data['Action'])

		return header + monStr + actStr


"""
Player Actions
"""
class  CoDMSG_PlayerAttack(CoDMessage):
	def __init__(self, _msgStr):
		super(CoDMSG_PlayerAttack, self).__init__(_msgStr, MSG_CS_PLAYER_DO_ATTACK)

		# format 
		# {
		# 	uint32 playerID
		#	uint32 targetMonster
		# }
		self.valid = True
		self.playerID = None
		self.targetMonster = None
		try:
			curPos = 0
			self.playerID = struct.unpack('<I', _msgStr[curPos:curPos+4])[0]
			curPos += 4
			self.targetMonster = struct.unpack('<I', _msgStr[curPos:curPos+4])[0]
		except:
			print 'denied requrest to perform attack'
			self.valid = False

"""
Player get item.
"""
class CoDMSG_PlayerGetItem(CoDMessage):
	def __init__(self, _msgStr):
		super(CoDMSG_PlayerGetItem, self).__init__(_msgStr, MSG_CS_PLAYER_GET_ITEM)

		#--[[
		#{
		#	uint32 playerID
		#	uint32 itemSeed
		#}
		#]]
		self.valid = True
		self.playerID = None
		self.itemSeed = None	
		try:
			curPos = 0
			self.playerID = struct.unpack('<I', _msgStr[curPos:curPos+4])[0]
			curPos += 4
			self.itemSeed = struct.unpack('<I', _msgStr[curPos:curPos+4])[0]
		except:
			print 'denied requrest to get item'
			self.valid = False

"""
Server confirm player recieve item.
"""
class CoDMSG_PlayerReceiveItem(CoDMessage):
	def __init__(self,playerID, itemSeed, itemType, _msgStr):
		super(CoDMSG_PlayerReceiveItem, self).__init__(_msgStr, MSG_SC_PLAYER_RECEIVE_ITEM)
		#--[[
		#{
		#	uint32 playerID
		#	uint32 itemSeed
		#	ushort itemType
		#}
		#]]
		self.playerID = playerID
		self.itemSeed = itemSeed
		self.itemType = itemType

	def marshal(self):
		header = struct.pack('<H', self._msgID)
		pidStr = struct.pack('<I', self.playerID)
		itmStr = struct.pack('<I', self.itemSeed)
		typStr = struct.pack('<H', self.itemType)

		return header + pidStr + itmStr + typStr


"""
Receive player chat.
"""
class CoDMSG_PlayerChat(CoDMessage):
	def __init__(self, _msgStr):
		super(CoDMSG_PlayerChat, self).__init__(_msgStr, MSG_CS_CHAT)
		#--[[
		#packing struct 
		#{
		#	uint32  playerID
		#	uint16  msgLength
		#	char*   msgStr
		#} -- '<I<Hcn' 
		#]]
		self.valid = True
		self.playerID = None
		self.msg = None	
		try:
			curPos = 0
			self.playerID = struct.unpack('<I', _msgStr[curPos:curPos+4])[0]
			curPos += 4
			msgLen = struct.unpack('<H', _msgStr[curPos:curPos+2])[0]
			curPos += 2
			self.msg = struct.unpack('%ds'%(msgLen), _msgStr[curPos:curPos+msgLen])[0]
		except:
			print 'denied message'
			self.valid = False

"""
Broadcast player chat.
"""
class CoDMSG_BoradcastPlayerChat(CoDMessage):
	def __init__(self, playerID, _msgStr):
		super(CoDMSG_BoradcastPlayerChat, self).__init__(_msgStr, MSG_SC_CHAT)
		self.playerID = playerID
		#--[[
		#packing struct 
		#{
		#	uint32  playerID
		#	uint16  msgLength
		#	char*   msgStr
		#} -- '<I<Hcn' 
		#]]

	def marshal(self):
		header = struct.pack('<H', self._msgID)
		idStr = struct.pack('<I', self.playerID)
		strLen = len(self._msgStr)
		content = struct.pack('<H%ds'%(strLen), strLen, self._msgStr)
		return header + idStr + content

"""
player use item.
"""
class CoDMSG_PlayerUseItem(CoDMessage):
	def __init__(self, _msgStr):
		super(CoDMSG_PlayerUseItem, self).__init__(_msgStr, MSG_CS_PLAYER_USE_ITEM)
		#--[[
		#{
		#	uint32 playerID
		#	uint32 itemSeed
		#}
		self.valid = True
		self.playerID = None
		self.itemSeed = None	
		try:
			curPos = 0
			self.playerID = struct.unpack('<I', _msgStr[curPos:curPos+4])[0]
			curPos += 4
			self.itemSeed = struct.unpack('<I', _msgStr[curPos:curPos+4])[0]
		except:
			print 'denied requrest to use item'
			self.valid = False

"""
player receive item effect
"""
class CoDMSG_PlayerReceiveEffect(CoDMessage):
	def __init__(self,playerID, itemSeed, hpEff, mpEff, _msgStr):
		super(CoDMSG_PlayerReceiveEffect, self).__init__(_msgStr, MSG_SC_PLAYER_RECEIVE_EFFECT)
		#--[[
		#{
		#	uint32 playerID
		#	uint32 itemSeed
		#	uint32 HpEffect
		#	uint32 MpEffect
		#}
		self.playerID = playerID
		self.itemSeed = itemSeed
		self.hpEffect = hpEff
		self.mpEffect = mpEff

	def marshal(self):
		header = struct.pack('<H', self._msgID)
		pidStr = struct.pack('<I', self.playerID)
		seedStr = struct.pack('<I', self.itemSeed)
		hpStr = struct.pack('<I', self.hpEffect)
		mpStr = struct.pack('<I', self.mpEffect)

		return header + pidStr + seedStr + hpStr + mpStr


"""
Fire ball skill
"""
class CoDMSG_PlayerUseFireBall(CoDMessage):
	def __init__(self, _msgStr):
		super(CoDMSG_PlayerUseFireBall, self).__init__(_msgStr, MSG_CS_PLAYER_USE_FIRE_BALL)
		#--[[
		#{
		#	uint32 playerID
		# 	uint32 targetMonster
		#}

		self.valid = True
		self.playerID = None
		self.targetMonster = None	
		try:
			curPos = 0
			self.playerID = struct.unpack('<I', _msgStr[curPos:curPos+4])[0]
			curPos += 4
			self.targetMonster = struct.unpack('<I', _msgStr[curPos:curPos+4])[0]
		except:
			print 'denied requrest to use skill'
			self.valid = False

"""
Dead skill
"""
class CoDMSG_PlayerUseDeadZone(CoDMessage):
	def __init__(self, _msgStr):
		super(CoDMSG_PlayerUseDeadZone, self).__init__(_msgStr, MSG_CS_PLAYER_USE_DEAD_ZONE)
		#--[[
		#{
		#	uint32 playerID
		#}

		self.valid = True
		self.playerID = None	
		try:
			curPos = 0
			self.playerID = struct.unpack('<I', _msgStr[curPos:curPos+4])[0]
		except:
			print 'denied requrest to use skill'
			self.valid = False

"""
player skill performed
"""
class CoDMSG_PlayerFireBallPerformed(CoDMessage):
	def __init__(self, playerX, playerY, monX, monY, _msgStr):
		super(CoDMSG_PlayerFireBallPerformed, self).__init__(_msgStr, MSG_SC_PLAYER_PERFORM_FIRE_BALL)
		#--[[
		#{
		#	ushort playerX
		#	ushort playerY
		#	ushort monX
		#	ushort monY
		#}
		self.playerX = playerX
		self.playerY = playerY
		self.monX = monX
		self.monY = monY

	def marshal(self):
		header = struct.pack('<H', self._msgID)
		pposStr = struct.pack('<H', self.playerX) + struct.pack('<H',self.playerY)
		mposStr = struct.pack('<H', self.monX) + struct.pack('<H', self.monY)

		return header + pposStr + mposStr

class CoDMSG_PlayerDeadZonePerformed(CoDMessage):
	def __init__(self, playerID, _msgStr):
		super(CoDMSG_PlayerDeadZonePerformed, self).__init__(_msgStr, MSG_SC_PLAYER_PERFORM_DEAD_ZONE)
		#--[[
		#{
		#	uint32 playerID
		#}
		self.playerID = playerID

	def marshal(self):
		header = struct.pack('<H', self._msgID)
		pidStr = struct.pack('<I', self.playerID)

		return header + pidStr


class CoDMSG_PlayerWin(CoDMessage):
	def __init__(self, _msgStr):
		super(CoDMSG_PlayerWin, self).__init__(_msgStr, MSG_SC_PLAYER_WIN)


	def marshal(self):
		header = struct.pack('<H', self._msgID)
		return header + struct.pack('<H', 9999)
