"use strict";

var btnSubmitID = $("#request_reset_code_submit")[0];
var pollIntervalID = "";

var pollResetStatus = function (email) {
    var xhrPollStatus = new XMLHttpRequest();
    var responsePollStatus = "";

    xhrPollStatus.onreadystatechange = function () {
        if (xhrPollStatus.readyState !== 4) return;

        if (xhrPollStatus.status >= 200 && xhrPollStatus.status < 300) {
            responsePollStatus = JSON.parse(xhrPollStatus.responseText);

            if (responsePollStatus["task_status"] === "FAILURE") {
                btnSubmitID.disabled = false;
                Swal.fire({
                    text: "Unable to request reset code via email. Please try again later.",
                    icon: "error",
                    buttonsStyling: false,
                    confirmButtonText: "Okay, got it!",
                    customClass: {
                        confirmButton: "btn btn-primary"
                    }
                });
                clearInterval(pollIntervalID);
            }

            if (responsePollStatus["task_status"] === "SUCCESS") {
                btnSubmitID.disabled = false;
                Swal.fire({
                    text: "Request reset code via email has been successfully completed! Please follow the instructions on the email.",
                    icon: "success",
                    buttonsStyling: false,
                    confirmButtonText: "Okay, got it!",
                    customClass: {
                        confirmButton: "btn btn-primary"
                    }
                });
                clearInterval(pollIntervalID);
            }   
        }
        else {
            btnSubmitID.disabled = false;
            responsePollStatus = JSON.parse(xhr1.responseText);
            Swal.fire({
                text: responsePollStatus["message"],
                icon: "error",
                buttonsStyling: false,
                confirmButtonText: "Okay, got it!",
                customClass: {
                    confirmButton: "btn btn-primary"
                }
            });
        }
    };

    xhrPollStatus.onerror = () => {
        btnSubmitID.disabled = false;
        Swal.fire({
            text: "Unable to communicate with the server. Please try again later.",
            icon: "error",
            buttonsStyling: false,
            confirmButtonText: "Okay, got it!",
            customClass: {
                confirmButton: "btn btn-primary"
            }
        });
    };
    xhrPollStatus.open("GET", "/backend/account-management/poll_reset_email_status?email=" +  email, true);
    xhrPollStatus.send();
}

var forgot_password = function () {
    var actions = function () {
        var form = $("#request_reset_code_form");

        form.on("submit", function (e) {
            e.preventDefault();

            if (this.checkValidity() === false) {
                e.stopPropagation();
            }
            else {
                btnSubmitID.disabled = true;

                var xhrRequestReset = new XMLHttpRequest();
                var response = {};

                xhrRequestReset.addEventListener("readystatechange", function () {
                    if (xhrRequestReset.readyState !== 4) return;

                    if (xhrRequestReset.status >= 200 && xhrRequestReset.status < 300) {
                        response = JSON.parse(xhrRequestReset.responseText);
                        pollIntervalID = setInterval(() => {
                            pollResetStatus($("#email").val());
                        }, 500);
                    }
                    else {
                        response = JSON.parse(xhrRequestReset.responseText);
                        btnSubmitID.disabled = false;
                        Swal.fire({
                            text: response["message"],
                            icon: "error",
                            buttonsStyling: false,
                            confirmButtonText: "Okay, got it!",
                            customClass: {
                                confirmButton: "btn btn-primary"
                            }
                        });
                    }
                });

                xhrRequestReset.onerror = () => {
                    btnSubmitID.disabled = false;
                    Swal.fire({
                        text: "Unable to communicate with the server. Please try again later.",
                        icon: "error",
                        buttonsStyling: false,
                        confirmButtonText: "Okay, got it!",
                        customClass: {
                            confirmButton: "btn btn-primary"
                        }
                    });
                };

                xhrRequestReset.open("POST", "/backend/account-management/request_password_reset_code/", true);

                let formData = new FormData();
                formData.append("email", $("#email").val());

                xhrRequestReset.send(formData);
            }
        });
    }

    return {
        init: function () {
            actions();
        }
    };
}();