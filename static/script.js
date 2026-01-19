

// Theme toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    const htmlElement = document.documentElement;
    const body = document.body;
    
    // Check for saved theme preference or default to light mode
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Apply saved theme on load
    if (currentTheme === 'dark') {
        body.classList.add('dark-mode');
        if (themeToggle) {
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        }
    }
    
    // Toggle theme on button click
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            body.classList.toggle('dark-mode');
            const isDarkMode = body.classList.contains('dark-mode');
            
            // Update button icon
            themeToggle.innerHTML = isDarkMode 
                ? '<i class="fas fa-sun"></i>' 
                : '<i class="fas fa-moon"></i>';
            
            // Save preference
            localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    if (!form) return;

    const fileInput = document.getElementById('fileUpload');
    const progress = document.getElementById('uploadProgress');
    const progressContainer = document.getElementById('uploadProgressContainer');
    const progressText = document.getElementById('uploadProgressText');
    const uploadBtn = document.getElementById('uploadBtn');

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        // include reusable checkbox if present
        const reusable = form.querySelector('input[name="reusable"]');
        if (reusable && reusable.checked) formData.append('reusable', 'on');

        const xhr = new XMLHttpRequest();
        xhr.open('POST', form.getAttribute('action'));

        xhr.upload.addEventListener('progress', function(ev) {
            if (ev.lengthComputable) {
                const percent = Math.round((ev.loaded / ev.total) * 100);
                if (progress) {
                    if (progressContainer) progressContainer.style.display = 'block';
                    progress.style.width = percent + '%';
                    progress.setAttribute('aria-valuenow', percent);
                    progress.textContent = percent + '%';
                }
                if (progressText) {
                    progressText.style.display = 'block';
                    progressText.textContent = percent + '%';
                }
                if (uploadBtn) {
                    uploadBtn.classList.add('yellowBtn');
                    uploadBtn.value = '· · ·';
                    uploadBtn.disabled = true;
                }
            }
        });

        xhr.addEventListener('load', function() {
            if (xhr.status >= 200 && xhr.status < 400) {
                // Try to extract flash messages from the returned HTML and inject them
                try {
                    const tmp = document.createElement('div');
                    tmp.innerHTML = xhr.responseText;
                    const newFlashes = tmp.querySelector('ul.flashes');
                    const oldFlashes = document.querySelector('ul.flashes');
                    if (newFlashes) {
                        if (oldFlashes) oldFlashes.replaceWith(newFlashes);
                        else document.body.insertBefore(newFlashes, document.body.firstChild);
                    } else {
                        // fallback to full reload if no flashes present
                        window.location.href = '/upload';
                        return;
                    }
                } catch (e) {
                    window.location.href = '/upload';
                    return;
                    } finally {
                    if (uploadBtn) {
                        uploadBtn.disabled = false;
                        uploadBtn.classList.remove('yellowBtn');
                        uploadBtn.value = 'Upload';
                    }
                    if (progress) {
                        if (progressContainer) progressContainer.style.display = 'none';
                        progress.style.width = '0%';
                        progress.setAttribute('aria-valuenow', 0);
                        progress.textContent = '0%';
                    }
                    if (progressText) { progressText.style.display = 'none'; progressText.textContent = '0%'; }
                    // clear file input and reusable checkbox after successful upload
                    if (fileInput) fileInput.value = '';
                    if (reusable && reusable.checked) reusable.checked = false;
                }
                } else {
                // error
                if (progressText) progressText.textContent = 'Upload failed';
                if (uploadBtn) {
                    uploadBtn.disabled = false;
                    uploadBtn.classList.remove('yellowBtn');
                    uploadBtn.value = 'Upload';
                }
                if (fileInput) fileInput.value = '';
                if (progress) { progress.style.display = 'none'; progress.value = 0; }
                if (progressText) progressText.style.display = 'none';
            }
        });

        xhr.addEventListener('error', function() {
            if (progressText) progressText.textContent = 'Upload error';
            if (uploadBtn) {
                uploadBtn.disabled = false;
                uploadBtn.classList.remove('yellowBtn');
                uploadBtn.value = 'Upload';
            }
            if (fileInput) fileInput.value = '';
            if (progress) {
                if (progressContainer) progressContainer.style.display = 'none';
                progress.style.width = '0%';
                progress.setAttribute('aria-valuenow', 0);
                progress.textContent = '0%';
            }
            if (progressText) progressText.style.display = 'none';
        });

        xhr.send(formData);
    });
});