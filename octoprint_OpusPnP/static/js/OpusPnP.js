/*
 * View model for OpusPnP
 *
 * Author: Sanskar Biswal
 * License: AGPLv3
 */
$(function() {

    self.uartValue = "";
    self.angleValue = "";


    // function OpuspnpViewModel(parameters) {
    //     var self = this;

    //     // assign the injected parameters, e.g.:
    //     // self.loginStateViewModel = parameters[0];
    //     self.settingsViewModel = parameters[0];

    //     // TODO: Implement your plugin's view model here.
    // }

    // /* view model class, parameters for constructor, container to bind to
    //  * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
    //  * and a full list of the available options.
    //  */
    // OCTOPRINT_VIEWMODELS.push({
    //     construct: OpuspnpViewModel,
    //     // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
    //     dependencies: [ "settingsViewModel"/* "loginStateViewModel", "settingsViewModel" */ ],
    //     // Elements to bind to, e.g. #settings_plugin_OpusPnP, #tab_plugin_OpusPnP, ...
    //     elements: [ /* ... */ ]
    // });
    OCTOPRINT_VIEWMODELS.push({
        construct: function() {
            OctoPrint.socket.onMessage("plugin.OpusPnP", function(message) {
                console.log(message);
                // handlePluginMessage(message.plugin, message.data);
            });
        }
    });
    console.log("OpusPnP JS Loaded");

    function handlePluginMessage(plugin, data) {
        // if (plugin !== "uart_communication") {
        //     return;
        // }
        if (data.valveState !== undefined) {
            $("#toggle-actuator").prop("checked", data.valveState);
        }
        if (data.rigState !== undefined) {
            $("#toggle-rig").prop("checked", data.rigState);
        }
        if (data.connectionStatus !== undefined) {
            $("#toggle_uart").prop("checked", data.connectionStatus);
        }
    }

    function sendUARTCommand() {
        var message = $("#uart_message").val();
        self.uartValue = message;
        OctoPrint.simpleApiCommand("OpusPnP", "send_uart", { "message": message });
    }

    function sendAngleCommand() {
        var angle = $("#angle_input").val();
        self.angleValue = angle;
        OctoPrint.simpleApiCommand("OpusPnP", "send_angle", { "angle": angle });
    }

    function toggle_uart_connection() {
        var port = $("#port_dropdown").val();
        // OctoPrint.simpleApiCommand("OpusPnP", "toggle_uart_connection", { "port": port });
        // getConnectionStatus();
        $.ajax({
            url: BASEURL+"plugin/OpusPnP/toggle_uart_connection",
            type: "POST",
            data: JSON.stringify({ "port": port }),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(response) {
                getConnectionStatus();
            },
            error: function(response) {
                console.log(response);
            }
        });
    }

    $("#send_uart_message").click(sendUARTCommand);
    $("#send_angle_input").click(sendAngleCommand);
    $("#toggle_uart_connection").click(toggle_uart_connection);

    $("#fetch_next_XY").click(function() {
        OctoPrint.simpleApiCommand("OpusPnP", "fetch_next_XY");
    });

    $("#fetch_next_Z").click(function() {
        OctoPrint.simpleApiCommand("OpusPnP", "fetch_next_Z");
    });

    $("#fetch_pick_XY").click(function() {
        OctoPrint.simpleApiCommand("OpusPnP", "fetch_pick_XY");
    });

    $("#fetch_pick_Z").click(function() {
        OctoPrint.simpleApiCommand("OpusPnP", "fetch_pick_Z");
    });

    $("#fetch_place_Z").click(function() {
        OctoPrint.simpleApiCommand("OpusPnP", "fetch_place_Z");
    });

    $("#fetch_home_Z").click(function() {
        OctoPrint.simpleApiCommand("OpusPnP", "fetch_home_Z");
    });

    $("#refresh_ports").click(function() {
        refreshPorts();
    });

    // Subscribe to plugin messages
    // OctoPrint.coreui.viewmodels.settingsViewModel.pluginMessages.subscribe(function(message) {
    //     console.log(message);
    //     handlePluginMessage(message.plugin, message.data);
    // });
    OctoPrint.socket.onMessage("plugin.OpusPnP", function(message) {
        console.log(message);
    });

    // COM Port Controls
    function refreshPorts() {
        $.get(BASEURL+"plugin/OpusPnP/ports", function(response){
            ret_val = response;
            console.log(ret_val);
            var ports = $("#port_dropdown");
            ports.empty();
            ret_val.forEach(function(port) {
                ports.append($("<option></option>").attr("value", port).text(port));
            });
        });
        // OctoPrint.simpleApiCommand("OpusPnP", "get_ports");
    }
    
    function getConnectionStatus() {
        $.get(BASEURL+"plugin/OpusPnP/get_connection_status", function(response){
            ret_val = response;
            $("#toggle_uart").prop("checked", ret_val);
        });
    }

    function getToolStatus() {
        connected = $("#toggle_uart").prop("checked");
        console.log(connected);
        if (!connected) {
            return;
        }
        $.get(BASEURL+"plugin/OpusPnP/get_tool_status", function(response){
            ret_val = response;
            vState = ret_val.valve_state;
            $("#toggle-actuator").prop("checked", ret_val.valve_state);
            $("#toggle-rig").prop("checked", ret_val.rig_state);
        });
    }

    refreshPorts();
    getConnectionStatus();
    setInterval(getToolStatus, 10000); // 10 seconds - 10000 ms
});
