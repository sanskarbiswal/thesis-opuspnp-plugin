/*
 * View model for OpusPnP
 *
 * Author: Sanskar Biswal
 * License: AGPLv3
 */
$(function() {

    self.ActuatorState = false;
    self.RigState = false;
    self.uartValue = "";


    function OpuspnpViewModel(parameters) {
        var self = this;

        // assign the injected parameters, e.g.:
        // self.loginStateViewModel = parameters[0];
        // self.settingsViewModel = parameters[1];

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

    function sendActuator() {
        var value = $("#toggle-actuator").is(":checked");
        self.ActuatorState = value;
        OctoPrint.simpleApiCommand("OpusPnP", "send_actuator", { "value": value });
    }

    function sendRig() {
        var value = $("#toggle-rig").is(":checked");
        self.RigState = value;
        OctoPrint.simpleApiCommand("OpusPnP", "send_rig", { "value": value });
    }

    function sendUARTCommand() {
        var message = $("#uart_message").val();
        self.uartValue = message;
        console.log(self.uartValue);
        OctoPrint.simpleApiCommand("OpusPnP", "send_uart", { "message": message });
    }

    $("#send_actuator").click(sendActuator);
    $("#send_rig").click(sendRig);
    $("#send_uart_message").click(sendUARTCommand);
});
