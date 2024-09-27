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
            } 
            else if (file.type.match(/^video\/(mp4|webm|ogg|avi|mov|wmv|flv)$/i)) {
                var reader = new FileReader();
                reader.onload = function(event) {
                    const video = document.createElement("video");
                    video.src = event.target.result;

                    video.onloadedmetadata = function() {
                        const width = video.videoWidth;
                        const height = video.videoHeight;

                        if (width < minWidth || height < minHeight) {
                            Swal.fire({
                                text: "Video dimensions must be at least " + minWidth + "x" + minHeight + " pixels.",
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
                };
                reader.readAsDataURL(file);
            }
            else {
                Swal.fire({
                    text: "Invalid file type. Only images/videos are allowed.",
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
    maxFiles: max_media_files,
    maxFilesize: 100 * max_media_files, // MB
    addRemoveLinks: true,
    accept: function (file, done) {
        done();
    },
    params: {
        "media_id": $("#mediaTypeUuidInput").val()
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

function uploadNewMediaTreasure(targetURL, form) {
    var response = {};

    var xhr = new XMLHttpRequest();
    xhr.addEventListener("readystatechange", function () {
        if (xhr.readyState !== 4) {
            return;
        }
        response = JSON.parse(xhr.responseText);

        if (xhr.status >= 200 && xhr.status < 300) {
            Swal.fire({
                text: "Media for Ecclesiastical Treasure has been successfully uploaded!",
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
        media_type_id: $("#mediaTypeUuidInput").val(),
        type: $("#mediaTypeInput").find(":selected").val(),
    }
    xhr.send(JSON.stringify(jsonData));
}

var btnSubmitID = $("#holder_upload_new_media_treasure_submit")[0];
var targetURL =  "/ecclesiastical-treasures/media/upload_new/";

var UPLOAD_NEW_MEDIA_TREASURE = function () {
    var actions = function () {
        var form = $("#holder_upload_new_media_treasure_form");

        $("#holder_upload_new_media_treasure_submit").on("click", function (e) {
            e.preventDefault();
            btnSubmitID.disabled = true;
            var invaliMediaType = false;
            var invalidFile = false;

            $("#mediaTypeInput").removeClass("is-invalid");
            $("#holder_add_temp_media").removeClass("is-invalid");
            $("#dropzonejs_temp_media").css("border-color", "");

            if ($("#mediaTypeInput").val() === "") {
                invaliMediaType = true;
            }

            if ($("#new_media_uuid").val() === "") {
                invalidFile = true;
            }

            if (invaliMediaType && invalidFile) {
                $("#mediaTypeInput").addClass("is-invalid");
                $("#holder_add_temp_media").addClass("is-invalid");
                $("#dropzonejs_temp_media").css("border-color", "var(--bs-form-invalid-border-color)");
                $("#mediaTypeInput").focus();
                btnSubmitID.disabled = false;
                return false;
            }
            else if (invaliMediaType) {
                $("#mediaTypeInput").addClass("is-invalid");
                $("#mediaTypeInput").focus();
                btnSubmitID.disabled = false;
                return false;
            }
            else if (invalidFile) {
                $("#holder_add_temp_media").addClass("is-invalid");
                $("#dropzonejs_temp_media").css("border-color", "var(--bs-form-invalid-border-color)");
                $("#holder_add_temp_media").focus();
                btnSubmitID.disabled = false;
                return false;
            }
            else {
                $("#mediaTypeInput").removeClass("is-invalid");
                $("#holder_add_temp_media").removeClass("is-invalid");
                $("#dropzonejs_temp_media").css("border-color", "");

                setTimeout(function () {
                    btnSubmitID.disabled = false;
                    uploadNewMediaTreasure(targetURL, form[0]);
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