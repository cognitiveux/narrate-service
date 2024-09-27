"use strict";

Dropzone.autoDiscover = false;

var file_uuid = "";
var validationFailed = false;

var videosMediaDropzone = new Dropzone("#dropzonejs_videos_media", {
    url: "/backend/file-management/media/temp/add/",
    init: function () {
        this.on("success", function (file, response) {
            file_uuid = response["resource_obj"]["uuid"];
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
            if (!validationFailed) {
                deleteTempFile(file.upload.filename);
            }
            validationFailed = false;
        });
        this.on("addedfile", function(file) {
            if (file.type.match(/^video\/(mp4|webm|ogg|avi|mov|wmv|flv)$/i)) {
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
                            videosMediaDropzone.removeFile(file);
                        }
                        else {
                            videosMediaDropzone.processQueue();
                        }
                    };
                };
                reader.readAsDataURL(file);
            } else {
                Swal.fire({
                    text: "Invalid file type. Only videos are allowed.",
                    icon: "error",
                    buttonsStyling: false,
                    confirmButtonText: "Okay, got it!",
                    customClass: {
                        confirmButton: "btn btn-primary"
                    }
                });
                validationFailed = true;
                videosMediaDropzone.removeFile(file);
            }
        });
    },
    autoProcessQueue: false,
    paramName: "file_src ",
    maxFiles: max_videos_media_files,
    maxFilesize: 100 * max_videos_media_files,
    addRemoveLinks: true,
    accept: function (file, done) {
        done();
    },
    params: {
        "media_id": $("#videos_uuid").val(),
        "type": "video"
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