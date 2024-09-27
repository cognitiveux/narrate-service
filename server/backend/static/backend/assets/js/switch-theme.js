$(document).ready(function () {
	var ColorMode = $("#bd-theme").attr("aria-label");
	$("#imgNarrateLogo").attr("src", $("#imgNarrateLogo").data("dark-src"));
	$("#imgNarrateFooterLogo").attr("src", $("#imgNarrateFooterLogo").data("dark-src"));
	$("#imgFundingLogo").attr("src", $("#imgFundingLogo").data("dark-src"));

	if (ColorMode.includes("dark")) {
		$("#imgNarrateLogo").attr("src", $("#imgNarrateLogo").data("light-src"));
		$("#imgNarrateFooterLogo").attr("src", $("#imgNarrateFooterLogo").data("light-src"));
		$("#imgFundingLogo").attr("src", $("#imgFundingLogo").data("light-src"));
	}

	$(".btnChangeColorModeLight").click(function () {
		$("#imgNarrateLogo").attr("src", $("#imgNarrateLogo").data("dark-src"));
		$("#imgNarrateFooterLogo").attr("src", $("#imgNarrateFooterLogo").data("dark-src"));
		$("#imgFundingLogo").attr("src", $("#imgFundingLogo").data("dark-src"));
	});

	$(".btnChangeColorModeDark").click(function () {
		$("#imgNarrateLogo").attr("src", $("#imgNarrateLogo").data("light-src"));
		$("#imgNarrateFooterLogo").attr("src", $("#imgNarrateFooterLogo").data("light-src"));
		$("#imgFundingLogo").attr("src", $("#imgFundingLogo").data("light-src"));
	});
});