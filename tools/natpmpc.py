#!/usr/bin/python3
#
# Script to keep port-forwading active with natpmp
#
# Requirements:
# - sudo apt install libnatpmp
#

import logging
import re
import shlex
from subprocess import check_output, CalledProcessError, STDOUT, TimeoutExpired
import time

EXEC_PATH = 'natpmpc'
PORT_FILE = '/config/port_listen' # TODO: Change
PUBLIC_PORT = 1
PRIVATE_PORT = 0
LIFETIME_INTERVAL = 60
REFRESH_INTERVAL = 45
GATEWAY_ADDRESS = '10.2.0.1'
TIMEOUT = 2

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

current_ports = [None, None]

def parse_natpmpc_response(str):
  response = {}

  match_gateway = re.search(r'\busing gateway : ([0-9a-fA-F\.\:]+)\b', str)
  response['gateway'] = match_gateway.groups()[0] if match_gateway is not None else None

  match_publicip = re.search(r'\bPublic IP address : ([0-9a-fA-F\.\:]+)\b', str)
  response['public_ip'] = match_publicip.groups()[0] if match_publicip is not None else None

  match_port = re.search(r'\bMapped public port (\d{1,5}) protocol (\w{3}) to local port (\d{1,5}) lifetime (\d+)\b', str)
  response['proto'] = match_port.groups()[1] if match_port is not None else None
  response['public_port'] = int(match_port.groups()[0]) if match_port is not None else None
  response['private_port'] = int(match_port.groups()[2]) if match_port is not None else None

  return response

def refresh_port():
  # Refresh UDP port
  data_udp = None
  output_udp = None
  try:
    command = shlex.split(f'{EXEC_PATH} -a {shlex.quote(str(PUBLIC_PORT))} {shlex.quote(str(PRIVATE_PORT))} udp {shlex.quote(str(LIFETIME_INTERVAL))} -g {shlex.quote(GATEWAY_ADDRESS)}')
    output_udp = check_output(command, stderr=STDOUT, timeout=(TIMEOUT if TIMEOUT > 0 else None)).decode()
    data_udp = parse_natpmpc_response(output_udp)
  except CalledProcessError as e:
    output_udp = e.stdout.decode()
    log.warning('Refresh UDP port: error')
    log.warning(output_udp)
  except TimeoutExpired as e:
    output_udp = e.stdout.decode()
    log.warning('Refresh UDP port timedout')

  # Refresh TCP port
  data_tcp = None
  output_tcp = None
  try:
    command = shlex.split(f'{EXEC_PATH} -a {shlex.quote(str(PUBLIC_PORT))} {shlex.quote(str(PRIVATE_PORT))} tcp {shlex.quote(str(LIFETIME_INTERVAL))} -g {shlex.quote(GATEWAY_ADDRESS)}')
    output_tcp = check_output(command, stderr=STDOUT, timeout=(TIMEOUT if TIMEOUT > 0 else None)).decode()
    data_tcp = parse_natpmpc_response(output_tcp)
  except CalledProcessError as e:
    output_tcp = e.stdout.decode()
    log.warning('Refresh TCP port: error')
    log.warning(output_tcp)
  except TimeoutExpired as e:
    output_tcp = e.stdout.decode()
    log.warning('Refresh TCP port timedout')

  return (data_udp, data_tcp, output_udp, output_tcp)

if __name__ == '__main__':
  while True:
    data = refresh_port()
    new_udp_port = data[0]['public_port']
    new_tcp_port = data[1]['public_port']

    if new_udp_port != current_ports[0] or new_tcp_port != current_ports[1]:
      current_ports[0] = new_udp_port
      current_ports[1] = new_tcp_port

      # Write new port to file
      with open(PORT_FILE, 'w') as file:
        file.write(str(new_udp_port)) 
    time.sleep(REFRESH_INTERVAL)
