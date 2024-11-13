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

from gi.repository import Gtk

import deluge.component as component
from deluge.plugins.pluginbase import Gtk3PluginBase
from deluge.ui.client import client
import os

from .common import get_resource

log = logging.getLogger(__name__)


class Gtk3UI(Gtk3PluginBase):
    def enable(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('config.ui'))

        component.get('Preferences').add_page(
            'portfile', self.builder.get_object('portfile_box'))
        component.get('PluginManager').register_hook(
            'on_apply_prefs', self.on_apply_prefs)
        component.get('PluginManager').register_hook(
            'on_show_prefs', self.on_show_prefs)
        
        self.builder.get_object('portfile_listen_port_file_path_entry').connect('changed', self.on_port_file_path_changed)
        

    def disable(self):
        component.get('Preferences').remove_page('portfile')
        component.get('PluginManager').deregister_hook(
            'on_apply_prefs', self.on_apply_prefs)
        component.get('PluginManager').deregister_hook(
            'on_show_prefs', self.on_show_prefs)

    def on_port_file_path_changed(self, widget):
        value = widget.get_text()

        def cb_path_check(result):
            if not result:
                widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, 'gtk-dialog-error')
            else:
                widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, None)

        client.portfile.check_file_path(value).addCallback(cb_path_check)
        
        return True

    def on_apply_prefs(self):
        log.debug('applying prefs for portfile')
        config = {
            'enabled': self.builder.get_object('portfile_enabled_checkbutton').get_active(),
            'port_listen_file': self.builder.get_object('portfile_listen_port_file_path_entry').get_text().strip(),
            'enable_monitor_port': self.builder.get_object('portfile_monitor_port_checkbutton').get_active(),
            'monitor_port_interval': self.builder.get_object('portfile_monitor_port_interval_spinbutton').get_value_as_int(),
            'enable_monitor_file': self.builder.get_object('portfile_monitor_file_checkbutton').get_active(),
            'monitor_file_interval': self.builder.get_object('portfile_monitor_file_spinbutton').get_value_as_int(),
        }
        client.portfile.set_config(config)

    def on_show_prefs(self):
        client.portfile.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        self.builder.get_object('portfile_enabled_checkbutton').set_active(config['enabled'])
        self.builder.get_object('portfile_listen_port_file_path_entry').set_text(config['port_listen_file'])
        self.builder.get_object('portfile_monitor_port_checkbutton').set_active(config['enable_monitor_port'])
        self.builder.get_object('portfile_monitor_port_interval_spinbutton').set_value(config['monitor_port_interval']),
        self.builder.get_object('portfile_monitor_file_checkbutton').set_active(config['enable_monitor_file'])
        self.builder.get_object('portfile_monitor_file_spinbutton').set_value(config['monitor_file_interval']),
