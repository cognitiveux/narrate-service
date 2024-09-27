"use strict";

function addNewTreasure(targetURL, form) {
    var response = {};

    var xhr = new XMLHttpRequest();
    xhr.addEventListener("readystatechange", function () {
        if (xhr.readyState !== 4) {
            return;
        }
        response = JSON.parse(xhr.responseText);

        if (xhr.status >= 200 && xhr.status < 300) {
            Swal.fire({
                text: "Ecclesiastical Treasure has been successfully added!",
                icon: "success",
                buttonsStyling: false,
                confirmButtonText: "Okay, got it!",
                customClass: {
                    confirmButton: "btn btn-primary"
                },
                timer: 2000
            });
            setTimeout(function () {
                location.href = baseURL + "/dashboard";
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
        content_id: $("#content_uuid").val(),
        photos_id: $("#photos_uuid").val(),
        videos_id: $("#videos_uuid").val(),
    }
    xhr.send(JSON.stringify(jsonData));
}