"use strict";

Dropzone.autoDiscover = false;

var file_uuid = "";
var validationFailed = false;

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
                if (!validationFailed) {
                    deleteTempFile(file.upload.filename);
                }
                validationFailed = false;
            }
        });
        this.on("addedfile", function(file) {
            if (file.type.match(/image.*/)) {
                var reader = new FileReader();
                reader.onload = function(event) {
                    var img = new Image();
                    img.onload = function() {
                        if (img.width < minWidth || img.height < minHeight) {
                            Swal.fire({
                                text: "Image dimensions must be at least " + minWidth + "x" + minHeight + " pixels.",
                                icon: "error",
                                buttonsStyling: false,
                                confirmButtonText: "Okay, got it!",
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                }
                            });
                            validationFailed = true;
                            MediaDropzone.removeFile(file);
                        }
                        else {
                            MediaDropzone.processQueue();
                        }
                    };
                    img.src = event.target.result;
                };
                reader.readAsDataURL(file);
            } else {
                Swal.fire({
                    text: "Invalid file type. Only images are allowed.",
                    icon: "error",
                    buttonsStyling: false,
                    confirmButtonText: "Okay, got it!",
                    customClass: {
                        confirmButton: "btn btn-primary"
                    }
                });
                validationFailed = true;
                MediaDropzone.removeFile(file);
            }
        });
    },
    autoProcessQueue: false,
    paramName: "file_src ",
    maxFiles: 1,
    maxFilesize: 100, // MB
    addRemoveLinks: true,
    accept: function (file, done) {
        done();
    },
    params: {
        "media_id": $("#mediaTypeUuidInput").val(),
        "type": $("#mediaTypeInput").val()
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

function updateMediaTreasure(targetURL, form) {
    var response = {};

    var xhr = new XMLHttpRequest();
    xhr.addEventListener("readystatechange", function () {
        if (xhr.readyState !== 4) {
            return;
        }
        response = JSON.parse(xhr.responseText);

        if (xhr.status >= 200 && xhr.status < 300) {
            Swal.fire({
                text: "Media of Ecclesiastical Treasure has been successfully updated!",
                icon: "success",
                buttonsStyling: false,
                confirmButtonText: "Okay, got it!",
                customClass: {
                    confirmButton: "btn btn-primary"
                },
                timer: 2000
            });
            setTimeout(function () {
                location.href = baseURL + "/treasures/media/?treasure_id=" + form.elements["treasureUuidInput"].value;
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
        treasure_id: form.elements["treasureUuidInput"].value,
        old_media_id: form.elements["mediaUuidInput"].value,
        new_media_id: $("#new_media_uuid").val(),
    }
    xhr.send(JSON.stringify(jsonData));
}


var btnSubmitID = $("#holder_update_media_treasure_submit")[0];
var targetURL = "/ecclesiastical-treasures/media/update/";

var UPDATE_MEDIA_TREASURE = function () {
    var actions = function () {
        var form = $("#holder_update_media_treasure_form");

        $("#holder_update_media_treasure_submit").on("click", function (e) {
            e.preventDefault();
            btnSubmitID.disabled = true;
            var invalidFile = false;

            $("#holder_add_temp_media").removeClass("is-invalid");
            $("#dropzonejs_temp_media").css("border-color", "");

            if ($("#new_media_uuid").val() === "") {
                invalidFile = true;
            }

            if (invalidFile) {
                $("#holder_add_temp_media").addClass("is-invalid");
                $("#dropzonejs_temp_media").css("border-color", "var(--bs-form-invalid-border-color)");
                $("#holder_add_temp_media").focus();
                btnSubmitID.disabled = false;
                return false;
            }
            else {
                $("#holder_add_temp_media").removeClass("is-invalid");
                $("#dropzonejs_temp_media").css("border-color", "");

                setTimeout(function () {
                    btnSubmitID.disabled = false;
                    updateMediaTreasure(targetURL, form[0]);
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