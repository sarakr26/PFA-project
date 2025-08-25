
// JS extrait de extract.html
// Gestion du tableau des utilisateurs par département
document.addEventListener('DOMContentLoaded', function() {
	// Sidebar: afficher les utilisateurs inscrits à un cours
	document.querySelectorAll('.course-link').forEach(function(el) {
		el.addEventListener('click', function(e) {
			e.preventDefault();
			const cours = this.getAttribute('data-cours');
			const lien = this.getAttribute('data-lien');
			if (lien) {
				showEnrolledUsers(cours, lien);
			} else {
				document.getElementById('course-content').innerHTML = `<div class='alert alert-warning'>Aucun lien de cours trouvé.</div>`;
			}
		});
	});

	function showEnrolledUsers(courseName, courseUrl) {
		document.getElementById('course-content').innerHTML = `<div class='alert alert-info'>Chargement des utilisateurs pour <strong>${courseName}</strong>...</div>`;
		fetch('/get_enrolled_users', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ course_url: courseUrl })
		})
		.then(response => response.json())
		.then(data => {
			if (data.error) {
				document.getElementById('course-content').innerHTML = `<div class='alert alert-danger'>Erreur : ${data.error}</div>`;
			} else if (data.users && data.users.length > 0) {
				// Récupérer la liste unique des départements
				const departments = [...new Set(data.users.map(u => u.departement).filter(Boolean))].sort();
				// Récupérer la liste unique des statuts
				const statuses = [...new Set(data.users.map(u => u.status).filter(Boolean))].sort();
				// Filtres HTML améliorés dans une carte
				let html = `<div class='alert alert-success'>Utilisateurs inscrits pour <strong>${courseName}</strong> :</div>`;
				html += `<div class="filter-card mb-3 p-3">
					<div class="row g-3 align-items-end">
						<div class="col-md-4">
							<label for="course-dept-filter" class="form-label"><i class="bi bi-building"></i> Département</label>
							<select id="course-dept-filter" class="form-select filter-select">
								<option value="">Tous les départements</option>
								${departments.map(dept => `<option value="${dept}">${dept}</option>`).join('')}
							</select>
						</div>
						<div class="col-md-4">
							<label for="course-rows-per-page" class="form-label"><i class="bi bi-list-ol"></i> Lignes par page</label>
							<select id="course-rows-per-page" class="form-select filter-select">
								<option value="10">10</option>
								<option value="25">25</option>
								<option value="50">50</option>
								<option value="100">100</option>
							</select>
						</div>
						<div class="col-md-4">
							<label for="course-status-filter" class="form-label"><i class="bi bi-person-badge"></i> Statut</label>
							<select id="course-status-filter" class="form-select filter-select">
								<option value="">Tous les statuts</option>
								${statuses.map(st => `<option value="${st}">${st}</option>`).join('')}
							</select>
						</div>
					</div>
				</div>`;
				html += `<div class="table-responsive analysis-container course-users-table-container" style="box-shadow: 0 4px 18px 0 rgba(80, 112, 255, 0.08); background: #fff; border-radius: 16px; margin-top: 1.5rem;">
				<table class='table table-bordered table-striped mb-0' id='course-users-table' style="border-radius: 16px; overflow: hidden;">
				<thead class="table-primary">
				<tr><th>Nom</th><th>Matricule</th><th>Département</th><th>Statut</th></tr></thead><tbody>`;
				data.users.forEach(u => {
					html += `<tr><td>${u.full_name || ''}</td><td>${u.matricule || ''}</td><td>${u.departement || ''}</td><td>${u.status || ''}</td></tr>`;
				});
				html += `</tbody></table></div>`;
				html += `<div class="d-flex justify-content-between align-items-center mt-2">
					<button class="btn btn-sm btn-outline-secondary" id="course-prev-page">&lt;</button>
					<span id="course-pagination-info"></span>
					<button class="btn btn-sm btn-outline-secondary" id="course-next-page">&gt;</button>
				</div>`;
				document.getElementById('course-content').innerHTML = html;

				// --- JS pour filtrage/pagination (ISOLÉ pour la table dynamique) ---
				(function() {
					const table = document.getElementById('course-users-table');
					if (!table) return;
					const tbody = table.querySelector('tbody');
					let allRows = Array.from(tbody.querySelectorAll('tr'));
					let filteredRows = allRows;
					let currentPage = 1;
					let rowsPerPage = 10;

					function filterRows() {
						const dept = document.getElementById('course-dept-filter').value;
						const status = document.getElementById('course-status-filter').value;
						filteredRows = allRows.filter(row => {
							const tds = row.children;
							const matchDept = !dept || tds[2].textContent.trim() === dept;
							const matchStatus = !status || tds[3].textContent.trim() === status;
							return matchDept && matchStatus;
						});
						currentPage = 1;
						updatePagination();
					}

					function updatePagination() {
						rowsPerPage = parseInt(document.getElementById('course-rows-per-page').value);
						const total = filteredRows.length;
						const totalPages = Math.ceil(total / rowsPerPage) || 1;
						if (currentPage > totalPages) currentPage = totalPages;
						const startIdx = (currentPage - 1) * rowsPerPage;
						const endIdx = startIdx + rowsPerPage;
						allRows.forEach(row => row.style.display = 'none');
						filteredRows.slice(startIdx, endIdx).forEach(row => row.style.display = '');
						// Pagination info
						const info = document.getElementById('course-pagination-info');
						if (info) {
							info.textContent = `Page ${currentPage} / ${totalPages} (${total} utilisateurs)`;
						}
						document.getElementById('course-prev-page').disabled = currentPage === 1;
						document.getElementById('course-next-page').disabled = currentPage === totalPages;
					}

					document.getElementById('course-dept-filter').addEventListener('change', filterRows);
					document.getElementById('course-status-filter').addEventListener('change', filterRows);
					document.getElementById('course-rows-per-page').addEventListener('change', function() {
						currentPage = 1;
						updatePagination();
					});
					document.getElementById('course-prev-page').addEventListener('click', function() {
						if (currentPage > 1) {
							currentPage--;
							updatePagination();
						}
					});
					document.getElementById('course-next-page').addEventListener('click', function() {
						const total = filteredRows.length;
						const totalPages = Math.ceil(total / rowsPerPage) || 1;
						if (currentPage < totalPages) {
							currentPage++;
							updatePagination();
						}
					});
					// Initial display
					filterRows();
				})();
			} else {
				document.getElementById('course-content').innerHTML = `<div class='alert alert-warning'>Aucun utilisateur inscrit trouvé pour ce cours.</div>`;
			}
		})
		.catch(err => {
			document.getElementById('course-content').innerHTML = `<div class='alert alert-danger'>Erreur lors de la récupération des utilisateurs.</div>`;
		});
	}

	// Table utilisateurs: filtrage et pagination
	const departmentFilter = document.getElementById('department-filter');
	const projetFilter = document.getElementById('projet-filter');
	const contratFilter = document.getElementById('contrat-filter');
	const rowsPerPageSelect = document.getElementById('rows-per-page');
	const startRangeSelect = document.getElementById('start-range');
	const prevPageBtn = document.getElementById('prev-page');
	const nextPageBtn = document.getElementById('next-page');
	const userTable = document.querySelector('.extract-container table');
	const matriculeSearch = document.getElementById('matricule-search');
	let allRows = Array.from(userTable.querySelectorAll('tbody tr'));
	let filteredRows = allRows;
	let currentPage = 1;
	let rowsPerPage = parseInt(rowsPerPageSelect.value);

	function filterRows() {
		const dept = departmentFilter.value;
		const projet = projetFilter.value;
		const contrat = contratFilter.value;
		const matricule = matriculeSearch ? matriculeSearch.value.trim().toLowerCase() : '';
		filteredRows = allRows.filter(row => {
			// Index: 0 = matricule, 3 = projet_actuel, 5 = type_contrat, 6 = departement_actuel
			if (row.children.length < 7) return true;
			let matchDept = !dept || row.children[6].textContent.trim() === dept;
			let matchProjet = !projet || row.children[3].textContent.trim() === projet;
			let matchContrat = !contrat || row.children[5].textContent.trim() === contrat;
			let matchMatricule = !matricule || row.children[0].textContent.trim().toLowerCase().includes(matricule);
			return matchDept && matchProjet && matchContrat && matchMatricule;
		});
		currentPage = 1;
		updatePagination();
	}

	function updatePagination() {
		rowsPerPage = parseInt(rowsPerPageSelect.value);
		const total = filteredRows.length;
		const totalPages = Math.ceil(total / rowsPerPage) || 1;
		if (currentPage > totalPages) currentPage = totalPages;
		const startIdx = (currentPage - 1) * rowsPerPage;
		const endIdx = startIdx + rowsPerPage;
		allRows.forEach(row => row.style.display = 'none');
		filteredRows.slice(startIdx, endIdx).forEach(row => row.style.display = '');
		// Update start-range select
		startRangeSelect.innerHTML = '';
		for (let i = 1; i <= total; i += rowsPerPage) {
			const end = Math.min(i + rowsPerPage - 1, total);
			const opt = document.createElement('option');
			opt.value = i;
			opt.textContent = `${i}-${end}`;
			startRangeSelect.appendChild(opt);
		}
		startRangeSelect.value = (startIdx + 1).toString();
		// Disable/enable prev/next
		prevPageBtn.disabled = currentPage === 1;
		nextPageBtn.disabled = currentPage === totalPages;
	}

	departmentFilter.addEventListener('change', filterRows);
	projetFilter.addEventListener('change', filterRows);
	contratFilter.addEventListener('change', filterRows);
	if (matriculeSearch) {
		matriculeSearch.addEventListener('input', filterRows);
	}
	rowsPerPageSelect.addEventListener('change', function() {
		currentPage = 1;
		updatePagination();
	});
	startRangeSelect.addEventListener('change', function() {
		const idx = parseInt(this.value) - 1;
		currentPage = Math.floor(idx / rowsPerPage) + 1;
		updatePagination();
	});
	prevPageBtn.addEventListener('click', function() {
		if (currentPage > 1) {
			currentPage--;
			updatePagination();
		}
	});
	nextPageBtn.addEventListener('click', function() {
		const total = filteredRows.length;
		const totalPages = Math.ceil(total / rowsPerPage) || 1;
		if (currentPage < totalPages) {
			currentPage++;
			updatePagination();
		}
	});

	// Initial display
	filterRows();
});
