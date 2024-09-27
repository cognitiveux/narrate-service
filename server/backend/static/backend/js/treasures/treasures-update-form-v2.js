"use strict";

var btnSubmitID = $("#holder_update_treasure_submit")[0];
var targetURL = "/ecclesiastical-treasures/update/";

var UPDATE_TREASURE = function () {
    var actions = function () {
        var form = $("#holder_update_treasure_form");

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
                    updateTreasure(targetURL, form[0]);
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
          if (tab.id === "tab4-tab") {
              $("#holder_update_treasure_submit").show();
          }
          else {
            $("#holder_update_treasure_submit").hide();
          }
        });
    });
});