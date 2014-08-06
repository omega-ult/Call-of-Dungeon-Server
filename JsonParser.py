# this file contains a class named 'JasonParser' for parsing json data into
# python's dict object.

# json key words for lexical analysis & grammatical analysis:
	
_json_predefined_escape_control_ = {
	u'"' : u'"',
	u'\\' : u'\\',
	u'/' : u'/',
	u'b' : u'\b',
	u'f' : u'\f',
	u'n' : u'\n',
	u'r' : u'\r',
	u't' : u'\t',
	u'u' : u'u'
}
_json_inv_predefined_escape_control_ = {
	u'"' : u'\\"',
	u'\\' : u'\\\\',
	u'/' : u'\/',
	u'\b' : u'\\b',
	u'\f' : u'\\f',
	u'\n' : u'\\n',
	u'\r' : u'\\r',
	u'\t' : u'\\t'
}

def _next_non_empty_char_(str, strPos):
	'''
	Get next non-empty char(' \t\r\n')'s position

	[in]str#str : input unicode string	
	[in]int#strPos : the start position of the string.

	[return]int#1 :
		#1 next position of a non-empty char
	'''
	_empty_char = [u' ', u'\t', u'\r', u'\n']
	_strCur = strPos
	while str[_strCur] in _empty_char:
		_strCur += 1
	return _strCur

def _parse_json_number_(str, strPos):
	'''
	Parse a json number, it is C-like number except that
	octal and hexadecimal formats are not used.
	
	[in]str#str : input unicode string	
	[in]int#strPos : the start position of the string.
	
	[return]int#1,int/float#2 :
		#1 is the end position of str after parsing,
		#2 is the result number.
	'''
	_strCur = strPos
	_numBegin = _strCur
	_numEnd = _strCur
	_isInt = False
	# may occur IndexError if str is invalid json string.ChainMap
	try:
		
		c = str[_strCur]
		# for +/- symbol
		if c == u'-':
			_strCur += 1
			c = str[_strCur]
			_negative = True
		else:
			_negative = False

		# forint, maybe the decimal's whole number part.
		_integer = 0
		_intBegin = _strCur
		_intEnd = _strCur
		if c.isdigit():
			if int(c) != 0:
				while c.isdigit():
					_strCur += 1
					c = str[_strCur]
					_intEnd = _strCur
			else:
				_strCur += 1
				c = str[_strCur]
				_intEnd = _strCur
			_numEnd = _intEnd
			#_integer =int(str[_intBegin : _intEnd])
		else:
			raise ValueError('Invalid digit: ' + c)

		# for decimal
		_fraction = 0.00
		_fracBegin = _strCur
		_fracEnd = _strCur
		if c == u'.':
			_strCur += 1
			c = str[_strCur]
			if c.isdigit():
				while c.isdigit():
					_strCur += 1
					c = str[_strCur]
					_fracEnd = _strCur
				_numEnd = _fracEnd
				#_fraction = float(str[_fracBegin : _fracEnd])
			else:
				raise ValueError('Unacceptable fraction: ' + c)

		# for exponent
		_exp = 0
		_expBegin = _strCur
		_expEnd = _strCur
		if c == u'e' or c == u'E':
			_strCur += 1
			c = str[_strCur]
			if c == u'-' or c == u'+':
				_strCur += 1
				c = str[_strCur]
			if c.isdigit():
				while c.isdigit():
					_strCur += 1
					c = str[_strCur]
					_expEnd = _strCur
				_numEnd = _expEnd
				#_exp =int(str[_expBegin : _expEnd])
			else: 
				raise ValueError('Unacceptable exponent: ' + c)

		if _numEnd == _intEnd:
			_isInt = True

	except ValueError, e:
		raise e
	except IndexError, e:
		_numEnd = _strCur

	# compose final number.
	_num = 0.00
	if _isInt:
		_num =int(str[_numBegin : _numEnd])
	else:
		_num = float(str[_numBegin : _numEnd])
		
	return _strCur, _num

