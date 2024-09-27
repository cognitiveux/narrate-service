"use strict";

var btnSubmitID = $("#activate_account_submit")[0];

var activate_account = function () {
    var actions = function () {
        var form = $("#activate_account_form");

        form.on("submit", function (e) {
            e.preventDefault();

            if (this.checkValidity() === false) {
                e.stopPropagation();
            }
            else {
                btnSubmitID.disabled = true;

                var xhrActivateAccount = new XMLHttpRequest();
                var response = {};

                xhrActivateAccount.addEventListener("readystatechange", function () {
                    if (xhrActivateAccount.readyState !== 4) return;

                    if (xhrActivateAccount.status >= 200 && xhrActivateAccount.status < 300) {
                        response = JSON.parse(xhrActivateAccount.responseText);
                        var is_activated = response["resource_is_activated"];
                        var is_already_activated = response["resource_is_already_activated"];

                        if (is_already_activated) {
                            btnSubmitID.disabled = false;
                            Swal.fire({
                                text: "Account is already activated.",
                                icon: "info",
                                buttonsStyling: false,
                                confirmButtonText: "Okay, got it!",
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                },
                                timer: 2000
                            });
    
                            setTimeout(function () {
                                response = JSON.parse(xhrActivateAccount.responseText);
                                location.href = "/backend/login/";
                            }, 2000);
                        }
                        else if (is_activated) {
                            btnSubmitID.disabled = false;
                            Swal.fire({
                                text: "Account has been successfully activated!",
                                icon: "success",
                                buttonsStyling: false,
                                confirmButtonText: "Okay, got it!",
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                },
                                timer: 2000
                            });

                            setTimeout(function () {
                                response = JSON.parse(xhrActivateAccount.responseText);
                                location.href = "/backend/login/";
                            }, 2000);
                        }
                        else {
                            btnSubmitID.disabled = false;
                            Swal.fire({
                                text: "The provided information is incorrect. Please try again.",
                                icon: "error",
                                buttonsStyling: false,
                                confirmButtonText: "Okay, got it!",
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                }
                            });
                        }
                    }
                    else {
                        btnSubmitID.disabled = false;
                        Swal.fire({
                            text: "The provided information is incorrect. Please try again.",
                            icon: "error",
                            buttonsStyling: false,
                            confirmButtonText: "Okay, got it!",
                            customClass: {
                                confirmButton: "btn btn-primary"
                            }
                        });
                    }
                });

                xhrActivateAccount.onerror = () => {
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

                xhrActivateAccount.open("POST", "/backend/account-management/activate_account/", true);

                let formData = new FormData();
                formData.append("email", $("#email").val());
                formData.append("activation_code", $("#activation-code").val());

                xhrActivateAccount.send(formData);
            }
        });
    }

    return {
        init: function () {
            actions();
        }
    };
}();