document.addEventListener('DOMContentLoaded', function() {
    const checkboxes = document.querySelectorAll('.torb-checkbox');
    const breedButton = document.getElementById('breed-button');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const selectedTorbs = document.querySelectorAll('.torb-checkbox:checked');
            let allFertile = true;

            selectedTorbs.forEach(selected => {
                const row = selected.closest('tr');
                if (row.dataset.fertile === "False") {
                    allFertile = false;
                }
            });

            breedButton.disabled = (selectedTorbs.length !== 2 || !allFertile);
        });
    });

});

let isPolling = false;

function checkReadyStatus() {
    console.log("Checking ready status...");

    fetch(checkReadyStatusUrl)
    .then(response => response.json())
    .then(data => {
        console.log("Polling response received:", data);
        if (data.ready) {
            console.log("Colony is ready, continuing polling.");
// If the colony is still ready, continue polling
            isPolling = true;
        } else {
            console.log("Colony is not ready, reloading page.");
// If the colony is no longer ready, refresh the page
            location.reload();
        }
    })
    .catch(error => console.error('Error checking ready status:', error));
}

function startPolling() {
    if (!isPolling) {
        console.log("Starting polling...");
        isPolling = true;
        setInterval(checkReadyStatus, 5000);
    }
}

// Check the initial status when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log("Checking initial colony status");
    fetch(checkReadyStatusUrl)
        .then(response => response.json())
        .then(data => {
            console.log("Initial status received:", data);
            if (data.ready) {
                console.log("Initial colony status is ready, starting polling.");
                // Start polling only if the colony is initially ready
                startPolling();
            } else {
                console.log("Initial colony status is not ready.");
            }
        })
        .catch(error => console.error('Error checking initial ready status:', error));
});

document.addEventListener('DOMContentLoaded', function() {
    const endTurnButton = document.getElementById('endTurnButton');
    const form = endTurnButton.closest('form');

    if (endTurnButton) {
        endTurnButton.addEventListener('click', function(event) {
            const form = endTurnButton.closest('form');

            // Prevent form from submitting immediately
            event.preventDefault();

            // Ensure the correct action value is set
            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'action';
            hiddenInput.value = 'end_turn';
            form.appendChild(hiddenInput);

            // Disable the button and change its text
            endTurnButton.disabled = true;
            endTurnButton.innerText = "Waiting for other players...";

            // Start polling
            isPolling = false;
            startPolling();

            // Submit the form after setting up everything
            form.submit();
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const consoleDisplay = document.querySelector('.console-display');
    consoleDisplay.scrollTop = consoleDisplay.scrollHeight; // Scroll to the bottom on load
});

// Optionally, you can also scroll to the bottom whenever new content is added
function scrollToBottom() {
    const consoleDisplay = document.querySelector('.console-display');
    consoleDisplay.scrollTop = consoleDisplay.scrollHeight;
}

document.addEventListener('DOMContentLoaded', function() {
    const tooltips = document.querySelectorAll('.status-tooltip');

    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', function() {
            const tooltipText = this.getAttribute('data-tooltip');
            const tooltipDiv = document.createElement('div');
            tooltipDiv.className = 'dynamic-tooltip';
            tooltipDiv.innerHTML = tooltipText;

            document.body.appendChild(tooltipDiv);

            const rect = this.getBoundingClientRect();
            tooltipDiv.style.top = `${rect.top - tooltipDiv.offsetHeight - 10}px`;
            tooltipDiv.style.left = `${rect.left + (rect.width / 2) - (tooltipDiv.offsetWidth / 2)}px`;

            tooltipDiv.style.opacity = '1';
            tooltipDiv.style.visibility = 'visible';
        });

        tooltip.addEventListener('mouseleave', function() {
            const tooltipDiv = document.querySelector('.dynamic-tooltip');
            if (tooltipDiv) {
                tooltipDiv.remove();
            }
        });
    });
});

function sortTable(columnIndex) {
    const table = document.getElementById("torb-table");
    let rows, switching, i, x, y, shouldSwitch, direction, switchCount = 0;

    switching = true;
    direction = "asc"; 

    // Clear previous arrows
    document.querySelectorAll('.sort-arrow').forEach(arrow => {
        arrow.innerHTML = '';
    });

    while (switching) {
        switching = false;
        rows = table.rows;

        for (i = 1; i < rows.length - 1; i++) {
            shouldSwitch = false;
            x = rows[i].getElementsByTagName("TD")[columnIndex];
            y = rows[i + 1].getElementsByTagName("TD")[columnIndex];

            let xContent = x.innerHTML.toLowerCase();
            let yContent = y.innerHTML.toLowerCase();

            // Check if content is numeric
            if (!isNaN(xContent) && !isNaN(yContent)) {
                xContent = parseFloat(xContent);
                yContent = parseFloat(yContent);
            }

            if (direction === "asc") {
                if (xContent > yContent) {
                    shouldSwitch = true;
                    break;
                }
            } else if (direction === "desc") {
                if (xContent < yContent) {
                    shouldSwitch = true;
                    break;
                }
            }
        }

        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchCount++;
        } else {
            if (switchCount === 0 && direction === "asc") {
                direction = "desc";
                switching = true;
            }
        }
    }

    // Set the arrow for the sorted column
    const arrow = document.getElementById(`sort-arrow-${columnIndex}`);
    arrow.innerHTML = direction === "asc" ? "↑" : "↓";
}