def _parse_json_string_(str, strPos):
	'''
	Parse a json string.
	
	[in]str#str : input unicode string	
	[in]int#strPos : the start position of the string.
	
	[return]int#1, str#2 :
		#1 is the end position of str after parsing,
		#2 is the result unicode string.
	'''
	_strCur = strPos
	_strBegin = _strCur
	_strEnd = _strCur
	_resultStr = []
	try:
		# capture the string
		c = str[_strCur]
		if c == u'"':
			_strCur += 1;
			c = str[_strCur]
			_strBegin = _strCur
			_strEnd = _strBegin
		while c != u'"':
			# escape '\\'
			if c == u'\\':
				_strCur += 2
				c = str[_strCur]
			else:
				_strCur += 1;
				c = str[_strCur]
			_strEnd = _strCur
		_tmpStr = str[_strBegin : _strEnd]
		
		# parse escape '\'
		_tmpLen = len(_tmpStr)
		i = 0
		while i < _tmpLen:
			c = _tmpStr[i]
			if c == u'\\':
				i += 1
				c = _tmpStr[i]
				if c not in _json_predefined_escape_control_:
					raise ValueError('Invalid escape control character: ' + c + repr(i))
				c = _json_predefined_escape_control_[c]
				
				# for unicode
				if c == u'u':
					i += 1
					_ucode = _tmpStr[i : i + 4]
					i += 4
					c = unichr(int(_ucode, 16))
				else:
					i += 1
			else:
				i += 1	
			_resultStr.append(c)
		_strCur += 1
	except BaseException, e:
		raise e
		
	return _strCur, u''.join(_resultStr)

def _parse_json_value_(str, strPos):
	'''
	Parse a json value object with given str and start
	string position, value may be string, number, object,
	array, or predefined value 'true', 'false' or 'null'
	
	[in]str#str : input unicode string
	[in]int#strPos : the start position of the string.
	
	[return]int#1, dict/list/str/int/float/True/False/None#2 :
		#1 is the end position of str after parsing,
		#2 is the result value.
	'''
	_strCur = _next_non_empty_char_(str,strPos)
	_result = None
	try:
		c = str[_strCur]
		# for string
		if c == u'"':
			return _parse_json_string_(str, _strCur)
		# for number
		if c.isdigit() or c == u'-':
			return _parse_json_number_(str, _strCur)
		# for object
		if c == u'{':
			return _parse_json_object_(str, _strCur)
		# for array
		if c == u'[':
			return _parse_json_array_(str, _strCur)

		# for buildin values
		if c == u't':
			if str[_strCur : _strCur + 4] == u'true':
				return _strCur + 4, True
		if c == u'f':
			if str[_strCur : _strCur + 5] == u'false':
				return _strCur + 5, False
		if c == u'n':
			if str[_strCur : _strCur + 4] == u'null':
				return _strCur + 4, None
		raise BaseException('Invalid json value at: ' + repr(_strCur))
	
	except BaseException, e:
		raise e
	return _strCur, _result


def _parse_json_array_(str, strPos):
	'''
	Parse a json array, whicn enclosed with bracket([])
	
	[in]str#str : input unicode string
	[in]int#strPos : the start position of the string.
	
	[return]int#1, list#2 :
		#1 is the end position of str after parsing,
		#2 is the result array.
	'''
	_strCur = strPos
	_result = []
	try:
		_strCur = _next_non_empty_char_(str,_strCur)
		c = str[_strCur]
		if c != u'[':
			raise BaseException('Invalid beginning of array: ' + c)
		
		_strCur += 1
		_strCur = _next_non_empty_char_(str,_strCur)
		c = str[_strCur]
		while c != u']':
			_strCur, _val = _parse_json_value_(str, _strCur)
			_result.append(_val)
			_strCur = _next_non_empty_char_(str,_strCur)
			c = str[_strCur]
			# for more elements in the array
			if c == u',':
				_strCur += 1
				c = str[_strCur]
			elif c != u']':
				raise BaseException('Invalid json array at: ' + c + repr(_strCur))
		_strCur += 1
	except BaseException, e:
		raise e
	
	return _strCur, _result


