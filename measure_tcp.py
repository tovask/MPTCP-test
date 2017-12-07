#!/usr/bin/python
"""
measuring program should be written in C for better performance
only measuring receiving bandwidth

refs:
https://docs.python.org/2/library/socket.html
https://docs.python.org/2/library/select.html
https://github.com/python/cpython/blob/a5293b4ff2c1b5446947b4986f98ecf5d52432d4/Modules/socketmodule.c
https://github.com/rvantonder/bandwidth-tester/blob/master/tcp/

TODO:
	- separate bandwidth and latency meter
	- option to use specific interface
	- compute headers length too
	- interrupt handler
	- are the variables used by the threads thread safe?

"""

import socket
import threading
import time
import re
import argparse

HOST = '' # Symbolic name meaning all available interfaces
PORT = 5001 # default listening/connecting port
DURATION = 10 # default testing time (seconds)
INTERVAL = 1 # default reporting frequency (seconds)
BUFFER_SIZE = 1024 # maximum send/receive data size


# Helper functions:
def safe_divide(num1, num2):
	# TODO return float('+/-Inf') if needed
	pass

def put_times_in_data(other_side_time, buffer_size):
	data = 'your_time('+str(other_side_time)+')my_time('+str(time.time())+')'
	if len(data) < buffer_size:
		data += 'A' * (buffer_size-len(data))
	else:
		# timestamps may will be cutted!
		data = data[:buffer_size]
	return data

def get_times_from_data(data):
	my_time = None
	other_side_time = None
	# the other side of the connection send my time back as 'your_time'
	m = re.search( r'your_time\(([\d.]+)\)', data)
	if m:
		my_time = float(m.group(1))
	# the other side of the connection send it's time as 'my_time'
	m = re.search( r'my_time\(([\d.]+)\)', data)
	if m:
		other_side_time = float(m.group(1))
	return (my_time, other_side_time)

def safe_send_all(clientsocket, data, verbose=False):
	"Send all the data, return True on success or False on failure"
	try:
		clientsocket.sendall(data)
	except socket.error, e:
		if(verbose): print 'Connection exception ('+str(e)+'), exiting'
		return False
	return True

def safe_recv_all(clientsocket, buffer_size, verbose=False):
	"Return the received data or None on failure"
	data = b''
	try:
		while len(data) < buffer_size:
			packet = clientsocket.recv(buffer_size - len(data))
			if not packet:
				if(verbose): print 'Connection closed, exiting'
				return None
			data += packet
	except socket.error, e:
		if(verbose): print 'Connection exception ('+str(e)+'), exiting'
		return None
	return data


