/*
 * View model for OpusPnP
 *
 * Author: Sanskar Biswal
 * License: AGPLv3
 */
$(function() {

    self.uartValue = "";
    self.angleValue = "";


    function OpuspnpViewModel(parameters) {
        var self = this;

        // assign the injected parameters, e.g.:
        // self.loginStateViewModel = parameters[0];
        self.settingsViewModel = parameters[0];

        // TODO: Implement your plugin's view model here.
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: OpuspnpViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ "settingsViewModel"/* "loginStateViewModel", "settingsViewModel" */ ],
        // Elements to bind to, e.g. #settings_plugin_OpusPnP, #tab_plugin_OpusPnP, ...
        elements: [ /* ... */ ]
    });
    // OCTOPRINT_VIEWMODELS.push({
    //     construct: function() {
    //         OctoPrint.socket.onMessage("plugin.OpusPnP", function(message) {
    //             console.log(message);
    //             // handlePluginMessage(message.plugin, message.data);
    //         });
    //     }
    // });
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

    $("#getFeederLoc").click(function() {
        // $.get(BASEURL+"plugin/OpusPnP/get_pos_feeder", function(response){
        //     // ret_val = response;
        // });
        $.ajax({
            url: BASEURL+"api/printer/command",
            type: "POST",
            data: JSON.stringify({ "command": "M114" }),
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                ret_val = response;
                console.log("Success" + response);
            },
            error: function(response) {
                console.log("Failure"+ response);
            }
        });
    });

    $("#getPickLoc").click(function() {
        $.get(BASEURL+"plugin/OpusPnP/get_pos_pick", function(response){
            // ret_val = response;
        });
    });

    $("#getCamLoc").click(function() {
        $.get(BASEURL+"plugin/OpusPnP/get_pos_cam", function(response){
            // ret_val = response;
        });
    });

    $("#fetch_place_Z").click(function() {
        $.get(BASEURL+"plugin/OpusPnP/fetch_place_Z", function(response){
            // ret_val = response;
        });
    });

    $("#fetch_home_Z").click(function() {
        $.get(BASEURL+"plugin/OpusPnP/fetch_home_Z", function(response){
            // ret_val = response;
        });
    });

    $("#refresh_ports").click(function() {
        refreshPorts();
    });

    $("#toggle_cv").click(function() {
        $.get(BASEURL+"plugin/OpusPnP/toggle_cv", function(response){
            ret_val = response.cv_status;
            if (ret_val === "success"){
                // Show CV Feed (Unhide)
                console.log("CV Feed: Display");
                $("#cv_feed").show();
            }else {
                // Hide CV Feed
                console.log("CV Feed: Hide");
                $("#cv_feed").hide();
            }
            // $("#toggle_cv").prop("checked", ret_val);
        });
    });

    $("#process_cv_frame").click(function() {
        var angle = $("#cv_target_angle").val();
        $.ajax({
            url: BASEURL+"plugin/OpusPnP/process_cv_frame",
            type: "POST",
            data: JSON.stringify({ "angle": angle }),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(response) {
                ret_val = response;
                var delta = ret_val.delta_angle;
                var angle = ret_val.current_angle;
                var offset = ret_val.offset;
                console.log("Delta Angle: " + delta, "Current Angle: " + angle, "Offset: " + offset);

            },
            error: function(response) {
                console.log(response);
            }
        });
    });

    // Subscribe to plugin messages
    // OctoPrint.coreui.viewmodels.settingsViewModel.pluginMessages.subscribe(function(message) {
    //     console.log(message);
    //     handlePluginMessage(message.plugin, message.data);
    // });
    OctoPrint.socket.onMessage("plugin.OpusPnP", function(message) {
        console.log("Opus Pluing Message"+ message);
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
