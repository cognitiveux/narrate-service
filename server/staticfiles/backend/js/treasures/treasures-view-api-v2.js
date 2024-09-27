"use strict";

const pageName = "treasuresView";

var ConservationMediaDatatable = function () {
    var dt;

    var initDatatable = function (data) {
        data = data.filter(obj => obj.media_type === "conservation");

        dt = $("#conservationMedia").DataTable({
            language: {
                search: "Search within results:"
            },
            responsive: true,
            searchDelay: 500,
            bDestroy: true,
            data: data,
            columns: [
                {
                    title: "Media ID",
                    data: "uuid",
                },
                {
                    title: "Media File",
                    data: "file_src",
                    render: function (data, type, row) {
                        return "<img src=" + baseURL + row["file_src"] + " width=50 height=50 />";
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
                        return `
                                    <a class="btn btn-outline-secondary" href="` + baseURL + row["file_src"] + `" target="_blank">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye" viewBox="0 0 16 16">
                                            <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8M1.173 8a13 13 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5s3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5s-3.879-1.168-5.168-2.457A13 13 0 0 1 1.172 8z"/>
                                            <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5M4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0"/>
                                        </svg>
                                    </a>
                            `;
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

var ContentMediaDatatable = function () {
    var dt;

    var initDatatable = function (data) {
        data = data.filter(obj => obj.media_type === "content");

        dt = $("#contentMedia").DataTable({
            language: {
                search: "Search within results:"
            },
            responsive: true,
            searchDelay: 500,
            bDestroy: true,
            data: data,
            columns: [
                {
                    title: "Media ID",
                    data: "uuid",
                },
                {
                    title: "Media File",
                    data: "file_src",
                    render: function (data, type, row) {
                        return "<img src=" + baseURL + row["file_src"] + " width=50 height=50 />";
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
                        return `
                                    <a class="btn btn-outline-secondary" href="` + baseURL + row["file_src"] + `" target="_blank">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye" viewBox="0 0 16 16">
                                            <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8M1.173 8a13 13 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5s3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5s-3.879-1.168-5.168-2.457A13 13 0 0 1 1.172 8z"/>
                                            <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5M4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0"/>
                                        </svg>
                                    </a>
                            `;
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

var PhotosMediaDatatable = function () {
    var dt;

    var initDatatable = function (data) {
        data = data.filter(obj => obj.media_type === "photo");

        dt = $("#photosMedia").DataTable({
            language: {
                search: "Search within results:"
            },
            responsive: true,
            searchDelay: 500,
            bDestroy: true,
            data: data,
            columns: [
                {
                    title: "Media ID",
                    data: "uuid",
                },
                {
                    title: "Media File",
                    data: "file_src",
                    render: function (data, type, row) {
                        return "<img src=" + baseURL + row["file_src"] + " width=50 height=50 />";
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
                        return `
                                    <a class="btn btn-outline-secondary" href="` + baseURL + row["file_src"] + `" target="_blank">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye" viewBox="0 0 16 16">
                                            <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8M1.173 8a13 13 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5s3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5s-3.879-1.168-5.168-2.457A13 13 0 0 1 1.172 8z"/>
                                            <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5M4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0"/>
                                        </svg>
                                    </a>
                            `;
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

var VideosMediaDatatable = function () {
    var dt;

    var initDatatable = function (data) {
        data = data.filter(obj => obj.media_type === "video");

        dt = $("#videosMedia").DataTable({
            language: {
                search: "Search within results:"
            },
            responsive: true,
            searchDelay: 500,
            bDestroy: true,
            data: data,
            columns: [
                {
                    title: "Media ID",
                    data: "uuid",
                },
                {
                    title: "Media File",
                    data: "file_src",
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
                        return `
                                <a class="btn btn-outline-secondary" href="` + baseURL + row["file_src"] + `" target="_blank">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye" viewBox="0 0 16 16">
                                        <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8M1.173 8a13 13 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5s3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5s-3.879-1.168-5.168-2.457A13 13 0 0 1 1.172 8z"/>
                                        <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5M4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0"/>
                                    </svg>
                                </a>
                            `;
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

function fetchTreasure(targetURL, treasureID) {
    const funcName = "fetchTreasure()";
    const params = "?treasure_id=" + treasureID;
    var response = {};
    console.log("[" + pageName + "] -> " + funcName);

    var xhr = new XMLHttpRequest();
    xhr.addEventListener("readystatechange", function () {
        if (xhr.readyState !== 4) {
            return;
        }
        response = JSON.parse(xhr.responseText);

        if (xhr.status >= 200 && xhr.status < 300) {
            var mailto = "mailto:" + response["resource_obj"]["user_email"];
            document.getElementById("treasure_id").value = treasureID;
            document.getElementById("user_email").href = mailto;
            document.getElementById("user_email").innerHTML = response["resource_obj"]["user_email"];
            document.getElementById("user_organization").value = response["resource_obj"]["user_organization"];
            document.getElementById("titleEnInput").value = response["resource_obj"]["e35_title_en_content"];
            document.getElementById("titleGrInput").value = response["resource_obj"]["e35_title_gr_content"];
            document.getElementById("titleBgInput").value = response["resource_obj"]["e35_title_bg_content"];
            document.getElementById("titleTkInput").value = response["resource_obj"]["e35_title_tk_content"];
            document.getElementById("appellationEnInput").value = response["resource_obj"]["e41_appellation_en_content"];
            document.getElementById("appellationGrInput").value = response["resource_obj"]["e41_appellation_gr_content"];
            document.getElementById("appellationBgInput").value = response["resource_obj"]["e41_appellation_bg_content"];
            document.getElementById("appellationTkInput").value = response["resource_obj"]["e41_appellation_tk_content"];
            document.getElementById("existingObjCodeInput").value = response["resource_obj"]["e42_identifier_content"];
            document.getElementById("descShortInput").value = response["resource_obj"]["description_short_content"];
            document.getElementById("descExtInput").value = response["resource_obj"]["description_extended_content"];
            document.getElementById("timeSpanInput").value = response["resource_obj"]["e52_time_span_content"];
            document.getElementById("kindInput").value = response["resource_obj"]["e55_type_content"];
            document.getElementById("creatorInput").value = response["resource_obj"]["e71_human_made_thing_content"];
            document.getElementById("beginningOfExistenceInput").value = response["resource_obj"]["e63_beginning_of_existence_content"];
            $("#wasInChurchInput").attr("checked", response["resource_obj"]["was_in_church"]);
            $("#wasInAnotherCountryInput").attr("checked", response["resource_obj"]["was_in_another_country"]);
            $("#wasLostAndFoundInput").attr("checked", response["resource_obj"]["was_lost_and_found"]);
            document.getElementById("dimensionInput").value = response["resource_obj"]["e54_dimension_content"];
            document.getElementById("materialInput").value = response["resource_obj"]["e57_material_content"];
            document.getElementById("inscriptionInput").value = response["resource_obj"]["e34_inscription_content"];
            document.getElementById("manuscriptTextInput").value = response["resource_obj"]["e73_information_object_content"];
            document.getElementById("eventInformationInput").value = response["resource_obj"]["e5_event_content"];            
            document.getElementById("positionOfTreasureInput").value = response["resource_obj"]["e53_place_content"];
            document.getElementById("previousDocumentationInput").value = response["resource_obj"]["previous_documentation_content"];
            document.getElementById("relevantBibliographyInput").value = response["resource_obj"]["relevant_bibliography_content"];
            document.getElementById("preservationStatusInput").value = response["resource_obj"]["e14_condition_assessment_content"];
            document.getElementById("conservationStatusInput").value = response["resource_obj"]["e11_modification_content"];
            document.getElementById("eventInformationInput").value = response["resource_obj"]["e5_event_content"];
            document.getElementById("firstPersonInput").value = response["resource_obj"]["people_that_help_with_documentation_first"];
            document.getElementById("secondPersonInput").value = response["resource_obj"]["people_that_help_with_documentation_second"];
            document.getElementById("thirdPersonInput").value = response["resource_obj"]["people_that_help_with_documentation_third"];
            document.getElementById("firstGroupInput").value = response["resource_obj"]["group_first"];
            document.getElementById("secondGroupInput").value = response["resource_obj"]["group_second"];
            document.getElementById("thirdGroupInput").value = response["resource_obj"]["group_third"];
            document.getElementById("collectionInput").value = response["resource_obj"]["e78_curated_holding_content"];            
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
    xhr.open("GET", baseURL + targetURL + params, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send();
}

function fetchTreasuresMedia(targetURL, treasureID) {
    const funcName = "fetchTreasuresMedia()";
    console.log("[" + pageName + "] -> " + funcName);

    const params = "?treasure_id=" + treasureID;
    var response = {};
    var xhr = new XMLHttpRequest();
    $("#conservationMedia tbody").css("filter", "blur(1.0rem)");
    $("#contentMedia tbody").css("filter", "blur(1.0rem)");
    $("#photosMedia tbody").css("filter", "blur(1.0rem)");
    $("#videosMedia tbody").css("filter", "blur(1.0rem)");

    xhr.addEventListener("readystatechange", function () {
        if (xhr.readyState !== 4) return;

        response = JSON.parse(xhr.responseText);

        if (xhr.status >= 200 && xhr.status < 300) {
            const data = response["resource_array"];
            ConservationMediaDatatable.init(data);
            ContentMediaDatatable.init(data);
            PhotosMediaDatatable.init(data);
            VideosMediaDatatable.init(data);
            setTimeout(() => {
                $("#conservationMedia").DataTable().columns.adjust().draw();
                $("#contentMedia").DataTable().columns.adjust().draw();
                $("#photosMedia").DataTable().columns.adjust().draw();
                $("#videosMedia").DataTable().columns.adjust().draw();
            }, 500);
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
            $("#conservationMedia tbody").css("filter", "none");
            $("#contentMedia tbody").css("filter", "none");
            $("#photosMedia tbody").css("filter", "none");
            $("#videosMedia tbody").css("filter", "none");
        }, 500);
        
    });

    xhr.onerror = () => {
        setTimeout(() => {
            $("#conservationMedia tbody").css("filter", "none");
            $("#contentMedia tbody").css("filter", "none");
            $("#photosMedia tbody").css("filter", "none");
            $("#videosMedia tbody").css("filter", "none");
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

$(document).ready(function () {
    console.log("[" + pageName + "]");

    var treasure_id = getUrlParameter("treasure_id");
    fetchTreasure("/ecclesiastical-treasures/fetch/", treasure_id);
    fetchTreasuresMedia("/ecclesiastical-treasures/media/list/", treasure_id);
});