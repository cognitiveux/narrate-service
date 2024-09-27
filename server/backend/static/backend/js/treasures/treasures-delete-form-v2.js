"use strict";

var btnSubmitID = $("#holder_delete_treasure_submit")[0];
var targetURL = "/ecclesiastical-treasures/delete/";

var DELETE_TREASURE = function () {
    var actions = function () {
        var form = $("#holder_delete_treasure_form");

        form.on("submit", function (e) {
            e.preventDefault();
            btnSubmitID.disabled = true;
            setTimeout(function () {
                deleteTreasure(targetURL, form[0]);
                btnSubmitID.disabled = false;
            }, 1000);
        });
    }

    return {
        init: function () {
            actions();
        }
    };
}();