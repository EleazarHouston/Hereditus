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

    const consoleDisplay = document.querySelector('.console-display');
    consoleDisplay.scrollTop = consoleDisplay.scrollHeight; // Scroll to the bottom on load

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

    reapplyTooltips();
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

function filterTorbs() {
    const checkboxes = document.querySelectorAll('.filter-buttons input[type="checkbox"]');
    const selectedActions = Array.from(checkboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value.toLowerCase());

    const url = new URL(filterTorbsUrl, window.location.origin);
    if (selectedActions.length > 0) {
        url.searchParams.append('action', selectedActions.join(','));
    }
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const torbTableBody = document.querySelector('#torb-table tbody');
            torbTableBody.innerHTML = '';
            data.torbs.forEach(torb => {
                const row = document.createElement('tr');
                row.dataset.fertile = torb.fertile;
                row.innerHTML = `
                    <td><input type="checkbox" name="selected_torbs" value="${torb.id}" class="torb-checkbox"></td>
                    <td>${torb.private_ID}</td>
                    <td>${torb.generation}</td>
                    <td>${torb.name}</td>
                    <td>${torb.hp}/${torb.max_hp}</td>
                    ${Object.entries(torb.genes).map(([gene, alleles]) => `<td>${alleles.join(' | ')}</td>`).join('')}
                    <td>${torb.action_desc}</td>
                    <td class="status-column"><span class="status-tooltip" data-tooltip="${torb.status}">🛈</span></td>
                `;
                torbTableBody.appendChild(row);
            });
            // Reapply sorting
            const sortedColumn = document.querySelector('.sort-arrow:not(:empty)');
            if (sortedColumn) {
                const columnIndex = sortedColumn.id.split('-').pop();
                sortTable(parseInt(columnIndex));
            }
            // Reapply tooltip functionality
            reapplyTooltips();
        });
}

function reapplyTooltips() {
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
}

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

function filterAttributes() {
    const fertileFilter = document.getElementById('fertile-filter');
    const fertileFilterLabel = document.getElementById('fertile-filter-label');
    const torbTableBody = document.querySelector('#torb-table tbody');
    const rows = torbTableBody.querySelectorAll('tr');

    let filterState = fertileFilter.dataset.filterState || 'all';

    if (filterState === 'all') {
        filterState = 'fertile';
        fertileFilterLabel.textContent = '✔️ Fertile';
        fertileFilter.checked = true;
    } else if (filterState === 'fertile') {
        filterState = 'infertile';
        fertileFilterLabel.textContent = '❌ Fertile';
        fertileFilter.checked = true;
    } else {
        filterState = 'all';
        fertileFilterLabel.textContent = 'Fertile';
        fertileFilter.checked = false;
    }

    fertileFilter.dataset.filterState = filterState;

    rows.forEach(row => {
        const isFertile = row.dataset.fertile === 'True';
        if (filterState === 'fertile' && !isFertile) {
            row.style.display = 'none';
        } else if (filterState === 'infertile' && isFertile) {
            row.style.display = 'none';
        } else {
            row.style.display = '';
        }
    });
}

