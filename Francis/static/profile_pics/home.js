var dir = "/cursos";
var file_extension = ".*";
$.ajax({
    //This will retrieve the contents of the folder if the folder is configured as 'browsable'
    url: dir,
    success: function (data) {
        //List all file names in the page
        $(data).find("a:contains(" + file_extension + ")").each(function () {
            var filename = this.href.replace(window.location, "").replace("http://", "");
            $("body").append("<a  href='/" + dir + filename + "'>");
        });
    }
});