def _parse_json_object_(str, strPos):
	'''
	Parse a json string to retrive a json object
	(dict in python), targetObj will be modified
	with parsing result.
	
	[in]str#str : input unicode string
	[in]int#strPos : the start position of the string.
	
	[return]int#1, dict#2 :
		#1 is the end position of str after parsing,
		#2 is the result object(dict in python).
	'''
	_strCur = strPos
	_result = {}
	try:
		_strCur = _next_non_empty_char_(str,_strCur)
		c = str[_strCur]
		if c != u'{':
			raise BaseException('Invalid beginning of array: ' + c)
		
		_strCur += 1
		_strCur = _next_non_empty_char_(str,_strCur)
		c = str[_strCur]
		while c != u'}':
			# the key must be string
			if c != u'"':
				raise ValueError('Invalid key value of: ' + c)
			
			_strCur, _key = _parse_json_string_(str, _strCur)
			_strCur = _next_non_empty_char_(str,_strCur)
			c = str[_strCur]
			if c != u':':
				raise ValueError('Invalid key value of: ' + c)
			
			_strCur += 1
			_strCur, _obj = _parse_json_value_(str, _strCur)
			
			_result[_key] = _obj
			_strCur = _next_non_empty_char_(str,_strCur)
			c = str[_strCur]
			# for more elements in that object
			if c == u',':
				_strCur += 1
				_strCur = _next_non_empty_char_(str,_strCur)
				c = str[_strCur]
			elif c != u'}':
				raise BaseException('Invalid json object at: ' + repr(_strCur) + '(' + c + ')')
			
		_strCur += 1
		
	except BaseException, e:
		raise e
	
	return _strCur, _result

def _parse_json_(str, strPos):
	
	'''
	Parse a json string to retrive a json object, or
	an array object if it is enclosed with brackets([]),
	
	[in]str#str : input unicode string
	[in]int#strPos : the start position of the string.
	
	[return]int#1, dict/list#2 :
		#1 is the end position of str after parsing,
		#2 is the result object(or array)
	'''
	c = str[_next_non_empty_char_(str,strPos)]
	if c == u'{':
		return _parse_json_object_(str, strPos)
	elif c == u'[':
		return _parse_json_array_(str, strPos)
	else:
		raise ValueError('Invalid json string')

def _dump_json_value_(obj, convertUnicode):
	'''
	Dump a python object into python string, value may be string, number,
	or predefined value 'true', 'false' or 'null'

	[in]str/int/float/True/False/None#obj : input object
	[in]True/False#convertUnicode : whether to convert
		unicode into json style(\uxxxx)
	
	[return]str#1 :
		#1 the result unicode string.
	'''
	if isinstance(obj, (str,str)) or isinstance(obj, (unicode,str)):
		_ustr_obj = u''
		if isinstance(obj, (str,str)):
			_ustr_obj = obj.decode('utf-8')
		else:
			_ustr_obj = obj
		_str_list = []
		_str_list.append(u'"')
		for c in _ustr_obj:
			if c in _json_inv_predefined_escape_control_:
				_str_list.append(_json_inv_predefined_escape_control_[c])
			elif c < u'\u0080' and c > u'\u0019':
				# for printable ascii:
				_str_list.append(c)
			else:
				# for non-ascii:
				if convertUnicode:
					_uc = u'\\u' + '%04x' % ord(c)
					_str_list.append(_uc)
				else:
					_str_list.append(c)
		_str_list.append(u'"')
		return u''.join(_str_list)
	# notice : must test bool before int because bool is
	# subclass of int!
	if isinstance(obj, bool):
		if obj == True:
			return u'true'
		else:
			return u'false'
	if obj == None:
		return u'null'
	if isinstance(obj, int) or isinstance(obj, float):
		_str = repr(obj)
		return _str.encode('utf-8')
	if isinstance(obj, long):
		_str = repr(obj)
		_str = _str[0 : len(_str)-1]
		return _str.encode('utf-8')
	return u''
	
