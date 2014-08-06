# -*- coding: utf-8 -*-
#======================================================================
#
# CoDNetwork.py - the network manager for receiving/sending message.
#
#
#======================================================================


import sys
import time
import struct
import socket
import errno


#======================================================================
# format of headers
#======================================================================
HEAD_WORD_LSB           = 0    # 2 bytes little endian (x86)
HEAD_WORD_MSB           = 1    # 2 bytes big endian (sparc)
HEAD_DWORD_LSB          = 2    # 4 bytes little endian (x86)
HEAD_DWORD_MSB          = 3    # 4 bytes big endian (sparc)
HEAD_BYTE_LSB           = 4    # 1 byte little endian
HEAD_BYTE_MSB           = 5    # 1 byte big endian
HEAD_WORD_LSB_EXCLUDE   = 6    # 2 bytes little endian, exclude itself
HEAD_WORD_MSB_EXCLUDE   = 7    # 2 bytes big endian, exclude itself
HEAD_DWORD_LSB_EXCLUDE  = 8    # 4 bytes little endian, exclude itself
HEAD_DWORD_MSB_EXCLUDE  = 9    # 4 bytes big endian, exclude itself
HEAD_BYTE_LSB_EXCLUDE   = 10   # 1 byte little endian, exclude itself
HEAD_BYTE_MSB_EXCLUDE   = 11   # 1 byte big endian, exclude itself
HEAD_BYTE_LSB_MASK	= 12   # 4 bytes little endian (x86) with mask

HEAD_HDR = (2, 2, 4, 4, 1, 1, 2, 2, 4, 4, 1, 1)
HEAD_INC = (0, 0, 0, 0, 0, 0, 2, 2, 4, 4, 1, 1)
HEAD_FMT = ('<H', '>H', '<I', '>I', '<B', '>B')

NET_STATE_STOP = 0				# state: init value
NET_STATE_CONNECTING = 1		# state: connecting
NET_STATE_ESTABLISHED = 2		# state: connected


#======================================================================
# netstream - basic tcp stream
#======================================================================
class NetStream(object):
	def __init__(self, head = HEAD_WORD_LSB):
		self._sock = None
		self._sendBuf = ''
		self._recvBuf = ''
		self._state = NET_STATE_STOP
		self._errd = (errno.EINPROGRESS, errno.EALREADY, errno.EWOULDBLOCK)
		self._conn = (errno.EISCONN, 10057, 10053)
		self._errc = 0
		self._headMask = False
		self.__headInit(head)

	def __headInit(self, head):
		if head == HEAD_BYTE_LSB_MASK:
			head = HEAD_DWORD_LSB
			self._headMask = True
		if (head < 0) or (head >= 12):
			head = 0
		_mode = head % 6
		self.__headMode = head
		self.__headHDR = HEAD_HDR[head]
		self.__headINC = HEAD_INC[head]
		self.__headFMT = HEAD_FMT[_mode]
		self.__headINT = _mode
		return 0

	def __tryConnect(self):
		if (self._state == NET_STATE_ESTABLISHED):
			return 1
		if (self._state != NET_STATE_CONNECTING):
			return -1
		try:
			self._sock.recv(0)
		except socket.error, (code, strerror):
			if code in self._conn:
				return 0
			if code in self._errd:
				self._state = NET_STATE_ESTABLISHED
				self._recvBuf = ''
				return 1
			self.close()
			return -1
		self._state = NET_STATE_ESTABLISHED
		return 1

	# try to receive all the data into recv_buf
	def __tryRecv(self):
		_rdata = ''
		while 1:
			_text = ''
			try:
				_text = self._sock.recv(1024)
				if not _text:
					self._errc = 10000 
					self.close()
					return -1
			except socket.error, (code, strerror):
				if not code in self._errd:
					self._errc = code
					delf.close()
					return -1
			if _text == '':
				break
			_rdata = _rdata + _text
		self._recvBuf = self._recvBuf + _rdata
		return len(_rdata)

	# send data from send_buf until block (reached system buffer limit)
	def __trySend(self):
		_wsize = 0
		if (len(self._sendBuf) == 0):
			return 0
		try:
			_wsize = self._sock.send(self._sendBuf)
		except socket.error, (code, strerror):
			if not code in self._errd:
				self._errc = code
				self.close()
				return -1
		self._sendBuf = self._sendBuf[_wsize:]
		return _wsize

	# connect the remote server
	def connect(self, address, port ,head = -1):
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._sock.setblocking(0)
		self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		self._sock.connect_ex((address, port))
		self._state = NET_STATE_CONNECTING
		self._sendBuf = ''
		self._recvBuf = ''
		self._errc = 0
		if head >= 0 and head < 12:
			self.__headInit(head)
		return 0

	# close connection
	def close(self):
		self._state = NET_STATE_STOP
		if not self._sock:
			return 0
		try:
			self._sock.close()
		except:
			pass
		self._sock = None
		return 0

	# assign a socket to netstream
	def assign(self, sock, head = -1):
		self.close()
		self._sock = sock
		self._sock.setblocking(0)
		self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		self._state = NET_STATE_ESTABLISHED
		if head >= 0 and head < 12:
			self.__headInit(head)
		self._sendBuf = ''
		self._recvBuf = ''
		return 0

	# update 
	def process(self):
		if self._state == NET_STATE_STOP:
			return 0
		if self._state == NET_STATE_CONNECTING:
			self.__tryConnect()
		if self._state == NET_STATE_ESTABLISHED:
			self.__tryRecv()
		if self._state == NET_STATE_ESTABLISHED:
			self.__trySend()
		return 0

	# return state
	def status(self):
		return self._state

	# error code
	def error(self):
		return self._errc

	# append data to send_buf then try to send it out (__trySend)
	def __sendRaw(self, data):
		self._sendBuf = self._sendBuf + data
		self.process()
		return 0

	# peek data from recv_buf (read without delete it)
	def __peekRaw(self, size):
		self.process()
		if len(self._recvBuf) == 0:
			return ''
		if size > len(self._recvBuf):
			size = len(self._recvBuf)
		_rdata = self._recvBuf[0:size]
		return _rdata

	# read data from recv_buf (read and delete it from recv_buf)
	def __recvRaw(self, size):
		_rdata = self.__peekRaw(size)
		size = len(_rdata)
		self._recvBuf = self._recvBuf[size:0]
		return _rdata

	# append data into send_buf with a size header
	def send(self, data, category = 0):
		_size = len(data) + self.__headHDR - self.__headINC
		if self._headMask:
			if category < 0:
				category = 0
			if category > 255:
				category = 255
			_size = (category << 24) | _size
		_wsize = struct.pack(self.__headFMT, _size)
		self.__sendRaw(_wsize + data)
		return 0

	def recv(self):
		_rsize = self.__peekRaw(self.__headHDR)
		if (len(_rsize) < self.__headHDR):
			return ''
		_size = struct.unpack(self.__headFMT, _rsize)[0] + self.__headINC
		if (len(self._recvBuf) < _size):
			return ''

		self.__recvRaw(self.__headHDR)
		return self.__recvRaw(_size - self.__headHDR)

	# set tcp nodelay flag
	def noDelay(self, nodelay = 0):
		if not 'TCP_NODELAY' in socket.__dict__:
			return -1
		if self._state != NET_STATE_ESTABLISHED:
			return -2
		self._sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, nodelay)
		return 0

