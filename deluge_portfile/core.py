# -*- coding: utf-8 -*-
# Copyright (C) 2024 Martin Dagarin <martin.dagarin@gmail.com>
#
# Basic plugin template created by the Deluge Team.
#
# This file is part of portfile and is licensed under GNU GPL 3.0, or later,
# with the additional special exception to link portions of this program with
# the OpenSSL library. See LICENSE for more details.
from __future__ import unicode_literals

import logging

import deluge.configmanager
from deluge.core.rpcserver import export
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import os
from twisted.internet.task import LoopingCall

log = logging.getLogger(__name__)

DEFAULT_PREFS = {
    'enabled': False,
    'port_listen_file': 'port_listen',
    'enable_monitor_port': True,
    'monitor_port_interval': 300,
    'enable_monitor_file': True,
    'monitor_file_interval': 120,
}

class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager('portfile.conf', DEFAULT_PREFS)
        self.monitor_port_timer = LoopingCall(self.on_check_port)
        self.monitor_file_timer = LoopingCall(self.on_check_file)

        self.enable_monitor()

    def disable(self):
        self.disable_monitor()

    def update(self):
        pass

    def enable_monitor(self):
        if not self.config['enabled']:
            return
        
        # Enable monitor file timer
        if self.monitor_file_timer is not None and not self.monitor_file_timer.running and self.config['enable_monitor_file']:
            log.debug('Monitor file timer started')
            self.monitor_file_timer.start(self.config['monitor_file_interval'])

        # Enable monitor port timer
        if self.monitor_port_timer is not None and not self.monitor_port_timer.running and self.config['enable_monitor_port']:
            log.debug('Monitor listen port timer started')
            self.monitor_port_timer.start(self.config['monitor_port_interval'])

    def disable_monitor(self):
        # Disable monitor file timer
        if self.monitor_file_timer is not None and self.monitor_file_timer.running:
            log.debug('Monitor file timer stoped')
            self.monitor_file_timer.stop()

        # Disable monitor port timer
        if self.monitor_port_timer is not None and self.monitor_port_timer.running:
            log.debug('Monitor listen port timer stop')
            self.monitor_port_timer.stop() 

    #
    #   On check port handler
    #
    def on_check_port(self):
        log.debug('Run check port')
        core = component.get('Core')
        core.test_listen_port().addCallback(self.cb_check_listen_port)
    
    #
    #   Handle result of listen port test
    #
    def cb_check_listen_port(self, is_open):
        if not is_open:
            self.change_listen_port()

    #
    #   On check file handler
    #
    def on_check_file(self):
        log.debug('Run check port file')
        self.change_listen_port()
    
    #
    #   Change listening port
    #
    def change_listen_port(self):
        core = component.get('Core')
        current_port = core.get_listen_port()
        new_port = self.get_port_from_file()
        if new_port is not None and current_port != new_port:
            # Change configuration
            core.set_config({'listen_ports': [new_port, new_port]})

            # Reannounce all torrents
            torrents = core.get_session_state()
            core.force_reannounce(torrents)

            log.info(f'Updating listening port from {current_port} to {new_port}')

    #
    #   Get port from text file
    #
    def get_port_from_file(self):
        if self.config['port_listen_file'] is None or len(self.config['port_listen_file']) < 1 or not os.path.exists(self.config['port_listen_file']):
            return None
        with open(self.config['port_listen_file'], 'r') as file:
            try:
                port = int(file.read().strip())
                return port
            except:
                return None
        return None

    @export
    def check_file_path(self, path = None):
        is_not_ok = path is None or len(path.strip()) < 1 or not os.path.exists(path)
        return not is_not_ok

    @export
    def set_config(self, config):
        # Check if config has changed
        config_changed = False
        for key in config:
            if self.config[key] != config[key]:
                config_changed = True
                break
        
        # Stop all operations
        if config_changed:
            self.disable_monitor()

        # Apply new values    
        for key in config:
            self.config[key] = config[key]
        self.config.save()

        # Resume all operations
        if config_changed:
            self.enable_monitor()

    @export
    def get_config(self):
        return self.config.config