def _dump_json_array_(obj, convertUnicode):
	'''
	Dump a python list into python string.

	[in]list#obj : input list
	[in]True/False#convertUnicode : whether to convert
		unicode into json style(\uxxxx)
	
	[return]list#1 :
		#1 the result unicode string list, join them to compose final result.
	'''
	_result = []
	_result.append(u'[')
	_list_empty = True
	for _val in obj:
		# handle ',', we use pre-add method.
		if _list_empty:
			_list_empty = False
		else:
			_result.append(u',')
			
		if isinstance(_val, list):
			_result.extend(_dump_json_array_(_val, convertUnicode))
		elif isinstance(_val, dict):
			_result.extend(_dump_json_object_(_val, convertUnicode))
		else:
			_result.append(_dump_json_value_(_val, convertUnicode))
			
	_result.append(u']')
	return _result

def _dump_json_object_(obj, convertUnicode):
	'''
	Dump a python dict into python string, make sure that _key, _value pair
	are both valid(see JsonParser.loadDict())

	[in]dict#obj : input dict
	[in]True/False#convertUnicode : whether to convert
		unicode into json style(\uxxxx)
	
	[return]list#1 :
		#1 the result unicode string list, join them to compose final result.
	'''
	_result = []
	_result.append(u'{')
	_list_empty = True
	for _key, _val in obj.items():
		if isinstance(_key, (str, str)):
			_key = _key.decode('utf-8')
		if isinstance(_key, (unicode,str)) and not isinstance(_val, tuple):
			# handle ',', we use pre-add method.
			if _list_empty:
				_list_empty = False
			else:
				_result.append(u',')
			_key = _dump_json_value_(_key, convertUnicode)
			_result.append(_key)
			_result.append(u':')
			
			if isinstance(_val, list):
				_result.extend(_dump_json_array_(_val, convertUnicode))
			elif isinstance(_val, dict):
				_result.extend(_dump_json_object_(_val, convertUnicode))
			else:
				_result.append(_dump_json_value_(_val, convertUnicode))
			
	_result.append(u'}')
	return _result


def _dump_json_(obj, convertUnicode = True):
	'''
	Dump a python object(may be dict or list) into python string.

	[in]dict/list#obj : input object
	[in]True/False#convertUnicode : whether to convert
		unicode into json style(\uxxxx)
	
	[return]str#1 :
		#1 the result unicode string
	'''
	if isinstance(obj, list):
		return u''.join(_dump_json_array_(obj, convertUnicode))
	if isinstance(obj, dict):
		return u''.join(_dump_json_object_(obj, convertUnicode))
	return u''

def _copy_json_list_(l):
	'''
	Deep copy a list without using copy module

	[in]list#l : input list
	
	[return]list#1 :
		#1 the result list
	'''
	_result = []
	for _val in l:
		if not isinstance(_val, tuple):
			if isinstance(_key, (str, str)):
				_key = _key.decode('utf-8')
			if isinstance(_val, dict):
				_result.append(_copy_json_dict_(_val))
			elif isinstance(_val, list):
				_result.extend(_copy_json_list_(_val))
			elif isinstance(_val, str) or isinstance(_val, int) or isinstance(_val, float) or \
				 _val == True or _val == False or _val == None:
				if isinstance(_val, (str, str)):
					_val = _val.decode('utf-8')
				_result.append(_val)
	return _result

