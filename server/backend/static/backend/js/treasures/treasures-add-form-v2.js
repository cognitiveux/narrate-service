"use strict";

var btnSubmitID = $("#holder_new_treasure_submit")[0];
var targetURL = "/ecclesiastical-treasures/create/";

var NEW_TREASURE = function () {
    var actions = function () {
        var form = $("#holder_new_treasure_form");

        form.on("submit", function (e) {
            e.preventDefault();
            btnSubmitID.disabled = true;
            $("#titleEnInput").removeClass("is-invalid");
            $("#appellationEnInput").removeClass("is-invalid");

            var invalidFields = $(form).find(":invalid");

            if (this.checkValidity() === false) {
                e.stopPropagation();
                var invalidField = this.querySelector(":invalid");

                if (invalidField) {
                    $("#tab1-tab").click();
                    invalidField.focus();
                }
                btnSubmitID.disabled = false;
            } else {
                setTimeout(function () {
                    btnSubmitID.disabled = false;
                    addNewTreasure(targetURL, form[0]);
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

$(document).ready(function () {
    const tabs = document.querySelectorAll(".nav-link");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            if (tab.id === "tab5-tab") {
                $("#holder_new_treasure_submit").show();
            }
            else {
                $("#holder_new_treasure_submit").hide();
            }
        });
    });
});