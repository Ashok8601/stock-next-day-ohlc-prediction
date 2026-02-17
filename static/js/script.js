document.addEventListener('DOMContentLoaded', function() {
    const stockForm = document.getElementById('stockForm');
    const stockSelect = document.getElementById('stock_select');
    const inputFormContainer = document.getElementById('inputFormContainer');
    const predictionFormHeading = inputFormContainer.querySelector('h2');
    const hiddenStockName = document.getElementById('hidden_stock_name');

    stockForm.addEventListener('submit', function(event) {
        event.preventDefault();

        const selectedStockValue = stockSelect.value;
        const selectedStockText = stockSelect.options[stockSelect.selectedIndex].text;

        if (selectedStockValue) {
            inputFormContainer.style.display = 'block';
            predictionFormHeading.innerHTML = `📈 Inputs for **${selectedStockText}**`;
            hiddenStockName.value = selectedStockValue;
            inputFormContainer.scrollIntoView({ behavior: 'smooth' });
        } else {
            alert('Please select a stock to predict.');
        }
    });

    stockSelect.addEventListener('change', function() {
        stockForm.dispatchEvent(new Event('submit', { cancelable: true }));
    });
});
