import os
from os import listdir
from os.path import isfile, join

mypath = os.path.dirname(__file__)+'/..'

onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath,f))]

with open(mypath+'/wtfj/protocol/uid.py','w') as uids:
	print('-------------------------')
	print('Generating uids in uid.py')
	print('-------------------------')
	for line in onlyfiles:
		print(line)
		parts = line.split('.')
		uid = parts[0]
		uid_val = uid.upper()+' = \''+uid+'\'\n'
		uids.write(uid_val)

from protocol import uid as Uid
from protocol import req as Req
from protocol import msg as Msg
from protocol import mode as Mode
from protocol import tcp as Tcp

def print_bar(msg,top=True):
	bar = ''
	for char in msg:
		bar += '-'
	if top is True: print(bar)
	print(msg)
	print(bar)

def get_uid(piece):
	''' Returns id based on class name '''
	return piece.__class__.__name__.lower()

def get_attr(class_to_check):
	''' Returns strings of a class' members '''
	return [getattr(class_to_check,member) for member in dir(class_to_check) 
		if '__' not in member]

print_bar('Importing all identifiers in protocol')

valid = [Uid,Req,Msg,Mode,Tcp]
for v in valid:
	print_bar('Importing ids for ['+v.__name__+']')
	for name in dir(v):
		if '__' not in name:
			print(name)