class Reporter:
	def __init__(self, interval):
		self.interval = interval
		self.report_data_format = '%5.2f s | %14.2f bit/s | %2.6f s | %2.6f s'
		self.report_header_format = '%7s | %20s | %10s | %10s'
	
	def start(self):
		self.start_time = time.time()
		self.amount = 0
		self.two_delay_sum = 0.0
		self.two_delay_count = 0
		self.one_delay_sum = 0.0
		self.one_delay_count = 0
		self.last_report_time = time.time()
		self.last_amount = self.amount
		self.last_two_delay_sum = 0.0
		self.last_two_delay_count = 0
		self.last_one_delay_sum = 0.0
		self.last_one_delay_count = 0
	
	def add(self, plus_amount, self_measure_delay, both_measure_delay):
		self.amount += plus_amount
		# check if delay successfully determined
		if self_measure_delay!=None:
			self.two_delay_sum += self_measure_delay
			self.two_delay_count += 1
		if both_measure_delay!=None:
			self.one_delay_sum += both_measure_delay
			self.one_delay_count += 1
	
	def check(self):
		# check if interval time elapsed
		if(time.time() - self.last_report_time >= self.interval):
			self.print_state()
			self.refresh_state()
	
	def refresh_state(self):
		self.last_report_time = time.time()
		self.last_amount = self.amount
		self.last_two_delay_sum = self.two_delay_sum
		self.last_two_delay_count = self.two_delay_count
		self.last_one_delay_sum = self.one_delay_sum
		self.last_one_delay_count = self.one_delay_count
	
	def print_header(self):
		# print the colums names
		print self.report_header_format % ('time', 'bandwidth', 'delay', 'delay')
	
	def print_state(self):
		# time
		time_passed = (time.time() - self.start_time)
		# bandwidth
		bandwidth = (self.amount - self.last_amount) / (time.time() - self.last_report_time)
		# delay (avoid division by zero)
		delay_two = (self.two_delay_sum - self.last_two_delay_sum) / (self.two_delay_count - self.last_two_delay_count) if self.two_delay_count != self.last_two_delay_count else float('Inf')
		delay_one =  (self.one_delay_sum - self.last_one_delay_sum) / (self.one_delay_count - self.last_one_delay_count) if self.one_delay_count != self.last_one_delay_count else float('Inf')
		# print it
		print self.report_data_format % (time_passed, bandwidth, delay_two, delay_one)
		#sys.stdout.flush()
	
	def print_total(self):
		print '\nTOTAL AVERAGE:', "\n",
		# time
		time_passed = (time.time() - self.start_time)
		# bandwidth
		bandwidth = self.amount / (time.time() - self.start_time)
		# delay (avoid division by zero)
		delay_two = self.two_delay_sum / self.two_delay_count if self.two_delay_count != 0 else float('Inf')
		delay_one = self.one_delay_sum / self.one_delay_count if self.one_delay_count != 0 else float('Inf')
		# print it
		print self.report_data_format % (time_passed, bandwidth, delay_two, delay_one)

def continuous_sender(args):
	# running as a separate process and continuously send the data
	# (run asyncronuosly in order not to cause a delay and a long waiting queue for the receiving datas)
	while args.running:
		# create a buffer_size long  data
		data = 'A' * args.buffer_size
		if not safe_send_all(args.clientsocket, data, args.verbose):
			args.running = False

def continuous_receiver(args):
	# running as a separate process and continuously receive and analyze the data
	while args.running:
		data = safe_recv_all(args.clientsocket, args.buffer_size, args.verbose)
		if data==None:
			args.running = False
			break
		# add to the statistic
		args.report( len(data)*8, None, None) # multiply by 8 to get the bits count

def measure_bandwidth(args):
	# measure the connection's bandwidth by continuously sending and receiving data
	reporter = Reporter(args.interval)
	if(not args.quiet): reporter.print_header()
	reporter.start()
	start_time = time.time()
	
	# adding to the args for passing to the threads
	args.report = reporter.add
	args.running = True
	
	receiver_process = threading.Thread(target=continuous_receiver, args=(args,))
	sender_process = threading.Thread(target=continuous_sender, args=(args,))
	receiver_process.start()
	sender_process.start()
	
	# run until an exception occure or the duration expire
	while args.running and (args.run_infinity or ( time.time() - start_time <= args.duration ) ):
		time.sleep(0.1) # TODO precise
		reporter.check()
	
	# time's up
	args.running = False
	receiver_process.join()
	sender_process.join()
	
	if(not args.quiet): reporter.print_total()