#======================================================================
# nethost - basic tcp host
#======================================================================
NET_NEW		= 0	# new connection (id,tag) ip/d,port/w   <hid>
NET_LEAVE	= 1	# lost connection (id,tag)   		<hid>
NET_DATA	= 2	# data comming (id,tag) data...	<hid>
NET_TIMER	= 3	# timer event: (none, none) 


#======================================================================
# nethost - basic tcp host
#======================================================================
class NetHost(object):

	def __init__(self, head = HEAD_WORD_LSB):
		self._host = 0
		self._state = NET_STATE_STOP
		self._index = 1
		self._queue = []
		self._count = 0
		self._sock = None
		self._port = 0
		self._head = head
		self._timeOut = 70.0
		self._timeSlap = long(time.time() * 1000)
		self._clients = []
		self._period = 0

	# start listening
	def startup(self, port = 0):
		self.shutdown()
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		try:
			self._sock.bind(('0.0.0.0', port))
		except:
			try:
				self._sock.close()
			except:
				pass
			return -1
		self._sock.listen(65536)
		self._sock.setblocking(0)
		self._port = self._sock.getsockname()[1]
		self._state = NET_STATE_ESTABLISHED
		self._timeSlap = long(time.time() * 1000)
		return 0

	# shutdown service
	def shutdown(self):
		if self._sock:
			try:
				self._sock.close()
			except:
				pass
			self._sock = None
			self._index = 1
			for _n in self._clients:
				if not n:
					continue
				try:
					n.close()
				except:
					pass
			self._clients = []
			self._queue = []
			self._state = NET_STATE_STOP
			self._count = 0

	# private: close hid
	def __close(self, hid, code = 0):
		_pos = hid & 0xffff
		if (_pos < 0) or (_pos >= len(self._clients)):
			return -1
		_client = self._clients[_pos]
		if _client == None:
			return -2
		if _client.hid != hid:
			return -3
		_client.close()
		return 0

	def __send(self, hid, data):
		_pos = hid & 0xffff
		if (_pos < 0) or (_pos >= len(self._clients)):
			return -1
		_client = self._clients[_pos]
		if _client == None:
			return -2
		if _client.hid != hid:
			return -3
		_client.send(data)
		_client.process()
		return 0

	# update: process clients and handle accepting
	def process(self):
		_curTime = time.time()
		if self._state != NET_STATE_ESTABLISHED:
			return 0
		_sock = None
		try:
			_sock, _remote = self._sock.accept()
			_sock.setblocking(0)
		except:
			pass
		if self._count > 0x10000:
			try:
				_sock.close()
			except:
				pass
			_sock = None
		if _sock:
			_pos = -1
			for _i in xrange(len(self._clients)):
				if self._client[_i] == None:
					_pos = _i
					break
			if _pos < 0:
				_pos = len(self._clients)
				self._clients.append(None)
			_hid = (_pos &0xffff) | (self._index << 16)
			self._index += 1
			if self._index >= 0x7fff:
				self._index = 1
			_client = NetStream(self._head)
			_client.assign(_sock, self._head)
			_client.hid = _hid
			_client.tag = 0
			_client.active = _curTime
			_client.peername = _sock.getpeername()
			self._clients[_pos] = _client
			self._count += 1
			self._queue.append((NET_NEW, _hid, 0, repr(_client.peername)))
		for pos in xrange(len(self._clients)):
			_client = self._clients[pos]
			if not _client:
				continue
			_client.process()
			while _client.status() == NET_STATE_ESTABLISHED:
				_data = _client.recv()
				if _data == '':
					break
				self._queue.append((NET_DATA, _client.hid, _client.tag, _data))
				_client.active = _curTime
			_timeOut = _curTime - _client.active
			if (_client.status() == NET_STATE_STOP) or (_timeOut >= self._timeOut):
				hid, tag = _client.hid, _client.tag
				self._queue.append((NET_LEAVE, hid, tag, ''))
				self._clients[pos] = None
				_client.close()
				del _client
				self._count -= 1
		_curTime = long(time.time() * 1000)
		if _curTime - self._timeSlap > 100000:
			self._timeSlap = _curTime
		_period = self._period
		if _period > 0:
			while self._timeSlap < _curTime:
				self._queue.append((NET_TIMER, 0, 0, ''))
				self._timeSlap += _period
		return 0

	# send data to hid
	def send(self, hid, data):
		return self.__send(hid, data)

	# close client
	def close(self, hid):
		return self.__close(hid, hid)

	# set tag
	def setTag(self, hid, tag = 0):
		_pos = hid & 0xffff
		if (_pos < 0) or (_pos >= len(self._clients)):
			return -1
		_client = self._clients[_pos]
		if _client == None: 
			return -2
		if hid != _client.hid: 
			return -3
		_client.tag = tag
		return 0

	def getTag(self, hid, tag = 0):
		_pos = hid & 0xffff
		if (_pos < 0) or (_pos >= len(self._clients)):
			return -1
		_client = self._clients[_pos]
		if _client == None: 
			return -2
		if hid != _client.hid: 
			return -3
		return _client.tag

	# read event
	def read(self):
		if len(self._queue) == 0:
			return (-1, 0, 0, '')
		_event = self._queue[0]
		self._queue = self._queue[1:]
		return _event

	def setTimer(self, millisec = 1000):
		if millisec <= 0: 
			millisec = 0
		self._period = millisec
		self._timeSlap = long(time.time() * 1000)

	def noDelay (self, hid, nodelay = 0):
		_pos = hid & 0xffff
		if (_pos < 0) or (_pos >= len(self._clients)): 
			return -1
		_client = self._clients[_pos]
		if _client == None: 
			return -1
		if hid != _client.hid: 
			return -1
		return _client.noDelay(nodelay)


