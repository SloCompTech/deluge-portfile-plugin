/**
 * Script: portfile.js
 *     The client-side javascript code for the portfile plugin.
 *
 * Copyright:
 *     (C) Martin Dagarin 2024 <martin.dagarin@gmail.com>
 *
 *     This file is part of portfile and is licensed under GNU GPL 3.0, or
 *     later, with the additional special exception to link portions of this
 *     program with the OpenSSL library. See LICENSE for more details.
 */

portfilePlugin = Ext.extend(Deluge.Plugin, {
    constructor: function(config) {
        config = Ext.apply({
            name: 'portfile'
        }, config);
        portfilePlugin.superclass.constructor.call(this, config);
    },

    onDisable: function() {
        deluge.preferences.removePage(this.prefsPage);
    },

    onEnable: function() {
        this.prefsPage = deluge.preferences.addPage(
            new Deluge.ux.preferences.portfilePage());
    }
});
new portfilePlugin();
