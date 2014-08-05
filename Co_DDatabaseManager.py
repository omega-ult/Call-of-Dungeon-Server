

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


"""
cm = CoDDatabaseManager()
cm.openDatabase(".\\cod.db")
"""