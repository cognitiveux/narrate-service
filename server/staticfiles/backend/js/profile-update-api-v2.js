"use strict";

Dropzone.autoDiscover = false;

var file_uuid = "";

var MediaDropzone = new Dropzone("#dropzonejs_temp_media", {
    url: "/backend/file-management/media/temp/add/",
    init: function () {
        this.on("success", function (file, response) {
            file_uuid = response["resource_obj"]["uuid"];
            $("#new_media_uuid").val(file_uuid);

            Swal.fire({
                text: "Upload of temporary media has been successfully completed!",
                icon: "success",
                buttonsStyling: false,
                confirmButtonText: "Okay, got it!",
                customClass: {
                    confirmButton: "btn btn-primary"
                },
                timer: 2000
            });
        });
        this.on("error", function (file, response) {
            $("#new_media_uuid").val("");
            Swal.fire({
                text: "Something went wrong. Please try again later.",
                icon: "error",
                buttonsStyling: false,
                confirmButtonText: "Okay, got it!",
                customClass: {
                    confirmButton: "btn btn-primary"
                }
            });
        });
        this.on("removedfile", function (file) {
            if (file_uuid != "") {
                $("#new_media_uuid").val("");
                deleteTempFile(file.upload.filename);
            }
        });
    },
    paramName: "file_src ",
    maxFiles: 1,
    maxFilesize: 100, // MB
    addRemoveLinks: true,
    accept: function (file, done) {
        done();
    },
    params: {
        "media_id": $("#mediaTypeUuidInput").val(),
        "type": "profile_pic"
    },
    renameFile: function (file) {
        var new_filename = uuidv4() + "_" + file.name;
        return new_filename;
    },
});

function deleteTempFile(file_uuid_param) {
    const params = "?file_id=" + file_uuid_param;
    const targetURL = "/file-management/media/temp/delete/";

    var xhr = new XMLHttpRequest();
    xhr.addEventListener("readystatechange", function () {
        if (xhr.readyState !== 4) {
            return;
        }

        if (xhr.status >= 200 && xhr.status < 300) {
            file_uuid = "";
            Swal.fire({
                text: "Deletion of temporary media has been successfully completed!",
                icon: "success",
                buttonsStyling: false,
                confirmButtonText: "Okay, got it!",
                customClass: {
                    confirmButton: "btn btn-primary"
                },
                timer: 2000
            });
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
    xhr.open("DELETE", baseURL + targetURL + params, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send();
}

function updateProfileDetails(targetURL, form) {
    var response = {};

    var xhr = new XMLHttpRequest();
    xhr.addEventListener("readystatechange", function () {
        if (xhr.readyState !== 4) {
            return;
        }
        response = JSON.parse(xhr.responseText);

        if (xhr.status >= 200 && xhr.status < 300) {
            Swal.fire({
                text: "Profile details have been successfully updated!",
                icon: "success",
                buttonsStyling: false,
                confirmButtonText: "Okay, got it!",
                customClass: {
                    confirmButton: "btn btn-primary"
                },
                timer: 2000
            });
            setTimeout(function () {
                location.href = baseURL + "/profile";
            }, 2000);
        } else {
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
        name: $("#nameInput").val(),
        surname: $("#surnameInput").val(),
        telephone: $("#telephoneInput").val(),
        media_type_id: $("#mediaTypeUuidInput").val(),
        type: "profile_pic",
    }
    xhr.send(JSON.stringify(jsonData));
}

var btnSubmitID = $("#holder_update_profile_submit")[0];
var targetURL = "/account-management/update_profile/";

var UPDATE_PROFILE = function () {
    var actions = function () {
        var form = $("#holder_update_profile_form");
    
        form.on("submit", function (e) {
            e.preventDefault();
            btnSubmitID.disabled = true;
            $("#nameInput").removeClass("is-invalid");
            $("#surnameInput").removeClass("is-invalid");

            var invalidFields = $(form).find(":invalid");

            if (this.checkValidity() === false) {
                e.stopPropagation();
                var invalidField = this.querySelector(":invalid");

                if (invalidField) {
                    invalidField.focus();
                }
                btnSubmitID.disabled = false;
            } else {
                setTimeout(function () {
                    btnSubmitID.disabled = false;
                    updateProfileDetails(targetURL, form[0]);
                }, 1000);
            }

            invalidFields.each(function () {
                $("#"+this.id).addClass("is-invalid");
            });
        });
    }

    return {
        init: function () {
            actions();
        }
    };
}();