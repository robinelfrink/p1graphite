#!/usr/bin/env python


import argparse
import crcmod.predefined
import re
import serial
import socket
import time


parser = argparse.ArgumentParser(description='Read DSMR P1 telegrams and send them to Graphite')
parser.add_argument('-d', '--debug', dest='debug', action='store_true', default=False, help='Debug mode')
parser.add_argument('-p', '--port', dest='port', default='/dev/ttyUSB0', help='Serial port')
parser.add_argument('-b', '--baudrate', dest='baudrate', type=int, default='115200', help='Serial port baudrate')
parser.add_argument('-H', '--host', dest='host', default='localhost', help='Graphite host')
parser.add_argument('-g', '--gport', dest='gport', default=2003, help='Graphite port')
parser.add_argument('--prefix', dest='prefix', default='', help='Graphite prefix')
args = parser.parse_args()


prefix = re.sub(r'^(.+)$', r'\1.', args.prefix)
crc16 = crcmod.predefined.mkPredefinedCrcFun('crc16')


if args.debug:
	print 'Opening serial port %s' % args.port
tty = serial.Serial()
tty.baudrate = args.baudrate
tty.bytesize = serial.EIGHTBITS
tty.parity = serial.PARITY_NONE
tty.stopbits = serial.STOPBITS_ONE
tty.xonxoff = 1
tty.rtscts = 0
tty.timeout = 12
tty.port = args.port


def get_telegram(port):
	telegram = []
	checksum = None
	while not checksum:
		line = port.readline().strip()
		if args.debug:
			print ' > %s' % line
		if re.match(r'^/', line):
			telegram = []
		elif re.match(r'^!(.*)', line):
			checksum = int(line[1:], 16)
		telegram.append(line)
	if args.debug:
		print 'Checksum: %s' % checksum
	crc = crc16('\r\n'.join(telegram[:-1]) + '\r\n!')
	if crc == checksum:
		if args.debug:
			print 'Checksum matches'
		return telegram
	return None


def parse_telegram(telegram):
	data = {}
	pattern = r'^([0-9]-([0-4]):([0-9]+\.[0-9]+\.[0-9]+))\(([^\)]+)\)(\(([^\)]+)\))?$'
	for line in telegram:
		match = re.match(pattern, line)
		if match:
			name = None
			value = float(re.sub(r'[^0-9\.].*', '', match.group(4)))
			if match.group(1)=='1-0:1.8.1':
				name = 'power.delivered.tariff1'
			elif match.group(1)=='1-0:1.8.2':
				name = 'power.delivered.tariff2'
			elif match.group(1)=='1-0:2.8.1':
				name = 'power.received.tariff1'
			elif match.group(1)=='1-0:2.8.2':
				name = 'power.received.tariff2'
			elif match.group(1)=='0-0:96.14.0':
				name = 'power.tariff'
			elif match.group(1)=='0-0:96.7.21':
				name = 'power.failures'
			elif match.group(1)=='0-0:96.7.9':
				name = 'power.longfailures'
			elif match.group(1)=='1-0:32.32.0':
				name = 'power.sags.l1'
			elif match.group(1)=='1-0:52.32.0':
				name = 'power.sags.l2'
			elif match.group(1)=='1-0:72:32.0':
				name = 'power.sags.l3'
			elif match.group(1)=='1-0:32.36.0':
				name = 'power.swells.l1'
			elif match.group(1)=='1-0:52.36.0':
				name = 'power.swells.l2'
			elif match.group(1)=='1-0:72.36.0':
				name = 'power.swells.l3'
			elif match.group(1)=='1-0:31.7.0':
				name = 'power.current.l1'
			elif match.group(1)=='1-0:51.7.0':
				name = 'power.current.l2'
			elif match.group(1)=='1-0:71.7.0':
				name = 'power.current.l3'
			elif match.group(1)=='1-0:21.7.0':
				name = 'power.active.l1.plus'
			elif match.group(1)=='1-0:41.7.0':
				name = 'power.active.l2.plus'
			elif match.group(1)=='1-0:61.7.0':
				name = 'power.active.l3.plus'
			elif match.group(1)=='1-0:22.7.0':
				name = 'power.active.l1.minus'
			elif match.group(1)=='1-0:42.7.0':
				name = 'power.active.l2.minus'
			elif match.group(1)=='1-0:62.7.0':
				name = 'power.active.l3.minus'
			elif match.group(1)[:1]=='0' and match.group(3)=='24.2.1':
				# Assuming gas for now...
				name = 'gas.delivered'
				value = float(re.sub(r'[^0-9\.].*', '', match.group(6)))
			if name:
				data[name] = value
	return data


def send_data(data):
	if args.debug:
		print 'Sending data to Graphite...'
	now = int(time.time())
	messages = []
	try:
		sock = socket.socket()
		sock.connect((args.host, args.gport))
		for name in data:
			messages.append('%s%s %f %d' % (prefix, name, data[name], now))
		if args.debug:
			print '< ' + '\n< '.join(messages)
		sock.sendall('\n'.join(messages) + '\n')
	except Exception as e:
		print 'Socket exception: %s' % e
	finally:
		sock.close()


try:
	tty.open()
	while True:
		telegram = get_telegram(tty)
		if telegram:
			data = parse_telegram(telegram)
			send_data(data)
except serial.SerialException as e:
	print 'Serial port error: %s' % e
