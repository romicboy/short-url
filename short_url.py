#!/usr/bin/python
# -*- coding: utf-8 -*- 
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import redis
import MySQLdb

redis_host = 'redis_host'
redis_port = 6379
db_host = 'db_host'
db_uesr = 'root'
db_password = 'root'
db_dbname = 'test'

redis_handle = redis.Redis(host=redis_host,port=redis_port,db=0)

PORT_NUMBER = 8080

#连接 mysql 的方法： connect('ip','user','password','dbname')
connect = MySQLdb.connect(db_host, db_uesr, db_password, db_dbname);

#所有的查询，都在连接 con 的一个模块 cursor 上面运行的
cursor = connect.cursor(MySQLdb.cursors.DictCursor)

#This class will handles any incoming request from
#the browser
class myHandler(BaseHTTPRequestHandler):

	#Handler for the GET requests
	def do_GET(self):

		http_query_string = self.parameter_get('/surl')
		if not http_query_string:
			return

		query_dict = self.http_query_to_dict(http_query_string);

		redis_key = query_dict['v']
		del query_dict['v']

		url = '404'
		if redis_key:
			data = self.redis_get(redis_key)
			if not data:
				db_data = self.db_get(redis_key)
				if db_data:
					data = db_data['url']
					
			if data:
				self.redis_set(redis_key,data)
				url = self.getEntireUrl(data,self.http_build_query(query_dict))
				self.html(url)
				#self.redirect(data)
				return

		self.html(url)
	

	def html(self, html):
		self.send_response(200)
		self.send_header('Content-type','text/html')
		self.end_headers()
		self.wfile.write(html)
		return

	def redirect(self, url):
		self.send_response(301)
		self.send_header('Location',url)
		self.end_headers()
		return

	def parameter_get(self, name):
		path_split = self.path.split('?')
		controller = path_split[0]
		if len(path_split) > 1:
			parameter = path_split[1]
			print 'controller: '+controller+', parameter: '+parameter
			if controller == name:
				return parameter

		return None

	def getEntireUrl(self, url, param):
		if None != param:
			if url.find('?') != -1:
				return url+"&"+param
			else:
				return url+"?"+param
		else:
			return url

	def http_query_to_dict(self, name):
		if not name:
			return None
		get_split = name.split('&')
		dict = {}
		if len(get_split) > 0:
			for get_str in get_split:
				get_str_split = get_str.split('=')
				dict[get_str_split[0]] = get_str_split[1]
		return dict

	def http_build_query(self, dict):
		if not dict:
			return None

		get_string = ''
		for key in dict.keys(): 
			#print 'key=%s, value=%s' % (key, dict[key]) 
			get_string += key +'=' + dict[key]
			get_string += '&'
		return get_string[0:len(get_string)-1]
		
	def redis_get(self, name):
		return redis_handle.get(name)

	def redis_set(self, name, value):
		redis_handle.setex(name,value,86400)

	def db_get(self, surl):
		sql = "SELECT * from su_shorturl where surl = '"+surl+"'"
		print sql
		cursor.execute(sql)
		data = cursor.fetchone()
		return data

try:
	#Create a web server and define the handler to manage the
	#incoming request
	server = HTTPServer(('', PORT_NUMBER), myHandler)
	print 'Started httpserver on port ' , PORT_NUMBER

	#Wait forever for incoming htto requests
	server.serve_forever()

except KeyboardInterrupt:
	print 'received, shutting down the web server'
	server.socket.close()
