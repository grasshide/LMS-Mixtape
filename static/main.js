// JavaScript for Music Export Tool
let songs = [];
let selectedSongs = new Set();

// Utility functions
function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alerts');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    const icon = type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info';
    alert.innerHTML = `<span class="material-icons">${icon}</span> ${message}`;
    alertsContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds with slide-out animation
    setTimeout(() => {
        alert.classList.add('removing');
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 300); // Wait for animation to complete
    }, 5000);
}

function updateStats() {
    document.getElementById('totalSongs').textContent = songs.length;
    document.getElementById('selectedSongs').textContent = selectedSongs.size;
}

function renderStars(rating) {
    const fullStars = Math.floor(rating / 20);
    const halfStar = (rating % 20) >= 10 ? 1 : 0;
    let html = '';
    for (let i = 0; i < 5; i++) {
        if (i < fullStars) {
            html += `<svg class="star" width="24" height="24" viewBox="0 0 24 24" fill="#6200ee" stroke="#6200ee" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><polygon points="12,2 15,9 22,9.3 17,14.1 18.5,21 12,17.8 5.5,21 7,14.1 2,9.3 9,9"/></svg>`;
        } else if (i === fullStars && halfStar) {
            html += `<svg class="star" width="24" height="24" viewBox="0 0 24 24"><defs><linearGradient id="half"><stop offset="50%" stop-color="#6200ee"/><stop offset="50%" stop-color="white" stop-opacity="0"/></linearGradient></defs><polygon points="12,2 15,9 22,9.3 17,14.1 18.5,21 12,17.8 5.5,21 7,14.1 2,9.3 9,9" fill="url(#half)" stroke="#6200ee" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
        } else {
            html += `<svg class="star" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6200ee" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><polygon points="12,2 15,9 22,9.3 17,14.1 18.5,21 12,17.8 5.5,21 7,14.1 2,9.3 9,9"/></svg>`;
        }
    }
    return html;
}

function renderSongs() {
    const container = document.getElementById('songsContainer');
    container.innerHTML = '';
    songs.forEach((song, index) => {
        const songElement = document.createElement('div');
        songElement.className = `song-item ${selectedSongs.has(index) ? 'selected' : ''}`;
        songElement.setAttribute('data-index', index);
        songElement.innerHTML = `
            <img class="song-cover" src="${song.cover_url}" alt="Cover" onerror="this.onerror=null;this.src='/static/default-cover.png';">
            <div class="song-info">
                <div class="song-title">${song.title || 'Unknown Title'}</div>
                <div class="song-details">
                    <strong>Artist:</strong> ${song.artist || 'Unknown Artist'} | 
                    <strong>Album:</strong> ${song.album || 'Unknown Album'} | 
                    <strong>Genre:</strong> ${song.genre || 'Unknown Genre'}
                    ${song.dyn_ps_val !== null && song.dyn_ps_val !== 0 ? ` | <strong>Dynamic Counter:</strong> ${song.dyn_ps_val}` : ''}
                </div>
            </div>
            <div class="song-rating">
                <div class="rating-stars">${renderStars(song.rating)}</div>
            </div>
        `;
        container.appendChild(songElement);
    });
    updateStats();
}

