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
import serial, threading, struct, platform

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
        self._pnp_action_gcode = [
            "PNP_FEEDER",
            "PNP_CAM",
            "PNP_RIG",
            "PNP_VALVE",
        ]

    def on_after_startup(self):
        self._logger.info(50*"#")
        self._logger.info("OpusPnP Plugin Started")
        self._logger.info(50*"#")
        self.connect_serial()

    def connect_serial(self):
        try:
            # self.ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
            if platform.system() == "Windows":
                self.ser = serial.Serial('COM19', 9600, timeout=1)
            else:
                self.ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
                # self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
            # self.ser = serial.Serial('COM19', 9600, timeout=1)
            self.keep_running = True
            self.recv_thread = threading.Thread(target=self.recv_data)
            self.recv_thread.start()
            self._logger.info("Connected to the serial port")
        except serial.SerialException as e:
            self._logger.error(f"Error: {e}\nCould not connect to the serial port")

    def disconnect_serial(self):
        self.keep_running = False
        if self.recv_thread is not None:
            self.recv_thread.join()
        if self.ser is not None:
            self.ser.close()
            self.ser = None

    def on_shutdown(self):
        self.disconnect_serial()

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
            feeder_next_X = 0,
            feeder_next_Y = 0,
            feeder_pick_X = 0,
            feeder_pick_Y = 0,
            feeder_next_Z = 0,
            feeder_pick_Z = 0,
            feeder_place_Z = 0,
            feeder_home_Z = 0,
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
            send_angle=["angle"],
            send_uart=["message"],
            toggle_uart_connection=[],
            fetch_next_XY=[],
            fetch_next_Z=[],
            fetch_pick_XY=[],
            fetch_pick_Z=[],
            fetch_place_Z=[],
            fetch_home_Z=[],
        )
    
    def get_printhead_position(self):
        return self._printer.get_current_data()["currentZ"]
    
    def set_printhead_z_position(self, pos_id):
        pnp_z_pos_list = ["Z0", "Z1", "Z2", "Z3"]
        if pos_id in pnp_z_pos_list:
            if pos_id == "Z0":
                # Move to Z0 position
                z_val = self._settings.get_float(["feeder_home_Z"])
            elif pos_id == "Z1":
                # Move to Z1 position
                z_val = self._settings.get_float(["feeder_next_Z"])
            elif pos_id == "Z2":
                # Move to Z2 position
                z_val = self._settings.get_float(["feeder_pick_Z"])
            elif pos_id == "Z3":
                # Move to Z3 position
                z_val = self._settings.get_float(["feeder_place_Z"])

            self._printer.commands(f"G0 Z{z_val}")
    
    def on_api_command(self, command, data):
        if command == "send_angle":
            angle = float(data["angle"])
            self.send_angle_data(angle)
        elif command == "send_uart":
            message = int(data["message"])
            self.send_data(message)

        elif command == "toggle_uart_connection":
            self._logger.info("Toggling connection from existing: {}".format(self.ser))
            if self.ser is None:
                self.connect_serial()
                self._plugin_manager.send_plugin_message(self._identifier, dict(connectionStatus=True))
            else:
                self.disconnect_serial()
                self._plugin_manager.send_plugin_message(self._identifier, dict(connectionStatus=False))
        
        elif command == "fetch_next_XY":
            # pos = self._printer.get_current_data()["currentZ"]
            pos = self.get_printhead_position()
            if pos is not None:
                # TODO: Write XY position to settings
                x = pos.get("x", 0.0)
                y = pos.get("y", 0.0)
                self._settings.set(["feeder_next_X"], x)
                self._settings.set(["feeder_next_Y"], y)
                self._settings.save()
            else:
                # TODO: Handle when no position is available
                ...
        
        elif command == "fetch_next_Z":
            pos = self.get_printhead_position()
            if pos is not None:
                z = pos.get("z", 0.0)
                self._settings.set(["feeder_next_Z"], z)
                self._settings.save()
            else:
                ...
        
        elif command == "fetch_pick_XY":
            pos = self.get_printhead_position()
            if pos is not None:
                x = pos.get("x", 0.0)
                y = pos.get("y", 0.0)
                self._settings.set(["feeder_pick_X"], x)
                self._settings.set(["feeder_pick_Y"], y)
                self._settings.save()
            else:
                ...
        
        elif command == "fetch_pick_Z":
            pos = self.get_printhead_position()
            if pos is not None:
                z = pos.get("z", 0.0)
                self._settings.set(["feeder_pick_Z"], z)
                self._settings.save()
            else:
                ...
                
        elif command == "fetch_place_Z":
            pos = self.get_printhead_position()
            if pos is not None:
                z = pos.get("z", 0.0)
                self._settings.set(["feeder_place_Z"], z)
                self._settings.save()
            else:
                ...
        
        elif command == "fetch_home_Z":
            pos = self.get_printhead_position()
            if pos is not None:
                z = pos.get("z", 0.0)
                self._settings.set(["feeder_home_Z"], z)
                self._settings.save()
            else:
                ...


    def send_data(self, message):
        if self.ser is not None:
            self.ser.write(f"{message}\n".encode())
            self._logger.info(f"Sent data: {message}")
    
    def send_angle_data(self, angle):
        if self.ser is not None:
            self.ser.write(f"301 {angle}\n".encode())
            self._logger.info(f"Sent data: 301 {angle}")
    
    def recv_data(self):
        while self.keep_running:
            if self.ser is not None and self.ser.in_waiting > 0:
                try:
                    data = self.ser.readline().decode().strip()
                    if data.startswith("status"):
                        valve_state, rig_state = struct.unpack('??', data[7:].encode())
                        self._logger.info("Received status: valveState={}, rigState={}".format(valve_state, rig_state))
                        self.update_ui(valve_state, rig_state)
                    elif data.startswith("RESUME"):
                        self._logger.info("Received RESUME")
                        # Resume Printer Execution using M108 command
                        self._printer.commands("M108")
                    else:
                        self._logger.info("Received data: {}".format(data))
                except Exception as e:
                    self._logger.error("Failed to read data: {}".format(e))

    def update_ui(self, valve_state, rig_state):
        # TODO: Update UI not working
        self._plugin_manager.send_plugin_message(self._identifier, dict(valveState=valve_state, rigState=rig_state))

                

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
                "repo": "thesis-opuspnp-plugin",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/sanskarbiswal/thesis-opuspnp-plugin/archive/{target_version}.zip",
            }
        }
    
    # def process_gcode(self, comm, line, *args, **kwargs):
    #     self._logger.info(f"Received line: {line}")
    def on_gcode_received(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        first_word = cmd.strip().split(" ")[0]
        if first_word == "PNP_VALVE":
            valve_state = cmd.strip().split(" ")[1]
            if valve_state == "1":
                self.send_data(101)
                self.update_ui(True, None)
            else:
                self.send_data(100)
                # self.update_ui(False, None)
        elif first_word == "PNP_RIG":
            cmd_state = cmd.strip().split(" ")[1]
            if cmd_state == "1":
                self.send_data(201)
            elif cmd_state == "0":
                self.send_data(200)
            elif cmd_state == "ROT":
                angle = cmd.strip().split(" ")[2]
                self.send_angle_data(angle)
            elif cmd_state == "Z0":
                # TODO: Move to Z0 position from settings
                self.set_printhead_z_position("Z0")
            elif cmd_state == "Z1":
                # TODO: Move to Z1 position from settings
                self.set_printhead_z_position("Z1")
            elif cmd_state == "Z2":
                # TODO: Move to Z2 position from settings
                self.set_printhead_z_position("Z2")
            elif cmd_state == "Z3":
                # TODO: Move to Z3 position from settings
                self.set_printhead_z_position("Z3")
        
        elif first_word == "PNP_PAUSE":
            # Pause Execution for 5s
            # TODO: Add 2nd word with value for S from GCODE
            # self._logger.info("Pausing Printer Execution")
            # Pause Printer Execution by sending M0 command
            self._printer.commands("G4 S5")

        elif first_word == "PNP_FEEDER":
            second_word = cmd.strip().split(" ")[1]
            third_word = cmd.strip().split(" ")[2]  # Feeder ID
            if second_word == "PICK":
                # TODO: Move to pick X Y location at Z0 height
                x = self._settings.get_float(["feeder_pick_X"])
                y = self._settings.get_float(["feeder_pick_Y"])
                x_new = x + (int(third_word)-1)*self._settings.get_float(["feeder_offset"])
                self._printer.commands(f"G0 X{x_new} Y{y}")

            elif second_word == "NEXT":
                # TODO: Move to feeder-next X Y location at Z0 height
                x = self._settings.get_float(["feeder_next_X"])
                y = self._settings.get_float(["feeder_next_Y"])
                x_new = x + (int(third_word)-1)*self._settings.get_float(["feeder_offset"])
                self._printer.commands(f"G0 X{x_new} Y{y}")
                self._logger.info(f"Moving to Feeder {third_word} at X={x_new}, Y={y}")

        elif first_word == "PNP_CAM":
            second_word = cmd.strip().split(" ")[1]
            # TODO: Implementation for Computer Vision
            # Cases = START, MOVE, CAPTURE, FIX {angle}, END



# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "OpusPnP"


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
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.sending": __plugin_implementation__.on_gcode_received
    }
