"use strict";

function updateSecurityDetails(targetURL, form) {
    var response = {};

    var xhr = new XMLHttpRequest();
    xhr.addEventListener("readystatechange", function () {
        if (xhr.readyState !== 4) {
            return;
        }
        response = JSON.parse(xhr.responseText);

        if (xhr.status >= 200 && xhr.status < 300) {
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
                location.href = baseURL + "/dashboard";
            }, 2000);
        } else {
            if (xhr.status === 422) {
                Swal.fire({
                    text: "The Existing Password you provided is not correct. Please try again.",
                    icon: "error",
                    buttonsStyling: false,
                    confirmButtonText: "Okay, got it!",
                    customClass: {
                        confirmButton: "btn btn-primary"
                    }
                });
            }
            else {
                Swal.fire({
                    text: "Something went wrong. Please try again later.",
                    icon: "error",
                    buttonsStyling: false,
                    confirmButtonText: "Okay, got it!",
                    customClass: {
                        confirmButton: "btn btn-primary"
                    }
                });
            }
        }
    });

    xhr.onerror = () => {
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
    xhr.open("POST", baseURL + targetURL, true);
    xhr.setRequestHeader("Content-Type", "application/json");

    const jsonData = {
        current_password: $("#oldPasswordInput").val(),
        new_password: $("#newPasswordInput").val(),
    }
    xhr.send(JSON.stringify(jsonData));
}

var btnSubmitID = $("#holder_update_security_submit")[0];
var targetURL = "/account-management/update_password/";

var UPDATE_SECURITY = function () {
    var actions = function () {
        var form = $("#holder_update_security_form");

        form.on("submit", function (e) {
            e.preventDefault();
            btnSubmitID.disabled = true;
            $("#oldPasswordInput").removeClass("is-invalid");
            $("#newPasswordInput").removeClass("is-invalid");
            $("#confirmNewPasswordInput").removeClass("is-invalid");

            var invalidFields = $(form).find(":invalid");

            if (this.checkValidity() === false) {
                e.stopPropagation();
                var invalidField = this.querySelector(":invalid");

                if (invalidField) {
                    invalidField.focus();
                }
                btnSubmitID.disabled = false;
                invalidFields.each(function () {
                    $("#"+this.id).addClass("is-invalid");
                });
            } else {
                var password = $("#newPasswordInput").val();
                var confirmPassword = $("#confirmNewPasswordInput").val();
                var isValid = true;

                if (password.length < 8) {
                    $("#newPasswordInput").addClass("is-invalid");
                    isValid = false;
                }

                if (password !== confirmPassword) {
                    $("#confirmNewPasswordInput").addClass("is-invalid");
                    isValid = false;
                }

                if (!isValid) {
                    btnSubmitID.disabled = false;
                    return false;
                }

                setTimeout(function () {
                    updateSecurityDetails(targetURL, form[0]);
                    btnSubmitID.disabled = false;
                }, 1000);
            }
        });
    }

    return {
        init: function () {
            actions();
        }
    };
}();