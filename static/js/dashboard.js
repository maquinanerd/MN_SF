// Dashboard JavaScript Functions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    initializeDashboard();
    
    // Update current time
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    
    // Auto-refresh data every 30 seconds
    setInterval(refreshDashboardData, 30000);
    
    // Initialize event listeners
    initializeEventListeners();
});

function initializeDashboard() {
    console.log('Content Automation Dashboard initialized');
    
    // Check if we're on the dashboard page
    if (window.location.pathname === '/') {
        loadInitialData();
    }
}

function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString('pt-BR', {
        timeZone: 'America/Sao_Paulo',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
    
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}

function refreshDashboardData() {
    // Refresh statistics
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            updateStatistics(data);
        })
        .catch(error => {
            console.error('Error refreshing statistics:', error);
        });
    
    // Refresh scheduler status
    fetch('/api/scheduler-status')
        .then(response => response.json())
        .then(data => {
            updateSchedulerStatus(data);
        })
        .catch(error => {
            console.error('Error refreshing scheduler status:', error);
        });
    
    // Refresh AI status
    fetch('/api/ai-status')
        .then(response => response.json())
        .then(data => {
            updateAIStatus(data);
        })
        .catch(error => {
            console.error('Error refreshing AI status:', error);
        });
}

function updateStatistics(data) {
    // Update statistics cards if they exist
    const statsCards = document.querySelectorAll('.card h4');
    if (statsCards.length >= 4) {
        statsCards[0].textContent = data.total_articles || 0;
        statsCards[1].textContent = data.pending_articles || 0;
        statsCards[2].textContent = data.processed_articles || 0;
        statsCards[3].textContent = data.published_articles || 0;
    }
}

function updateSchedulerStatus(data) {
    const statusElement = document.getElementById('schedulerStatus');
    if (statusElement) {
        if (data.running) {
            statusElement.innerHTML = '<span class="text-success">Ativo</span>';
        } else {
            statusElement.innerHTML = '<span class="text-danger">Parado</span>';
        }
    }
    
    // Update next execution time
    if (data.jobs && data.jobs.length > 0) {
        const automationJob = data.jobs.find(job => job.id === 'automation_cycle');
        if (automationJob && automationJob.next_run) {
            nextRunTime = automationJob.next_run;
            updateCountdown(automationJob.next_run);
        }
    }
}

function updateCountdown(nextRunTime) {
    const nextExecTime = document.getElementById('next-execution-time');
    const countdownTimer = document.getElementById('countdown-timer');
    
    if (!nextExecTime || !countdownTimer) return;
    
    const nextRun = new Date(nextRunTime);
    const now = new Date();
    const timeDiff = nextRun - now;
    
    // Update next execution time display
    nextExecTime.textContent = nextRun.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    if (timeDiff > 0) {
        const minutes = Math.floor(timeDiff / 60000);
        const seconds = Math.floor((timeDiff % 60000) / 1000);
        
        if (minutes > 0) {
            countdownTimer.textContent = `${minutes}m ${seconds}s`;
        } else {
            countdownTimer.textContent = `${seconds}s`;
        }
        
        // Change color based on time remaining
        const countdownDiv = document.getElementById('next-execution-countdown');
        if (minutes < 1) {
            countdownDiv.className = 'text-danger fw-bold fs-5';
        } else if (minutes < 5) {
            countdownDiv.className = 'text-warning fw-bold fs-5';
        } else {
            countdownDiv.className = 'text-success fw-bold fs-5';
        }
    } else {
        countdownTimer.textContent = 'Executando...';
        const countdownDiv = document.getElementById('next-execution-countdown');
        countdownDiv.className = 'text-info fw-bold fs-5';
    }
}

// Store next run time globally to avoid constant API calls
let nextRunTime = null;

// Update countdown every second using stored time
setInterval(() => {
    if (nextRunTime) {
        updateCountdown(nextRunTime);
    }
}, 1000);

// Update next run time every 30 seconds via API
setInterval(() => {
    fetch('/api/scheduler-status')
        .then(response => response.json())
        .then(data => {
            if (data.jobs && data.jobs.length > 0) {
                const automationJob = data.jobs.find(job => job.id === 'automation_cycle');
                if (automationJob && automationJob.next_run) {
                    nextRunTime = automationJob.next_run;
                }
            }
        })
        .catch(error => console.error('Error updating next run time:', error));
}, 30000);

function updateAIStatus(data) {
    // Update AI status indicators
    console.log('AI Status updated:', data);
}

function loadInitialData() {
    // Load initial dashboard data
    refreshDashboardData();
}

function initializeEventListeners() {
    // Execute Now button
    const executeNowBtn = document.getElementById('executeNowBtn');
    if (executeNowBtn) {
        executeNowBtn.addEventListener('click', function() {
            executeAutomationNow();
        });
    }
    
    // Pause button
    const pauseBtn = document.getElementById('pauseBtn');
    if (pauseBtn) {
        pauseBtn.addEventListener('click', function() {
            pauseAutomation();
        });
    }
    
    // Resume button
    const resumeBtn = document.getElementById('resumeBtn');
    if (resumeBtn) {
        resumeBtn.addEventListener('click', function() {
            resumeAutomation();
        });
    }
}

function executeAutomationNow() {
    const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
    modal.show();
    
    const button = document.getElementById('executeNowBtn');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Executando...';
    button.disabled = true;
    
    fetch('/api/execute-now', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        modal.hide();
        button.innerHTML = originalText;
        button.disabled = false;
        
        if (data.error) {
            showAlert('Erro ao executar automação: ' + data.error, 'danger');
        } else {
            showAlert('Automação executada com sucesso!', 'success');
            // Refresh data after execution
            setTimeout(refreshDashboardData, 2000);
        }
    })
    .catch(error => {
        modal.hide();
        button.innerHTML = originalText;
        button.disabled = false;
        showAlert('Erro na comunicação: ' + error.message, 'danger');
    });
}

function pauseAutomation() {
    fetch('/api/pause-automation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('Erro ao pausar automação: ' + data.error, 'danger');
        } else {
            showAlert('Automação pausada com sucesso!', 'warning');
            refreshDashboardData();
        }
    })
    .catch(error => {
        showAlert('Erro na comunicação: ' + error.message, 'danger');
    });
}

function resumeAutomation() {
    fetch('/api/resume-automation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('Erro ao retomar automação: ' + data.error, 'danger');
        } else {
            showAlert('Automação retomada com sucesso!', 'success');
            refreshDashboardData();
        }
    })
    .catch(error => {
        showAlert('Erro na comunicação: ' + error.message, 'danger');
    });
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Find container to insert alert
    const container = document.querySelector('main.container-fluid');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    } else {
        // Fallback to browser alert
        alert(message);
    }
}

// Utility functions
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR', {
        timeZone: 'America/Sao_Paulo',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatStatus(status) {
    const statusMap = {
        'pending': { class: 'secondary', text: 'Pendente' },
        'processing': { class: 'warning', text: 'Processando' },
        'processed': { class: 'info', text: 'Processado' },
        'published': { class: 'success', text: 'Publicado' },
        'failed': { class: 'danger', text: 'Falhou' }
    };
    
    const statusInfo = statusMap[status] || { class: 'secondary', text: status };
    return `<span class="badge bg-${statusInfo.class}">${statusInfo.text}</span>`;
}

// Export functions for use in other scripts
window.dashboardUtils = {
    refreshDashboardData,
    executeAutomationNow,
    pauseAutomation,
    resumeAutomation,
    showAlert,
    formatDateTime,
    formatStatus
};
