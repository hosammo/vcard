document.addEventListener('DOMContentLoaded', function() {
    const colorInputs = document.querySelectorAll('input[type="color"]');

    colorInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            console.log('Color updated:', this.value);
        });
    });
});