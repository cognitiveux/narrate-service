"use strict";

function fetchTreasuresMedia() {
    const params = "?treasure_id=" + getUrlParameter("treasure_id");
    var response = {};
    var xhr = new XMLHttpRequest();
    $("#datatable_treasures_media tbody").css("filter", "blur(1.0rem)");

    xhr.addEventListener("readystatechange", function () {
        if (xhr.readyState !== 4) return;

        response = JSON.parse(xhr.responseText);

        if (xhr.status >= 200 && xhr.status < 300) {
            const data = response["resource_array"];
            TreasuresMediaDatatable.init(data);
        } else {
            response = JSON.parse(xhr.responseText);
            Swal.fire({
                text: "There was an error loading data. Please try again later.",
                icon: "error",
                buttonsStyling: false,
                confirmButtonText: "Okay, got it!",
                customClass: {
                    confirmButton: "btn btn-primary"
                }
            });
        }
        setTimeout(() => {
            $("#filterArea").css("filter", "none");
            $("#datatable_treasures_media tbody").css("filter", "none");
        }, 500);
    });

    xhr.onerror = () => {
        setTimeout(() => {
            $("#filterArea").css("filter", "none");
            $("#datatable_treasures_media tbody").css("filter", "none");
        }, 500);
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

    xhr.open("GET", baseURL + "/ecclesiastical-treasures/media/list/" + params, true);
    xhr.send();
}

var TreasuresMediaDatatable = function () {
    var dt;

    var initDatatable = function (data) {
        dt = $("#datatable_treasures_media").DataTable({
            language: {
                search: "Search within results:"
            },
            responsive: true,
            searchDelay: 500,
            bDestroy: true,
            data: data,
            columns: [
                {
                    title: "Media UUID",
                    data: "uuid",
                },
                {
                    title: "Media File",
                    data: "thumbnail",
                    render: function (data, type, row) {
                        return "<img src=" + row["thumbnail"] + " width=50 height=50 />";
                    },
                },
                {
                    title: "Media Type",
                    data: "media_type",
                },
                {
                    title: "Actions",
                    data: null,
                    orderable: false,
                    render: function (data, type, row) {
                        if (row["is_editable"] == true) {
                            return `
                                    <a class="btn btn-outline-secondary" href="` + baseURL + row["file_src"] + `" target="_blank">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye" viewBox="0 0 16 16">
                                            <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8M1.173 8a13 13 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5s3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5s-3.879-1.168-5.168-2.457A13 13 0 0 1 1.172 8z"/>
                                            <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5M4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0"/>
                                        </svg>
                                    </a>

                                    <a class="btn btn-outline-secondary" href="` + baseURL + "/treasures/media/update?treasure_id=" + getUrlParameter("treasure_id") + "&media_id=" + row["uuid"] + `" data-treasure-uuid="` + row["uuid"] + `">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pencil" viewBox="0 0 16 16">
                                            <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325"/>
                                        </svg>
                                    </a>

                                    <a class="btn btn-outline-danger" href="` + baseURL + "/treasures/media/delete?treasure_id=" + getUrlParameter("treasure_id") + "&media_id=" + row["uuid"] + `" data-treasure-uuid="` + row["uuid"] + `">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                                            <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
                                            <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
                                        </svg>
                                    </a>
                                `;
                        }
                        else {
                            return `
                                    <a class="btn btn-outline-secondary" href="` + baseURL + row["file_src"] + `" target="_blank">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye" viewBox="0 0 16 16">
                                            <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8M1.173 8a13 13 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5s3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5s-3.879-1.168-5.168-2.457A13 13 0 0 1 1.172 8z"/>
                                            <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5M4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0"/>
                                        </svg>
                                    </a>
                                `;
                        }
                    },
                },
            ]
        });
    }

    return {
        init: function (data) {
            initDatatable(data);
        }
    }
}();

function uploadNewPhotosTreasurePage() {
    location.href = baseURL + "/treasures/media/add/?treasure_id=" + getUrlParameter("treasure_id");
}

$(document).ready(function () {
    fetchTreasuresMedia();
});