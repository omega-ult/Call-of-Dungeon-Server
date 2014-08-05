# -*- coding: utf-8 -*-

import sys
import sqlite3

sqlite3.connect(".\\cod.db")


class CoDDatabaseManager(object):
	"""
	Initialize database using dbLoc as fullpath of .db file.
	"""
	def __init__(self, dbLoc):
		print "yooooo"
