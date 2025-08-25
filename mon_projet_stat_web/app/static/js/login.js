// JS spécifique à la page de connexion (exemple: affichage du nom du fichier sélectionné)
document.addEventListener('DOMContentLoaded', function() {
    var fileInput = document.getElementById('users_file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            var info = document.querySelector('.file-info');
            if (fileInput.files.length > 0) {
                info.textContent = 'Fichier sélectionné : ' + fileInput.files[0].name;
            } else {
                info.textContent = 'Format: Excel (.xlsx, .xls) - Colonnes: utilisateur, departement';
            }
        });
    }
});
