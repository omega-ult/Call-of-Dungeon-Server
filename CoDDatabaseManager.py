

import sys
import sqlite3



class CoDDatabaseManager:
	"""
	Initialize.
	"""
	def __init__(self):
		self._dbConnection = []
	
	"""
	Connect to a database using a path of .db file
	"""
	def openDatabase(self, destPath):
		self._dbConnection = sqlite3.connect(destPath)
		self._dbCur = self._dbConnection.cursor()
	"""
	Return specified player's account information.
	return (playerID, PlayerAccount, PlayerPassword)
	"""
	def getPlayerAccount(self, playerAccount):
		self._dbCur.execute('select PlayerID, UserName, Password from PlayerAccount where UserName = (?)', (playerAccount,))
		result = self._dbCur.fetchone()
		if result == None:
			return ()
		return result

	"""
	Return specified player's actors information
	"""
	def getPlayerActor(self, playerID):
		self._dbCur.execute('select ActorID, NickName, ActorType, HP, MP from PlayerActor where PlayerID = (?)', (playerID,))
		result = self._dbCur.fetchall()
		pdataList = []
		for d in result:
			pdata = {}
			pdata['ActorID'] = d[0]
			pdata['NickName'] = d[1]
			pdata['ActorType'] = d[2]
			pdata['HP'] = d[3]
			pdata['MP'] = d[4]
			pdataList.append(pdata)
		return pdataList

	"""
	Return data of specified character
	"""
	def getActorData(self, actorID):
		self._dbCur.execute('select PlayerID, NickName, ActorType, HP, MP, Attack from PlayerActor where ActorID = (?)', (actorID,))
		actorData = {}
		result = self._dbCur.fetchone()
		if result != ():
			actorData['PID'] = int(result[0])
			actorData['ActorID'] = actorID
			actorData['NickName'] = result[1]
			actorData['ActorType'] = int(result[2])
			actorData['HP'] = int(result[3])
			actorData['MP'] = int(result[4])
			actorData['Atk'] = int(result[5])
		return actorData



	#def queryTest(self):

	#	self._dbCur.execute('select * from PlayerAccount')
	#	data = self._dbCur.fetchall()
	#	print data
