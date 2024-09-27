"use strict";

var btnSubmitID = $("#sign_up_submit")[0];

var signup = function () {
    var actions = function () {
        var form = $("#sign_up_form");

        form.on("submit", function (e) {
            e.preventDefault();

            if (this.checkValidity() === false) {
                e.stopPropagation();
            }
            else {
                btnSubmitID.disabled = true;

                $("#password").removeClass("is-invalid");
                $("#confirm-password").removeClass("is-invalid");

                var password = $("#password").val();
                var confirmPassword = $("#confirm-password").val();
                var isValid = true;

                if (password.length < 8) {
                    $("#password").addClass("is-invalid");
                    isValid = false;
                }

                if (password !== confirmPassword) {
                    $("#confirm-password").addClass("is-invalid");
                    isValid = false;
                }

                if (!isValid) {
                    btnSubmitID.disabled = false;
                    return false;
                }

                var xhrRegister = new XMLHttpRequest();
                var response = {};

                xhrRegister.addEventListener("readystatechange", function () {
                    if (xhrRegister.readyState !== 4) return;

                    if (xhrRegister.status >= 200 && xhrRegister.status < 300) {
                        Swal.fire({
                            text: "Account has been successfully created!",
                            icon: "success",
                            buttonsStyling: false,
                            confirmButtonText: "Okay, got it!",
                            customClass: {
                                confirmButton: "btn btn-primary"
                            },
                            timer: 2000
                        });

                        setTimeout(function () {
                            response = JSON.parse(xhrRegister.responseText);
                            location.href = "/backend/activate_account/";
                        }, 2000);
                    }
                    else {
                        response = JSON.parse(xhrRegister.responseText);

                        if (response["already_exists_fields"].includes("email")) {
                            btnSubmitID.disabled = false;
                            Swal.fire({
                                text: "The email is already in use. Please try a different one.",
                                icon: "error",
                                buttonsStyling: false,
                                confirmButtonText: "Okay, got it!",
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                }
                            });
                            $("#email").addClass("is-invalid");
                        }
                        else {
                            btnSubmitID.disabled = false;
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

                xhrRegister.onerror = () => {
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

                xhrRegister.open("POST", "/backend/account-management/register_user/", true);

                let formData = new FormData();
                formData.append("email", $("#email").val());
                formData.append("password", $("#password").val());
                formData.append("organization", $("#organization").val());
                formData.append("name", $("#first-name").val());
                formData.append("surname", $("#last-name").val());

                xhrRegister.send(formData);
            }
        });
    }

    return {
        init: function () {
            actions();
        }
    };
}();