"use strict";

var btnSubmitID = $("#reset_password_submit")[0];

var reset_password = function () {
    var actions = function () {
        var form = $("#reset_password_form");

        form.on("submit", function (e) {
            e.preventDefault();

            if (this.checkValidity() === false) {
                e.stopPropagation();
            }
            else {
                btnSubmitID.disabled = true;

                $("#password").removeClass("is-invalid");

                var password = $("#password").val();
                var isValid = true;

                if (password.length < 8) {
                    $("#password").addClass("is-invalid");
                    isValid = false;
                }

                if (!isValid) {
                    btnSubmitID.disabled = false;
                    return false;
                }

                var xhrResetPassword = new XMLHttpRequest();
                var response = {};

                xhrResetPassword.addEventListener("readystatechange", function () {
                    if (xhrResetPassword.readyState !== 4) return;

                    if (xhrResetPassword.status >= 200 && xhrResetPassword.status < 300) {
                        response = JSON.parse(xhrResetPassword.responseText);
                        btnSubmitID.disabled = false;
                        Swal.fire({
                            text: "Password has been successfully updated!",
                            icon: "success",
                            buttonsStyling: false,
                            confirmButtonText: "Okay, got it!",
                            customClass: {
                                confirmButton: "btn btn-primary"
                            },
                            timer: 2000
                        });
                        setTimeout(function () {
                            response = JSON.parse(xhrResetPassword.responseText);
                            location.href = "/backend/login/";
                        }, 2000);
                    }
                    else {
                        response = JSON.parse(xhrResetPassword.responseText);
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

                xhrResetPassword.onerror = () => {
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

                xhrResetPassword.open("POST", "/backend/account-management/reset_password/", true);

                let formData = new FormData();
                formData.append("email", $("#email").val());
                formData.append("password", $("#password").val());
                formData.append("reset_code", $("#reset-code").val());

                xhrResetPassword.send(formData);
            }
        });
    }

    return {
        init: function () {
            actions();
        }
    };
}();