function openTab(evt, title) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for(i = 0; i < tabcontent.length; i++) // make all tab content invisible
        tabcontent[i].style.display = "none";

    tablinks = document.getElementsByClassName("tablinks");
    for(i = 0; i < tablinks.length; i++) // make all tabs non-active
        tablinks[i].className = tablinks[i].className.replace(" active", "");

    // make the clicked-on tab active and show its content
    document.getElementById(title).style.display = "block";
    evt.currentTarget.className += " active"
}
