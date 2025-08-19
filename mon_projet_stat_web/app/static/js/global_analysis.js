// JS extrait de global_analysis.html

document.getElementById('start-analysis').addEventListener('click', function() {
    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loading-text');
    const progressBar = loading.querySelector('.progress-bar');
    loading.style.display = 'flex';

    fetch('/analyze_all_courses', {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert('Erreur lors de l\'analyse: ' + data.error);
        }
    })
    .catch(error => {
        alert('Erreur: ' + error.message);
    })
    .finally(() => {
        loading.style.display = 'none';
    });
});

// Add click event listeners to department cards

document.querySelectorAll('.department-card').forEach(card => {
    card.addEventListener('click', function() {
        const dept = this.dataset.dept;
        // Hide all details sections
        document.querySelectorAll('.details-section').forEach(section => {
            section.style.display = 'none';
        });
        // Show the clicked department's details
        const detailsSection = document.getElementById(`details-${dept}`);
        if (detailsSection) {
            detailsSection.style.display = 'block';
            detailsSection.scrollIntoView({ behavior: 'smooth' });
        }
    });
});
