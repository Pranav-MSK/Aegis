let currentDir = '';
let currentFile = '';
let page = 1;
let loading = false;
let hasMore = true;
let totalLinesLoaded = 0;

const loadingSpinner = document.getElementById('loadingSpinner');
const logStats = document.getElementById('logStats');
const logsContainer = document.getElementById('logsContainer');
const logContent = document.getElementById('logContent');
const directorySelect = document.getElementById('directorySelect');
const scrollToBottom = document.getElementById('scrollToBottom');

// Scroll to bottom button handler
scrollToBottom.addEventListener('click', () => {
    logContent.scrollTop = logContent.scrollHeight;
});

// Show/hide scroll to bottom button based on scroll position
logContent.addEventListener('scroll', () => {
    const threshold = 100;
    const bottomDistance = logContent.scrollHeight - (logContent.scrollTop + logContent.clientHeight);
    scrollToBottom.classList.toggle('hidden', bottomDistance <= threshold);
});

// Intersection Observer for infinite scroll
const observer = new IntersectionObserver(
    (entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && hasMore && !loading && currentFile) {
                page++;
                loadLogs(currentDir, currentFile, page, true);
            }
        });
    },
    { threshold: 0.1 }
);

        
async function fetchDirectories() {
    try {
        const response = await fetch('/api/v1/logger/directories');
        const directories = await response.json();
        directorySelect.innerHTML = '<option value="">Select Directory</option>';
        directories.forEach(dir => {
            const option = document.createElement('option');
            option.value = dir.path;
            option.textContent = dir.name;
            directorySelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error fetching directories:', error);
    }
}

directorySelect.addEventListener('change', (e) => {
    currentDir = e.target.value;
    if (currentDir) {
        fetchLogFiles(currentDir);
    }
});

function formatFileSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

async function fetchLogFiles(directory) {
    try {
        const response = await fetch(`/api/v1/logfiles?directory=${encodeURIComponent(directory)}`);
        const logFiles = await response.json();
        const logFilesList = document.getElementById('logFilesList');
        logFilesList.innerHTML = '';

        document.getElementById('fileCount').textContent = `${logFiles.length} files`;

        logFiles.forEach(file => {
            const fileDiv = document.createElement('div');
            fileDiv.className = 'directory-item hover:bg-gray-50 cursor-pointer transition-colors';
            fileDiv.innerHTML = `
                <div class="p-4" onclick="selectLogFile('${file.name}')">
                    <div class="flex items-center justify-between">
                        <div class="min-w-0 flex-1">
                            <p class="text-sm font-medium text-gray-900 truncate">${file.name}</p>
                            <p class="text-xs text-gray-500 mt-1">
                                ${new Date(file.modified).toLocaleString()}
                            </p>
                        </div>
                        <div class="ml-4">
                            <span class="text-xs text-gray-500 file-size">${formatFileSize(file.size)}</span>
                        </div>
                    </div>
                </div>
            `;
            logFilesList.appendChild(fileDiv);
        });
    } catch (error) {
        console.error('Error fetching log files:', error);
    }
}

async function loadLogs(directory, filename, pageNum, append = true) {
    if (loading) return;
    
    loading = true;
    loadingSpinner.classList.remove('hidden');
    
    try {
        const filePath = `${directory}/${filename}`;
        const response = await fetch(`/api/v1/logs/${encodeURIComponent(filePath)}?page=${pageNum}`);
        const data = await response.json();

        if (!append) {
            logsContainer.innerHTML = '';
            totalLinesLoaded = 0;
        }

        // Add new log entries
        data.content.reverse().forEach(log => {
            const logEntry = document.createElement('div');
            logEntry.className = 'text-sm text-gray-800 font-mono hover:bg-gray-50 rounded px-2 py-1';
            logEntry.textContent = log;
            logsContainer.appendChild(logEntry);
        });

        totalLinesLoaded += data.content.length;
        logStats.textContent = `${totalLinesLoaded} lines loaded`;

        hasMore = data.has_more;

        if (!hasMore) {
            const endMarker = document.createElement('div');
            endMarker.className = 'text-center text-gray-500 text-sm py-4';
            endMarker.textContent = 'End of logs';
            logsContainer.appendChild(endMarker);
        } else {
            // Add sentinel element for infinite scroll
            const sentinel = document.createElement('div');
            sentinel.id = 'sentinel';
            sentinel.style.height = '20px';
            logsContainer.appendChild(sentinel);
            observer.observe(sentinel);
        }

        // Update file size in header
        document.getElementById('fileSize').textContent = formatFileSize(data.total_size);
    } catch (error) {
        console.error('Error loading logs:', error);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-red-500 text-sm text-center py-4';
        errorDiv.textContent = 'Error loading logs. Please try again.';
        logsContainer.appendChild(errorDiv);
    } finally {
        loading = false;
        loadingSpinner.classList.add('hidden');
    }
}

function selectLogFile(filename) {
    currentFile = filename;
    page = 1;
    hasMore = true;
    document.getElementById('currentFileName').textContent = filename;
    document.getElementById('defaultMessage').style.display = 'none';
    loadLogs(currentDir, filename, page, false);

    setInterval(() => {
        if (currentFile && currentDir && page === 1) {
            loadLogs(currentDir, currentFile, 1, false);
        }
        fetchLogFiles(currentDir);
    }, 3000);
}

function reloadCurrentView() {
    if (currentDir) {
        fetchLogFiles(currentDir);
        if (currentFile) {
            loadLogs(currentDir, currentFile, 1, false);
        }
    }
}

document.getElementById('viewLogFileButton').addEventListener('click', () => {
    const filePath = document.getElementById('filePathInput').value.trim();
    if (filePath) {
        // Extract the directory from the file path
        const directory = filePath.substring(0, filePath.lastIndexOf('/'));
        currentDir = directory; // Set currentDir for further operations

        // Extract the filename
        currentFile = filePath.substring(filePath.lastIndexOf('/') + 1);

        // Load logs from the specified file path
        document.getElementById('defaultMessage').style.display = 'none';
        loadLogs(directory, currentFile, 1, false);
    } else {
        alert('Please enter a valid file path.');
    }
});

function isValidFilePath(filePath) {
    // Simple regex to check for valid file path
    const regex = /^(\/[^\/]+)+\/[^\/]+(\.[a-z0-9]+)?$/i;
    return regex.test(filePath);
}

document.getElementById('viewLogFileButton').addEventListener('click', () => {
    const filePath = document.getElementById('filePathInput').value.trim();
    if (isValidFilePath(filePath)) {
        // Proceed with loading logs...
    } else {
        alert('Please enter a valid file path.');
    }
});


// Initial load
document.addEventListener('DOMContentLoaded', fetchDirectories);

// Auto-refresh logs every 30 seconds if a file is selected and on first page
setInterval(() => {
    if (currentFile && currentDir && page === 1) {
        loadLogs(currentDir, currentFile, 1, false);
    }
}, 30000);


document.getElementById('addDirectoryButton').addEventListener('click', function () {
    // Show the form
    document.getElementById('directoryForm').style.display = 'block';
});


document.getElementById('submitDirectory').addEventListener('click', function () {
    const directoryPath = document.getElementById('directoryPath').value;
    if (directoryPath) {
        fetch('/api/v1/logger/directories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path: directoryPath })
        })
        .then(response => {
            console.log('Response status:', response.status);
            return response.text().then(text => {
                if (!response.ok) {
                    throw new Error(text);
                }
                return JSON.parse(text);
            });
        })
        .then(data => {
            alert('Directory added successfully');
            // Refresh the directory list
            fetchDirectories();
            document.getElementById('directoryForm').style.display = 'none'; // Hide the form
            document.getElementById('directoryPath').value = ''; // Clear the input
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`An error occurred while adding the directory: ${error.message}`);
        });
    } else {
        alert('Please enter a valid directory path.');
    }
});

document.getElementById('deleteDirectoryButton').addEventListener('click', function () {
    const directoryPath = directorySelect.value; // Get the selected directory
    if (directoryPath) {
        fetch('/api/v1/logger/directories', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path: directoryPath })
        })
        .then(response => {
            console.log('Response status:', response.status);
            return response.text().then(text => {
                if (!response.ok) {
                    throw new Error(text);
                }
                return JSON.parse(text);
            });
        })
        .then(data => {
            alert('Directory deleted successfully');
            // Refresh the directory list
            fetchDirectories();
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`An error occurred while deleting the directory: ${error.message}`);
        });
    } else {
        alert('Please select a directory to delete.');
    }
});
