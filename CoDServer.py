
import sys
import socket
import CoDDatabaseManager


class CoDServer:
	"""
	Initialize.
	"""
	def __init__(self):
		self._dbMgr = CoDDatabaseManager.CoDDatabaseManager()
		self._dbMgr.openDatabase(".\\cod.db")
		
		self._socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self._socket.bind(('localhost', 10305))
		self._socket.listen(20)

	"""
	Start logic loop
	"""
	def run(self):
		while True:
			conn, addr = self._socket.accept()
		try:
			conn.settimeout(5)
			buf = conn.recv(1024)
			if buf == '1':
				conn.send('welcome to server!')
		except socket.timeout, e:
			conn.close()

if __name__ == '__main__':
	svr = CoDServer();
