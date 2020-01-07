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