function renderRatingPicker(value) {
    // value: 0-100, but we want exactly 5 stars, each clickable for different values
    const container = document.getElementById('ratingPicker');
    container.innerHTML = '';
    const stars = 5;
    const starValue = value / 20; // 0-5 in 0.5 steps
    
    // Get the theme color from CSS custom property
    const themeColor = getComputedStyle(document.documentElement).getPropertyValue('--mdc-theme-on-surface').trim() || '#111';
    
    // Add a "no rating" option (0 stars) at the beginning
    const noRatingSvg = `<svg class="star-picker" data-value="0" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="${themeColor}" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" style="cursor:pointer; margin-right: 8px;"><polygon points="12,2 15,9 22,9.3 17,14.1 18.5,21 12,17.8 5.5,21 7,14.1 2,9.3 9,9"/></svg>`;
    container.innerHTML = noRatingSvg;
    
    // Create exactly 5 stars, each clickable for different values
    for (let i = 1; i <= stars; i++) {
        const starValueForThisStar = i * 20; // 20, 40, 60, 80, 100
        const currentStarValue = i; // 1, 2, 3, 4, 5
        
        let starType = 'empty';
        if (starValue >= currentStarValue) {
            starType = 'full';
        } else if (starValue >= currentStarValue - 0.5) {
            starType = 'half';
        }
        
        let svg = '';
        if (starType === 'full') {
            svg = `<svg class="star-picker" data-value="${starValueForThisStar}" width="28" height="28" viewBox="0 0 24 24" fill="${themeColor}" stroke="${themeColor}" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" style="cursor:pointer;"><polygon points="12,2 15,9 22,9.3 17,14.1 18.5,21 12,17.8 5.5,21 7,14.1 2,9.3 9,9"/></svg>`;
        } else if (starType === 'half') {
            svg = `<svg class="star-picker" data-value="${starValueForThisStar}" width="28" height="28" viewBox="0 0 24 24" style="cursor:pointer;"><defs><linearGradient id="half-theme-${i}"><stop offset="50%" stop-color="${themeColor}"/><stop offset="50%" stop-color="white" stop-opacity="0"/></linearGradient></defs><polygon points="12,2 15,9 22,9.3 17,14.1 18.5,21 12,17.8 5.5,21 7,14.1 2,9.3 9,9" fill="url(#half-theme-${i})" stroke="${themeColor}" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
        } else {
            svg = `<svg class="star-picker" data-value="${starValueForThisStar}" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="${themeColor}" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" style="cursor:pointer;"><polygon points="12,2 15,9 22,9.3 17,14.1 18.5,21 12,17.8 5.5,21 7,14.1 2,9.3 9,9"/></svg>`;
        }
        container.innerHTML += svg;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('searchBtn').addEventListener('click', async () => {
        const rating = parseInt(document.getElementById('rating').value);
        const limit = parseInt(document.getElementById('limit').value);
        const excludeGenres = document.getElementById('excludeGenres').value.split(',').map(s => s.trim()).filter(s => s);
        const dynPsVal = parseInt(document.getElementById('dynPsVal').value);
        const albumLimit = parseInt(document.getElementById('albumLimit').value);
        const randomize = document.getElementById('randomize').checked;
        const addedBefore = document.getElementById('addedBefore').value;
        let addedBeforeTimestamp = null;
        if (addedBefore) {
            // Convert YYYY-MM-DD to Unix timestamp (seconds)
            addedBeforeTimestamp = Math.floor(new Date(addedBefore + 'T00:00:00').getTime() / 1000);
        }
        document.getElementById('dynPsValValue').textContent = dynPsVal;
        document.getElementById('albumLimitValue').textContent = albumLimit;
        document.getElementById('searchBtn').disabled = true;
        document.getElementById('searchBtn').innerHTML = '<span class="material-icons rotating">refresh</span> Searching...';
        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    rating,
                    limit,
                    exclude_genres: excludeGenres,
                    dyn_ps_val: dynPsVal === 0 ? null : dynPsVal,
                    album_limit: albumLimit === 0 ? null : albumLimit,
                    randomize: randomize,
                    added_before: addedBeforeTimestamp
                })
            });
            const data = await response.json();
            if (data.success) {
                songs = data.songs;
                selectedSongs.clear();
                renderSongs();
                document.getElementById('resultsCard').style.display = 'block';
                document.getElementById('exportCard').style.display = 'block';
                showAlert(`Found ${data.count} songs!`, 'success');
            } else {
                showAlert(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            showAlert(`Network error: ${error.message}`, 'error');
        } finally {
            document.getElementById('searchBtn').disabled = false;
            document.getElementById('searchBtn').innerHTML = '<span class="material-icons">search</span> Search Songs';
        }
    });

    document.getElementById('songsContainer').addEventListener('click', (e) => {
        const songItem = e.target.closest('.song-item');
        if (!songItem) return;
        const index = parseInt(songItem.getAttribute('data-index'));
        if (selectedSongs.has(index)) {
            selectedSongs.delete(index);
            songItem.classList.remove('selected');
        } else {
            selectedSongs.add(index);
            songItem.classList.add('selected');
        }
        updateStats();
    });

    document.getElementById('selectAllBtn').addEventListener('click', () => {
        selectedSongs.clear();
        songs.forEach((_, index) => selectedSongs.add(index));
        renderSongs();
    });

    document.getElementById('deselectAllBtn').addEventListener('click', () => {
        selectedSongs.clear();
        renderSongs();
    });

    // Function to toggle embed covers checkbox visibility
    function toggleEmbedCoversVisibility() {
        const exportFormat = document.querySelector('input[name="exportFormat"]:checked').value;
        const embedCoversCheckbox = document.getElementById('embedCovers');
        const syncFolderCheckbox = document.getElementById('syncFolder');
        
        if (exportFormat === 'zip') {
            // Hide embed covers option for ZIP format
            if (embedCoversCheckbox) {
                embedCoversCheckbox.closest('.checkbox-option').style.display = 'none';
            }
            // Hide sync folder option for ZIP format
            if (syncFolderCheckbox) {
                syncFolderCheckbox.closest('.checkbox-option').style.display = 'none';
            }
        } else {
            // Show embed covers option for folder format
            if (embedCoversCheckbox) {
                embedCoversCheckbox.closest('.checkbox-option').style.display = 'flex';
            }
            // Show sync folder option for folder format
            if (syncFolderCheckbox) {
                syncFolderCheckbox.closest('.checkbox-option').style.display = 'flex';
            }
        }
    }

    // Add event listeners to export format radio buttons
    document.querySelectorAll('input[name="exportFormat"]').forEach(radio => {
        radio.addEventListener('change', toggleEmbedCoversVisibility);
    });

    // Initial call to set correct visibility
    toggleEmbedCoversVisibility();

    document.getElementById('exportBtn').addEventListener('click', async () => {
        if (selectedSongs.size === 0) {
            showAlert('Please select at least one song to export.', 'error');
            return;
        }
        
        // Remove any existing download links
        const existingDownloadLinks = document.querySelectorAll('#exportCard a[href^="/api/download/"]');
        existingDownloadLinks.forEach(link => link.remove());
        
        const exportFormat = document.querySelector('input[name="exportFormat"]:checked').value;
        const embedCovers = document.getElementById('embedCovers').checked;
        const renameFiles = document.getElementById('renameFiles').checked;
        const syncFolder = document.getElementById('syncFolder').checked;
        const selectedSongsList = Array.from(selectedSongs).map(index => songs[index]);
        document.getElementById('exportBtn').disabled = true;
        document.getElementById('exportBtn').innerHTML = '<span class="material-icons rotating">refresh</span> Exporting...';
        try {
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    songs: selectedSongsList,
                    format: exportFormat,
                    embed_covers: embedCovers,
                    rename_files: renameFiles,
                    sync_folder: syncFolder
                })
            });
            const data = await response.json();
            if (data.success) {
                showAlert(`Successfully exported ${selectedSongs.size} songs!`, 'success');
                
                // Only create download link for ZIP format
                if (exportFormat === 'zip') {
                    const filename = data.export_path.split('/').pop();
                    const downloadLink = document.createElement('a');
                    downloadLink.href = `/api/download/${filename}`;
                    downloadLink.download = filename;
                    downloadLink.className = 'btn btn-success';
                    downloadLink.innerHTML = '<span class="material-icons">download</span> Download Export';
                    downloadLink.style.marginTop = '10px';
                    document.getElementById('exportCard').appendChild(downloadLink);
                }
            } else {
                showAlert(`Export error: ${data.error}`, 'error');
            }
        } catch (error) {
            showAlert(`Network error: ${error.message}`, 'error');
        } finally {
            document.getElementById('exportBtn').disabled = false;
            document.getElementById('exportBtn').innerHTML = '<span class="material-icons">download</span> Export Selected Songs';
        }
    });

    // Star rating picker logic
    const ratingInput = document.getElementById('rating');
    let currentRating = parseInt(ratingInput.value);
    renderRatingPicker(currentRating);
    document.getElementById('ratingPicker').addEventListener('mousemove', function(e) {
        if (e.target.closest('.star-picker')) {
            const val = parseInt(e.target.closest('.star-picker').getAttribute('data-value'));
            renderRatingPicker(val);
        }
    });
    document.getElementById('ratingPicker').addEventListener('mouseleave', function() {
        renderRatingPicker(currentRating);
    });
    document.getElementById('ratingPicker').addEventListener('click', function(e) {
        if (e.target.closest('.star-picker')) {
            const val = parseInt(e.target.closest('.star-picker').getAttribute('data-value'));
            currentRating = val;
            ratingInput.value = val;
            renderRatingPicker(currentRating);
        }
    });
}); 