function setupData() {
    $(document).ready(function () {
        $('#example').DataTable({
            "ajax": {
                "url": "/cursos-get", 
                "dataType": "json",
                "dataSrc": "",
                "contentType":"application/json"
            },
            "columns": [
                {"data": "id"},
                {"data": "codigo"},
                {"data": "nombre"},
                {"data": "descripcion"},
                {"data": "ciclo"},
                {"data": "anno"}
            ]
        });
    });
}
$( window ).on( "load", setupData );

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