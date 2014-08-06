#======================================================================
#
# CoDMessage.py - all messages transported between server and clients are
# written in plain json string, this file contains their definitions. 
#
#======================================================================


import JsonParser



if __name__ == '__main__':
	jp = JsonParser.JsonParser()
	test_json_str = '{"description": "Support escaping",	"data": { "v":"\\" \\\\ \/ \b  \f \n  \r \t \u0081"},	"valid": false}'
	jp.load(test_json_str)
	print (jp.dumpDict())