#----------------------------------------------------------------------
# testing case
#----------------------------------------------------------------------
if __name__ == '__main__':
	host = NetHost(8)
	host.startup(2000)
	sock = NetStream(8)
	last = time.time()
	sock.connect('127.0.0.1', 2000)
	sock.send('Hello, world !!')
	stat = 0
	last = time.time()
	print 'service startup at port', host._port
	host.setTimer(5000)
	sock.noDelay(0)
	sock.noDelay(1)
	while 1:
		time.sleep(0.1)
		host.process()
		sock.process()
		# client side testing case:
		if stat == 0:
			if sock.status() == NET_STATE_ESTABLISHED:
				stat = 1
				sock.send('Hello, world !!')
				last = time.time()
		elif stat == 1:	
			if time.time() - last >= 3.0:
				sock.send('VVVV')
				stat = 2
		elif stat == 2:
			if time.time() - last >= 5.0:
				sock.send('exit')
				stat = 3
		# server side testing case:
		event, wparam, lparam, data = host.read()
		if event < 0: continue
		print 'event=%d wparam=%xh lparam=%xh data="%s"'%(event, wparam, lparam, data)
		if event == NET_DATA:
			host.send(wparam, 'RE: ' + data)
			if data == 'exit': 
				print 'client request to exit'
				host.close(wparam)
		elif event == NET_NEW:
			host.send(wparam, 'HELLO CLIENT %X'%(wparam))
			host.setTag(wparam, wparam)
			host.noDelay(wparam, 1)