def measure_latency(args):
	# measure the connection latency by sending timestamps and waiting for the response, then analyze it
	# important: no new data will be sent until the response received,
	#            so the sent data surely reached the other side
	#            and not hanging in the sending or receiving queue!!!
	reporter = Reporter(args.interval)
	if(not args.quiet): reporter.print_header()
	reporter.start()
	
	start_time = time.time()
	last_other_side_time = None
	
	if args.server: # someone should starts the ping-pong
		if not safe_send_all(args.clientsocket, put_times_in_data(last_other_side_time, args.buffer_size), args.verbose):
			return
	
	# run until an exception occure or the duration expire
	while args.run_infinity or ( time.time() - start_time <= args.duration ) :
		# receive the timestamps
		data = safe_recv_all(args.clientsocket, args.buffer_size, args.verbose)
		if data==None:
			break
		# get the timestamps from the data
		my_time, other_side_time = get_times_from_data(data)
		# check if timestamps successfully received
		my_delay = time.time()-my_time if (my_time!=None and my_time!=0) else None # in the beginning, the other side don't know our time and send a '0'
		other_side_delay = time.time()-other_side_time if (other_side_time!=None) else None
		# add to the statistic
		reporter.add( 0, my_delay, other_side_delay)
		# sometimes just part of the data received which isn't fully contains the timestamps
		# in that case we should avoid overwrite a valid value with a corrupt one
		last_other_side_time = other_side_time if other_side_time!=None else last_other_side_time
		
		# sending back the timestamps
		if not safe_send_all(args.clientsocket, put_times_in_data(last_other_side_time, args.buffer_size), args.verbose):
			break
		
		reporter.check()
	# time's up
	if(not args.quiet): reporter.print_total()

if __name__ == "__main__":
	host = HOST
	port = PORT
	parser = argparse.ArgumentParser(description='Measure TCP bandwidth or latency.')
	parser.add_argument("-s", "--server", action="store_true", help="run server mode")
	parser.add_argument("-c", "--client", action="store_true", help="run client mode (this is the default)")
	parser.add_argument("-a","--host", metavar='<host>', default=HOST, help="ip address or host name, default: "+repr(HOST))
	parser.add_argument("-p","--port", metavar='<port>', type=int, default=PORT, help="port number, default: "+repr(PORT))
	parser.add_argument("-w", "--bandwidth", action="store_true", help="measure bandwidth (this is the default)")
	parser.add_argument("-l", "--latency", action="store_true", help="measure latency")
	parser.add_argument("-t","--duration", metavar='time [s]', type=float, default=DURATION, help="testing duration (in seconds), 0 for infinity, default: "+repr(DURATION))
	parser.add_argument("-i","--interval", metavar='time [s]', type=float, default=INTERVAL, help="reporting interval (in seconds), default: "+repr(INTERVAL))
	parser.add_argument("-b","--buffer-size", metavar='bytes', type=int, default=BUFFER_SIZE, help="sending/receiving buffer size (in bytes), default: "+repr(BUFFER_SIZE))
	parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
	parser.add_argument("-q", "--quiet", action="store_true", help="only print interval statistic")
	args = parser.parse_args()
	
	args.run_infinity = (args.duration == 0)
	
	# the client and the server mode is almost the same
	# mainly they only differ in the connection setup
	# after connected, both handled in the same way
	
	# setup the connection
	try:
		if(args.server):
			if(args.verbose): print 'Running server'
			# creating an IPv4 TCP socket
			serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			if(args.verbose): print 'Socket created'
			serversocket.bind((args.host,args.port))
			serversocket.listen(0) # don't expect more than 1 client
			if(args.verbose): print 'Server now listening', serversocket.getsockname()
			# Waiting for client to connect
			clientsocket, client_addr = serversocket.accept()
		else:
			if(args.verbose): print 'Running client'
			# creating an IPv4 TCP socket
			clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			if(args.verbose): print 'Socket created'
			clientsocket.connect((args.host,args.port))
	except socket.error, e:
		if(args.verbose): print 'Error on connection setup:', e
		raise	# or do something more useful
	
	# from here, we have a connected socket 'clientsocket', what we want to measure
	
	if(args.verbose): print 'Client connected', clientsocket.getpeername()
	
	args.clientsocket = clientsocket
	
	if args.latency:
		measure_latency(args)
	else:
		measure_bandwidth(args)
	
	# measurement ends, close the sockets
	clientsocket.close()
	if(args.server):
		serversocket.shutdown(socket.SHUT_RDWR) # for faster recreate next time
		serversocket.close()
	
	if(args.verbose): print '\ntest ended'
