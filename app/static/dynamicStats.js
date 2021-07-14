// if a button is clicked, send a post request which is different than what happens when the page is refreshed
$(document).ready(function() {
    $("#save_button").click(function() {
        $.post("/",
        {
            button_clicked: "save"
        },
        function(data, status) { });
    });

    $("#clear_button").click(function() {
        $.post("/",
        {
            button_clicked: "clear"
        },
        function(data, status) { });
    });
});

function updateCurrentStats(data) {
    $("#split").text(data['split']);
    $("#avg_split").text(data['avg_split']);
    $("#hr").text(data['hr']);
    $("#avg_hr").text(data['avg_hr']);
    $("#current_hr_zone").text(data['current_hr_zone']);
    
    if (data['current_hr_zone'].startsWith("Error"))
        $("#current_hr_zone").css({'color': 'red'});
    else
        $("#current_hr_zone").css({'color': data['hr_color']});
}
