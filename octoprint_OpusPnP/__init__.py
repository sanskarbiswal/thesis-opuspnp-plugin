# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin
import flask
import serial, threading

class OpuspnpPlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.SimpleApiPlugin
):
    
    def __init__(self):
        self.ser = None
        self.recv_thread = None
        self.keep_running = False

    def on_after_startup(self):
        self._logger.info(50*"#")
        self._logger.info("OpusPnP Plugin Started")
        self._logger.info(50*"#")
        try:
            # self.ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
            self.ser = serial.Serial('COM19', 9600, timeout=1)
            self.keep_running = True
            self.recv_thread = threading.Thread(target=self.recv_data)
            self.recv_thread.start()
            self._logger.info("Connected to the serial port")
        except serial.SerialException as e:
            self._logger.error(f"Error: {e}\nCould not connect to the serial port")

    def on_shutdown(self):
        self.keep_running = False
        if self.recv_thread is not None:
            self.recv_thread.join()
        if self.ser is not None:
            self.ser.close()

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
            feeder_X = 0,
            feeder_Y = 0,
            feeder_next_Z = 0,
            feeder_pick_Z = 0,
            feeder_offset = 0,
            camera_X = 0,
            camera_Y = 0,
            camera_Z = 0,
        )

    ##~~ AssetPlugin mixin
    def get_template_configs(self):
        return [
            # dict(
            #     type="generic",
            #     custom_bindings=True,
            #     template="OpusPnP_tab.jinja2",
            # ),
            dict(
                type="settings",
                custom_bindings=False
            )
        ]

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/OpusPnP.js"],
            "css": ["css/OpusPnP.css"],
            "less": ["less/OpusPnP.less"]
        }

    ##~~ Softwareupdate hook
    def get_api_commands(self):
        return dict(
            send_actuator=["value"],
            send_rig=["value"],
            send_uart=["message"]
        )
    
    def on_api_command(self, command, data):
        self._logger.info(f"Received command: {command}, with data: {data}")
        if command == "send_actuator":
            value = "ON" if data["value"] else "OFF"
            flask.jsonify(response=f"Actuator is now {value}")
            self._logger.info("Actuator is now %s" % value)
        elif command == "send_rig":
            value = "ON" if data["value"] else "OFF" 
        elif command == "send_uart":
            message = int(data["message"])
            self.send_data(message)

    def send_data(self, message):
        if self.ser is not None:
            self.ser.write(f"{message}\n".encode())
            self._logger.info(f"Sent data: {message}")
    
    def recv_data(self):
        while self.keep_running:
            if self.ser.in_waiting > 0 and self.ser is not None:
                data = self.ser.readline().decode().strip()
                self._logger.info(f"Received data: {data}")
                

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "OpusPnP": {
                "displayName": "Opuspnp Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "sanskarbiswal",
                "repo": "OpusPnP_plugin",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/sanskarbiswal/OpusPnP_plugin/archive/{target_version}.zip",
            }
        }
    
    def process_gcode(self, comm, line, *args, **kwargs):
        self._logger.info(f"Received line: {line}")


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Opuspnp Plugin"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = OpuspnpPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.ui.tab": __plugin_implementation__.get_template_configs,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
