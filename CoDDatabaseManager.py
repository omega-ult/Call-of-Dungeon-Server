

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
		self._dbCur.execute('select * from PlayerAccount where UserName = "%s"'%(playerAccount))
		result = self._dbCur.fetchone()
		if result == None:
			return ()
		return result

	"""
	Return specified player's actors information
	"""
	def getPlayerActor(self, playerID):
		self._dbCur.execute('select * from PlayerActor where PlayerID = %d'%(playerID))
		result = self._dbCur.fetchall()
		return result

	#def queryTest(self):

	#	self._dbCur.execute('select * from PlayerAccount')
	#	data = self._dbCur.fetchall()
	#	print data
