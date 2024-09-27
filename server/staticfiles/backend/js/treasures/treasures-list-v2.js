"use strict";

function fetchTreasures() {
    var response = {};
    var xhr = new XMLHttpRequest();
    $("#datatable_treasures tbody").css("filter", "blur(1.0rem)");

    xhr.addEventListener("readystatechange", function () {
        if (xhr.readyState !== 4) return;

        response = JSON.parse(xhr.responseText);

        if (xhr.status >= 200 && xhr.status < 300) {
            const data = response["resource_array"];
            TreasuresDatatable.init(data);
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
            $("#datatable_treasures tbody").css("filter", "none");
        }, 500);
    });

    xhr.onerror = () => {
        setTimeout(() => {
            $("#filterArea").css("filter", "none");
            $("#datatable_treasures tbody").css("filter", "none");
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
    xhr.open("GET", baseURL + "/ecclesiastical-treasures/list/", true);
    xhr.send();
}

function setupFilterArea() {
    $("#free_text_term").val("");
    $("#exactmatch-check").prop("checked", false);
}

function toggleCheckbox() {
    var textValue = $("#free_text_term").val();
    if (textValue.length > 0) {
        $("#exactmatch-check").prop("disabled", false);
    } else {
        $("#exactmatch-check").prop("disabled", true);
    }
}

function applyTreasuresFilter() {
    var free_text_term = $("#free_text_term").val();
    var isTrueChecked = $("#exactmatch-check").prop("checked");
    var exact_match = isTrueChecked ? true : false;

    const params = "?search_keyword=" + free_text_term + "&exact_match=" + exact_match;

    var response = {};
    $("#datatable_treasures tbody").css("filter", "blur(1.0rem)");

    var xhr = new XMLHttpRequest();
    xhr.addEventListener("readystatechange", function () {
        if (xhr.readyState !== 4) return;

        response = JSON.parse(xhr.responseText);

        if (xhr.status >= 200 && xhr.status < 300) {
            const data = response["resource_array"];
            TreasuresDatatable.init(data);
        } else {
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
            $("#datatable_treasures tbody").css("filter", "none");
        }, 500);

    });

    xhr.onerror = () => {
        setTimeout(() => {
            $("#datatable_treasures tbody").css("filter", "none");
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

    xhr.open("GET", baseURL + "/ecclesiastical-treasures/list/" + params, true);
    xhr.send();

}

function resetTreasuresFilter() {
    setupFilterArea();
    fetchTreasures();
}

var TreasuresDatatable = function () {
    var dt;

    var initDatatable = function (data) {
        dt = $("#datatable_treasures").DataTable({
            order: [],
            language: {
                search: "Search within results:"
            },
            responsive: true,
            searchDelay: 500,
            bDestroy: true,
            data: data,
            columns: [
                {
                    title: "Treasure ID",
                    data: "uuid",
                },
                {
                    title: "Default Media",
                    data: "default_img_src",
                    render: function (data, type, row) {
                        return "<img src=" + row["default_img_src"] + " width=50 height=50 />";
                    },
                },
                {
                    title: "Title (English)",
                    data: "title_en",
                },
                {
                    title: "Appellation (English)",
                    data: "appellation_en",
                },
                {
                    title: "Added by (Email)",
                    data: "user_email",
                    render: function (data, type, row) {
                        var mailto = "mailto:" + row["user_email"];
                        return "<a href=" + mailto + ">" + row["user_email"] + "</a>";
                    },
                },
                {
                    title: "Organization",
                    data: "user_organization",
                },
                {
                    title: "Actions",
                    data: null,
                    orderable: false,
                    render: function (data, type, row) {
                        if (row["is_editable"] == true) {
                            return `
                                <a class="btn btn-outline-secondary" href="` + baseURL + "/treasures/view?treasure_id=" + row["uuid"] + `" data-treasure-uuid="` + row["uuid"] + `">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye" viewBox="0 0 16 16">
                                        <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8M1.173 8a13 13 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5s3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5s-3.879-1.168-5.168-2.457A13 13 0 0 1 1.172 8z"/>
                                        <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5M4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0"/>
                                    </svg>
                                </a>
                                <a class="btn btn-outline-secondary" href="` + baseURL + "/treasures/update?treasure_id=" + row["uuid"] + `" data-treasure-uuid="` + row["uuid"] + `">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pencil" viewBox="0 0 16 16">
                                        <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325"/>
                                    </svg>
                                </a>
                                <a class="btn btn-outline-secondary" href="` + baseURL + "/treasures/media?treasure_id=" + row["uuid"] + `" data-treasure-uuid="` + row["uuid"] + `">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-file-image" viewBox="0 0 16 16">
                                        <path d="M8.002 5.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0"/>
                                        <path d="M12 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2M3 2a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v8l-2.083-2.083a.5.5 0 0 0-.76.063L8 11 5.835 9.7a.5.5 0 0 0-.611.076L3 12z"/>
                                    </svg>
                                </a>
                                <a class="btn btn-outline-danger" href="` + baseURL + "/treasures/delete?treasure_id=" + row["uuid"] + `" data-treasure-uuid="` + row["uuid"] + `">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                                        <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
                                        <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
                                    </svg>
                                </a>
                            `;
                        }
                        else {
                            return `
                                    <a class="btn btn-outline-secondary" href="` + baseURL + "/treasures/view?treasure_id=" + row["uuid"] + `" data-treasure-uuid="` + row["uuid"] + `">
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

        $('#datatable_treasures tbody').on('click', 'td.dtr-control', function () {
            $(this).parent().toggleClass('parent-shown');
        });

    }

    return {
        init: function (data) {
            initDatatable(data);
        }
    }
}();

function addNewTreasurePage() {
    location.href = baseURL + "/treasures/add/";
}


$(document).ready(function () {
    setupFilterArea();
    fetchTreasures();
    $("#free_text_term").on("input", toggleCheckbox);
    toggleCheckbox();
});