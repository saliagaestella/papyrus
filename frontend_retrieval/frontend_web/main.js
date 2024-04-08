document.addEventListener('DOMContentLoaded', function () {
    fetchData(); //Output recibido y accedido en Json (por ahora no da problemas)
});

/* 
3. Meter links
*/
function fetchData() {

 // Show the loading icon
    document.getElementById('loading-icon').style.display = 'flex';

    fetch('http://localhost:3001')
    .then(response => response.json())
    .then(data => {
 // Hide the loading icon
        document.getElementById('loading-icon').style.display = 'none';
        const container = document.getElementById('data-container');
        container.innerHTML = ''; // Clear previous content

        if(data.length > 0) {
            // Extract date from the first document
            const date = `${data[0].dia}/${data[0].mes}/${data[0].anio}`;
            // Update the page title with the date
            document.querySelector('h1').textContent = `Novedades Regulatorias - ${date}`;

            // Iterate over each item and display it in the requested order
            data.forEach(item => {
                // Main div for each document
                const itemDiv = document.createElement('div');
                itemDiv.classList.add('data-item');

                // Div for ID
                const idDiv = document.createElement('div');
                idDiv.textContent = `${item._id}`;
                idDiv.classList.add('id-values');
                itemDiv.appendChild(idDiv);

                // Div for "Etiquetas" label
                const etiquetasLabelDiv = document.createElement('div');
                etiquetasLabelDiv.textContent = "Etiquetas";
                etiquetasLabelDiv.classList.add('etiquetas-label');
                itemDiv.appendChild(etiquetasLabelDiv);

                // Container for Etiquetas values
                const etiquetasValuesContainer = document.createElement('div');
                etiquetasValuesContainer.classList.add('etiquetas-values');

                // Append each etiqueta as a separate span/div inside etiquetasValuesContainer
                item.etiquetas.forEach(etiqueta => {
                    const etiquetaSpan = document.createElement('span'); // Using 'span' for inline display
                    etiquetaSpan.textContent = etiqueta;
                    etiquetasValuesContainer.appendChild(etiquetaSpan);
                });

                // Append Etiquetas values container to the main Etiquetas container
                itemDiv.appendChild(etiquetasValuesContainer);

                // Div for "Resumen" label
                const resumenLabelDiv = document.createElement('div');
                resumenLabelDiv.textContent = "Resumen";
                resumenLabelDiv.classList.add('resumen-label'); 
                itemDiv.appendChild(resumenLabelDiv);

                // Div for Resumen content
                const resumenContentDiv = document.createElement('div');
                resumenContentDiv.classList.add('resumen-content'); 
                resumenContentDiv.textContent = item.resumen;
                itemDiv.appendChild(resumenContentDiv);

                // Append the main div to the container
                container.appendChild(itemDiv);
            });
        } else {
            // Handle case where no items were found
            container.textContent = 'No data found for the selected date.';
        }
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });
}

/*
function toggleMenu() {
    var menu = document.querySelector('.menu');
    if (menu.style.display === 'block') {
      menu.style.display = 'none';
      menu.style.marginRight = '0'; // Reset the margin when menu is closed
    } else {
      menu.style.display = 'block';
      menu.style.marginRight = '150px'; // Apply the margin when menu is open
    }
    menu.classList.toggle('active');
  }
*/
  

/*

function fetchData() {
    fetch('http://localhost:3001')
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('data-container');
        container.innerHTML = ''; // Clear previous content
        
        if(data.length > 0) {
            // Extract date from the first document
            const date = `${data[0].dia}/${data[0].mes}/${data[0].anio}`;
            // Update the page title with the date
            document.querySelector('h1').textContent = `Novedades Regulatorias - ${date}`;

            // Iterate over each item and display it
            data.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.classList.add('data-item');
                const content = `ID: ${item._id}, Resumen: ${item.resumen}, Etiquetas: ${item.etiquetas.join(', ')}`;
                itemDiv.textContent = content;
                container.appendChild(itemDiv);
            });
        } else {
            // Handle case where no items were found
            container.textContent = 'No data found for the selected date.';
        }
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });
}

*/








/* Get justs some elements from backend but with all variables
function fetchData() {
    fetch('http://localhost:3001')
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('data-container');
        container.innerHTML = ''; // Clear previous content

        // Get today's date components
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth() + 1; // getMonth() is zero-based
        const day = today.getDate();

        // Filter data for today's date
        const filteredData = data.filter(item => {
            return item.anio === year && item.mes === month && item.dia === day;
        });

        // Display each filtered item
        filteredData.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.classList.add('data-item');
            // Customize this line as needed to display relevant information
            itemDiv.textContent = `Date: ${item.dia}/${item.mes}/${item.anio}, Data: ${JSON.stringify(item)}`;
            container.appendChild(itemDiv);
        });

        // Handle case where no items match today's date
        if(filteredData.length === 0) {
            container.textContent = 'No data found for today.';
        }
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });
}
*/



/* Get just last element from backend
function fetchData() {
    fetch('http://localhost:3001')
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('data-container');
        container.innerHTML = ''; // Clear previous content
        if(data.length > 0) {
            const lastItem = data[data.length - 1]; // Get the last item
            const itemDiv = document.createElement('div');
            itemDiv.classList.add('data-item');
            itemDiv.textContent = JSON.stringify(lastItem); // Display the last item
            container.appendChild(itemDiv);
        }
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });
}

*/