
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

    if (form && endTurnButton) {
        form.addEventListener('submit', function(event) {
            // Before the form is submitted, ensure the correct action value is set
            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'action';
            hiddenInput.value = 'end_turn';
            form.appendChild(hiddenInput);

            // Disable the button and change its text
            endTurnButton.disabled = true;
            endTurnButton.innerText = "Waiting for other players...";

            isPolling = false;
            startPolling();
        });
    }
});

