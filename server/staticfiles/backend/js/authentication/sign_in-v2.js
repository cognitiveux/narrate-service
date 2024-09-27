"use strict";

var btnSubmitID = $("#sign_in_submit")[0];

var signin = function () {
    var actions = function () {
        var form = $("#sign_in_form");

        form.on("submit", function (e) {
            e.preventDefault();

            if (this.checkValidity() === false) {
                e.stopPropagation();
            }
            else {
                btnSubmitID.disabled = true;

                var xhrLogin = new XMLHttpRequest();
                var response = {};

                xhrLogin.addEventListener("readystatechange", function () {
                    if (xhrLogin.readyState !== 4) return;

                    if (xhrLogin.status >= 200 && xhrLogin.status < 300) {
                        setTimeout(function () {
                            response = JSON.parse(xhrLogin.responseText);
                            location.href = response["next_url"];
                        }, 250);
                    }
                    else if (xhrLogin.status == 403) {
                        btnSubmitID.disabled = false;
                        Swal.fire({
                            text: "Your account is not activated yet. Please activate it before you login.",
                            icon: "warning",
                            buttonsStyling: false,
                            confirmButtonText: "Okay, got it!",
                            customClass: {
                                confirmButton: "btn btn-primary"
                            }
                        });
                    }
                    else {
                        btnSubmitID.disabled = false;
                        Swal.fire({
                            text: "Wrong credentials, please try again.",
                            icon: "error",
                            buttonsStyling: false,
                            confirmButtonText: "Okay, got it!",
                            customClass: {
                                confirmButton: "btn btn-primary"
                            }
                        });
                    }
                });

                xhrLogin.onerror = () => {
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

                xhrLogin.open("POST", "/backend/account-management/login/", true);

                let formData = new FormData(); 
                formData.append("email", $("#email").val()); 
                formData.append("password", $("#password").val());
                formData.append("organization", $("#organization").val());

                xhrLogin.send(formData);
            }
        });
    }

    return {
        init: function () {
            actions();
        }
    };
}();