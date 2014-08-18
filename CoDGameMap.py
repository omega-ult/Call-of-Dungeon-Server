#======================================================================
#
# CoDGameMap.py - GameMap used in game.
#
#
#======================================================================

import sys



"""
GameMap only handles messages about path, chest, it does not 
record player position in the map, but it provide function to
calculate a shortest path between two point.
"""

class GameMap(object):
	def __init__(self, bornFile, pathFile, monsterFile, chestFile): #chest file 
		# init map data.
		bornFile = open(bornFile)
		bx = bornFile.readline()
		by = bornFile.readline()
		self._playerBornPosX = int(bx)
		self._playerBornPosY = int(by)

		pathFile = open(pathFile)
		mw = pathFile.readline()
		mh = pathFile.readline()
		self._mapSizeHeight = int(mh)
		self._mapSizeWidth = int(mw)
		self._mapPath =  [[0 for col in range(self._mapSizeWidth)] for row in range(self._mapSizeHeight)]
		for y in range(0, self._mapSizeHeight):
			hStride = pathFile.readline()
			x = 0
			for c in hStride:
				if c == '1':
					self._mapPath[y][x] = 1
				x += 1

		self._monPos = []
		monFile = open(monsterFile)
		content = monFile.readline()
		plist = content.split(' ')
		for p in plist:
			if p != '':
				pos = p.split(',')
				#print pos
				self._monPos.append([int(pos[0]), int(pos[1])])

		self._chestPos = []
		chestFile = open(chestFile)
		content = chestFile.readline()
		plist = content.split(' ')
		for p in plist:
			if p != '':
				pos = p.split(',')
				self._chestPos.append([int(pos[0]), int(pos[1])])



	def getMapAvailablity(self, x, y):
		if x < self._mapSizeWidth and x >= 0 and y < self._mapSizeHeight and y >= 0:
			return self._mapPath[y][x] == 1

	def getBornPosition(self):
		return [self._playerBornPosX, self._playerBornPosY]

	def getMonsterPos(self):
		return self._monPos

	# return [[x,y], [x,y]] as result
	def getMonsterBornPosition(self):
		return self._monPos

	def getChestPosition(self):
		return self._chestPos