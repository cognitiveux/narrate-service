"use strict";

Dropzone.autoDiscover = false;

var file_uuid = "";
var validationFailed = false;

var conservationMediaDropzone = new Dropzone("#dropzonejs_conservation_media", {
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
                            conservationMediaDropzone.removeFile(file);
                        }
                        else {
                            conservationMediaDropzone.processQueue();
                        }
                    };
                    img.src = event.target.result;
                };
                reader.readAsDataURL(file);
            } 
            else {
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
                conservationMediaDropzone.removeFile(file);
            }
        });
    },
    autoProcessQueue: false,
    paramName: "file_src ",
    maxFiles: max_conservation_media_files,
    maxFilesize: 100 * max_conservation_media_files,
    addRemoveLinks: true,
    accept: function (file, done) {
        done();
    },
    params: {
        "media_id": $("#conservation_photos_uuid").val(),
        "type": "conservation"
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