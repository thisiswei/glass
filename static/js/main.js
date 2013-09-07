$("#dispatch").on('click', function() {
    var checked = $(this).is(':checked');
    var process = "dispatch"

    $.ajax({
        type: "POST",
        url: "/",
        data: {checked : checked, operation: process}
    });
});

$("#obsession").on('click', function() {
    var checked = $(this).is(':checked');
    var process = "obsession"

    $.ajax({
        type: "POST",
        url: "/",
        data: {checked : checked, operation: process}
    });
});

$("#streetchic").on('click', function() {
    var checked = $(this).is(':checked');
    var process = "streetchic"

    $.ajax({
        type: "POST",
        url: "/",
        data: {checked : checked, operation: process}
    });
});

$("#stylerater").on('click', function() {
    var checked = $(this).is(':checked');
    var process = "style"

    $.ajax({
        type: "POST",
        url: "/",
        data: {checked : checked, operation: process}
    });
});

$("#horoscope").on('click', function() {
    var checked = $(this).is(':checked');
    var process = "horoscope"

    $.ajax({
        type: "POST",
        url: "/",
        data: {checked : checked, operation: process}
    });
});

$("#horoscope_select").on('change', function() {
    var value = $(this).val();
    var process = "horoscope_select"

    $.ajax({
        type: "POST",
        url: "/",
        data: {value : value, operation: process}
    });
});

function deleteArticle(model_type, model_id)
{
	var process = "delete_article"
	
	$.ajax({
        type: "POST",
        url: "/delete",
        data: {operation: process, model_type : model_type, model_id: model_id},
        success: function(result) {
			window.location='/';
        }
    });
}
