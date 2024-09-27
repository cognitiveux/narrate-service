"use strict";

function fetchTreasure(targetURL, treasureID) {
    const params = "?treasure_id=" + treasureID;
    var response = {};

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


function updateTreasure(targetURL, form) {
    var response = {};

    var xhr = new XMLHttpRequest();
    xhr.addEventListener("readystatechange", function () {
        if (xhr.readyState !== 4) {
            return;
        }
        response = JSON.parse(xhr.responseText);

        if (xhr.status >= 200 && xhr.status < 300) {
            Swal.fire({
                text: "Ecclesiastical Treasure has been successfully updated!",
                icon: "success",
                buttonsStyling: false,
                confirmButtonText: "Okay, got it!",
                customClass: {
                    confirmButton: "btn btn-primary"
                },
                timer: 2000
            });
            setTimeout(function () {
                location.href = baseURL + "/dashboard/";
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
        uuid: getUrlParameter("treasure_id"),
        title_en: form.elements["titleEnInput"].value,
        title_gr: form.elements["titleGrInput"].value,
        title_bg: form.elements["titleBgInput"].value,
        title_tk: form.elements["titleTkInput"].value,
        appellation_en: form.elements["appellationEnInput"].value,
        appellation_gr: form.elements["appellationGrInput"].value,
        appellation_bg: form.elements["appellationBgInput"].value,
        appellation_tk: form.elements["appellationTkInput"].value,
        existing_obj_code: form.elements["existingObjCodeInput"].value,
        desc_short_version: form.elements["descShortInput"].value,
        desc_extended_version: form.elements["descExtInput"].value,
        time_span: form.elements["timeSpanInput"].value,
        kind: form.elements["kindInput"].value,
        creator: form.elements["creatorInput"].value,
        beginning_of_existence: form.elements["beginningOfExistenceInput"].value,
        was_in_church: $("#wasInChurchInput").is(":checked"),
        was_in_another_country: $("#wasInAnotherCountryInput").is(":checked"),
        was_lost_and_found: $("#wasLostAndFoundInput").is(":checked"),
        dimension: form.elements["dimensionInput"].value,
        material: form.elements["materialInput"].value,
        inscription: form.elements["inscriptionInput"].value,
        manuscript_text: form.elements["manuscriptTextInput"].value,
        event_information: form.elements["eventInformationInput"].value,
        position_of_treasure: form.elements["positionOfTreasureInput"].value,
        previous_documentation: form.elements["previousDocumentationInput"].value,
        relevant_bibliography: form.elements["relevantBibliographyInput"].value,
        preservation_status: form.elements["preservationStatusInput"].value,
        conservation_status: form.elements["conservationStatusInput"].value,
        people_that_help_with_documentation: [
            form.elements["firstPersonInput"].value,
            form.elements["secondPersonInput"].value,
            form.elements["thirdPersonInput"].value,
        ],
        group_of_objects: [
            form.elements["firstGroupInput"].value,
            form.elements["secondGroupInput"].value,
            form.elements["thirdGroupInput"].value,
        ],
        collection_it_belongs: form.elements["collectionInput"].value,
        conservation_id: $("#conservation_photos_uuid").val(),
    }
    xhr.send(JSON.stringify(jsonData));
}

$(document).ready(function () {
    var treasure_id = getUrlParameter("treasure_id");
    fetchTreasure("/ecclesiastical-treasures/fetch/", treasure_id);
});