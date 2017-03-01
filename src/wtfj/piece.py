import time
from threading import Thread
from Queue import Queue,Empty
import traceback

from uid import *
from connector import *


class Piece(object):
	def __init__(self,uid,connector):
		''' Requires a unique identifier and a connector supplying i/o '''
		assert uid in names(Uid) # Fail if unique id not in master list
		self._uid = uid
		# Fail if connector does not have required functions
		members = dir(connector)
		assert 'send' in members
		assert 'poll' in members
		assert 'subscribe' in members
		self._conn = connector
		self._alive = False # Controls polling event loop
		self._period = 0.001 # Update period in seconds
		self._subscriptions = [] # List of uids to listen to besides own

	def start(self,echo=False):
		''' Starts the polling thread '''
		self._birthday = time.clock()
		self._echo = echo
		self.subscribe('@'+self._uid)
		# Set thread to live and start
		self._alive = True
		poll_thread = Thread(target=self._poll)
		poll_thread.start()
		self.send(Msg.STARTED)
		try:
			self._after_start()
		except AttributeError:
			pass

	def stop(self):
		''' Public access to stop the polling loop '''
		self._on_stop()

	def send(self,topic,data=None):
		''' Sends a message string to the connector '''
		try:
			self._conn.send(pack(self._uid,topic,data))
		except AssertionError as e:
			self.err('Uid or topic invalid '+repr(e))

	def send_to(self,uid,topic,data=''):
		''' Sends a message string targeted for a specific client or service '''
		''' The connector bears responsibility for proper routing '''
		try:
			self._conn.send(pack('@'+uid,topic,data))
		except AssertionError as e:
			self.err('Uid or topic invalid '+repr(e))

	def subscribe(self,topic):
		''' Keep a list of subscriptions and set in connector'''
		self._conn.subscribe(topic)
		self._subscriptions.append(topic)

	def err(self,msg):
		self.send(Msg.ERR,msg)

	def _interpret(self,msg):
		''' 
		Attempts to parse the incoming packet 
		Calls a function based on the msg content
		'''
		parts = unpack(msg)
		if parts is None: 
			self.err('Malformed message ['+msg+'], found '+str(len(parts))+' of minimum 2 arguments')
			return False

		uid,topic,data = parts # Data may equal None

		try:
			if uid == '@'+self._uid:
				try:
					getattr(self,'_on_'+topic)(data)
				except AttributeError as e:
					self.err('No interpretation of message ['+msg+'] available')
					return False
			elif uid in self._subscriptions:
				try:
					getattr(self,'_on_'+uid+'_'+topic)(data)
				except AttributeError:
					return False
		except Exception as e:
			self.err('Exception thrown\n'+traceback.format_exc())
			return False
		return True

	def _poll(self):
		''' Run in its own thread '''
		while self._alive == True:
			# Loop through all new available messages
			msgs = self._conn.poll(uid=self._uid,wait_s=self._period)
			for msg in msgs: 
				# Process each message
				if self._interpret(msg) == False:
					# Echo back out if can't consume it and _echo is set
					if self._echo == True: self._conn.send(msg)
			try:
				self._poll_event()
			except AttributeError:
				pass

	def _on_marco(self,data=None):
		self.send(Msg.POLO)

	def _on_stop(self,data=None):
		try:
			self._before_stop()
		except AttributeError:
			pass
		self._alive = False
		self.send(Msg.STOPPING)

	def _on_uptime(self,data=None):
		self.send(Msg.UPTIME,str(time.clock() - self._birthday))

	def _on_set_period(self,data=None):
		try:
			self._period = float(data)
			return
		except ValueError:
			pass
		except TypeError:
			pass
		self.err('Failed to set period, could not interpret ['+repr(data)+'] as float')


if __name__ == '__main__': # Make a test server, start client, quit
	
	script = [
		'@test marco',
		'@test set_period 1',
		'@test uptime',
		'@test uptime',
		'@test set_period 0.1',
		'@test uptime',
		'@test uptime',
		'@test throw error',
		'@test stop'
	]

	Piece(Uid.TEST,ScriptConnector(script)).start()