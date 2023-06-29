document.getElementById('date-form').addEventListener('submit', function(e) {
    // ziskam input values
    var startDate = document.getElementById('start_date').value; // bude ve formatu string
    var endDate = document.getElementById('end_date').value;

    // vytvori Date objects
    var start = new Date(startDate);
    var end = new Date(endDate);
    var now = new Date();

    // check jestli je vybrane datum po dnesku
    if (start<now) {
        alert("Začátek nesmí být v minulosti.");
        e.preventDefault(); // nechci submitovat formular
    }
    if (start > end) {
        alert("Konec musí být ve stejný nebo pozdèjší den jako začátek.");
        e.preventDefault();
    }

    // Fetch data from the server
    fetch('/search', {              // HTTP request
        method: 'POST',
        headers: {                           // HTTP header
            'Content-Type': 'application/json'   // chceme predat data ve formatu json
        },
        body: JSON.stringify({
            start_date: startDate,
            end_date: endDate
        })
    })
    .then(function(response) {   // po fetch se vrati response
        return response.json();  // z response se stane json
    })
.then(function(data) {              // json = data
    var resultsDiv = document.getElementById('search-results');
    resultsDiv.style.display = 'block'; // zobrazit result div na strance

    var htmlString = '<h3>Ve zvolené dny ' + data.start_date + ' - ' + data.end_date + ' jsou dostupné následující kategorie aut:</h3>';

    htmlString += '<table class="results-table">' +
                  '<tr><th>Kategorie</th><th>Počet</th><th></th></tr>'; // hlavicka tabulky

    for (var category in data.car_categories) {
        htmlString += '<tr><td>' + category + '</td><td>' + data.car_categories[category] + '</td>' + // kategorie a pocet aut
                      '<td><form action="/reservation" method="POST">' +
                      '<input type="hidden" id="car_category" name="car_category" value="' + category + '">' +
                      '<button type="submit">Vybrat</button>' +
                      '</form></td></tr>';
    }

    resultsDiv.innerHTML = htmlString;
});

});