def _copy_json_dict_(d):
	'''
	Deep copy a dict without using copy module

	[in]dict#d : input dict
	
	[return]dict#1 :
		#1 the result dict
	'''
	_result = {}
	for _key, _val in d.items():
		if isinstance(_key, (unicode, str)):
			if not isinstance(_val, tuple):
				if isinstance(_val, dict):
					_result[_key] = _copy_json_dict_(_val)
				elif isinstance(_val, list):
					_result[_key] = _copy_json_list_(_val)
				elif isinstance(_val, (unicode, str)) or isinstance(_val, int) or isinstance(_val, float) or \
					 _val == True or _val == False or _val == None:
					_result[_key] = _val
	return _result

class JsonParser:
	'''
	JsonParser uses a json string(can be read from a file)
	to form a json-like object(array or dict object).
	'''
	def __init__(self):
		self.name = "JsonParser"
		self._json_obj = {}
		
	def load(self, s):
		'''
		Load a string s into internal object, which represent a
		complete json object(or array).

		[in]str#s : input unicode string
		
		[return]None
		'''
		self._json_obj = {}
		try:
			_strPos, self._json_obj = _parse_json_(s, 0)
		except BaseException, e:
			raise e

	def dump(self, convertUnicode = False):
		'''
		Export internal object to a json string.

		[in]True/False#convertUnicode : whether to convert
			unicode into json style(\uxxxx)
		
		[return]str#1 :
			#1 unicode json string that represent internal object.
		'''
		return _dump_json_(self._json_obj, convertUnicode)
	
	def loadJson(self, f):
		'''
		Load a json file into internal object, which represent a
		complete json object(or array).

		[in]str#f : input file name
		
		[return]None
		'''
		_file = None
		try:
			_file = open(f)
			_str = _file.read()
			_ustr = _str.decode('utf-8')
			self.load(_ustr)
			_file.close()
		except BaseException, e:
			_file.close()
			raise e
		
	def dumpJson(self, f, convertUnicode = False):
		'''
		Export internal object to a json file.

		[in]str#f : target output file name
		[in]True/False#convertUnicode : whether to convert
			unicode into json style(\uxxxx)
		
		[return]str#1 :
			#1 json string that represent internal object.
		'''
		_file = None
		try:
			_file = open(f, 'w')
			_file.write(self.dump(convertUnicode).encode('utf-8'))
		except BaseException, e:
			raise e
		_file.close()
		
	
	def loadDict(self, d):
		'''
		Load a dict into internal object, which represent a
		complete json object(or array).
		Notice that only string can be valid key and value
		should not be tuple, item in d meets each condition
		will be discarded

		[in]dict#d : input dict
		
		[return]None
		'''
		self._json_obj = _copy_json_dict_(d)
	
	def dumpDict(self):
		'''
		Export internal object to a dict(or list).

		[in]None
		
		[return]dict/list#1 :
			#1 dict or list that represent json object.
		'''
		if isinstance(self._json_obj, dict):
			return _copy_json_dict_(self._json_obj)
		if isinstance(self._json_obj, list):
			return _copy_json_list_(self._json_obj)
		return {}
	
	def update(self, d):
		'''
		Update values from d to internal object, item will be
		ignored if it doesn't exist internally.

		[in]dict#d : input dict
		
		[return]None
		'''
		if not isinstance(self._json_obj, dict):
			return
		self._json_obj.update(d)
		self.loadDict(self._json_obj)
			
	def __getitem__(self, k):
		'''
		Query specified value at index k, k may be string(for dict)
		or int(for list), depending on internal object type

		[in]string/int#k : key index
		
		[return]list/dict/int/float/str/True/False/None#1 :
			#1 the object in specified index.
		'''
		return self._json_obj[k]
	
	def __setitem__(self, k, val):
		'''
		Set value for index k, k may be string(for dict)
		or int(for list), depending on internal object type

		[in]string/int#k : key index
		[in]list/dict/int/float/str/True/False/None#val : assigning value
		
		[return]None
		'''
		self._json_obj[k] = val