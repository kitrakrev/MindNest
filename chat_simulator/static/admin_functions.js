// Admin control functions for Chat Simulator
// Append to app.js or include separately

// Show system statistics
async function showSystemStats() {
    try {
        const response = await fetch(`${API_BASE}/api/admin/stats`);
        if (response.ok) {
            const stats = await response.json();
            
            const message = `
<div style="text-align: left; padding: 20px;">
    <h3 style="margin-bottom: 15px;">📊 System Statistics</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 10px; font-weight: bold;">👥 Personas</td>
            <td style="padding: 10px; text-align: right;">${stats.personas}</td>
        </tr>
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 10px; font-weight: bold;">🗂️ Groups</td>
            <td style="padding: 10px; text-align: right;">${stats.groups}</td>
        </tr>
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 10px; font-weight: bold;">🎮 Simulations</td>
            <td style="padding: 10px; text-align: right;">${stats.simulations}</td>
        </tr>
        <tr>
            <td style="padding: 10px; font-weight: bold;">💬 Messages</td>
            <td style="padding: 10px; text-align: right;">${stats.messages}</td>
        </tr>
    </table>
    <p style="margin-top: 15px; font-size: 12px; color: #666;">
        All data is now persistent and stored in database.
    </p>
</div>
            `;
            
            showNotification('System statistics loaded', 'success');
            
            // Show in a modal or alert
            const modal = confirm(`Stats:\nPersonas: ${stats.personas}\nGroups: ${stats.groups}\nSimulations: ${stats.simulations}\nMessages: ${stats.messages}\n\n✓ All data is persistent`);
            
        } else {
            throw new Error('Failed to load stats');
        }
    } catch (error) {
        console.error('Failed to load system stats:', error);
        showNotification('Failed to load system stats', 'error');
    }
}

// Confirm and clear only messages/simulations
async function confirmClearMessages() {
    const confirmed = confirm(
        '🗑️ Clear All Chats?\n\n' +
        'This will delete:\n' +
        '• All messages\n' +
        '• All simulations\n\n' +
        '✓ Personas and groups will be kept\n\n' +
        'Continue?'
    );
    
    if (!confirmed) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/clear-messages`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(
                `Cleared ${result.deleted.messages} messages and ${result.deleted.simulations} simulations`,
                'success'
            );
            
            // Refresh the UI
            clearChat();
            currentSimulation = null;
            updateButtons(false);
            
        } else {
            throw new Error('Failed to clear messages');
        }
    } catch (error) {
        console.error('Failed to clear messages:', error);
        showNotification('Failed to clear messages', 'error');
    }
}

// Confirm and clear ALL data
async function confirmClearAll() {
    const confirmed = confirm(
        '⚠️ RESET ALL DATA?\n\n' +
        'This will DELETE EVERYTHING:\n' +
        '• All personas\n' +
        '• All groups\n' +
        '• All simulations\n' +
        '• All messages\n' +
        '• All memories\n\n' +
        '❌ THIS CANNOT BE UNDONE!\n\n' +
        'Type "RESET" to confirm'
    );
    
    if (!confirmed) return;
    
    const confirmText = prompt('Type RESET to confirm:');
    if (confirmText !== 'RESET') {
        showNotification('Reset cancelled', 'info');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/clear-all`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(
                `All data cleared: ${result.deleted.personas} personas, ${result.deleted.messages} messages`,
                'success'
            );
            
            // Refresh everything
            personas = [];
            selectedPersonas = [];
            currentSimulation = null;
            renderPersonasList();
            clearChat();
            updateButtons(false);
            
            // Reload the page to reset state
            setTimeout(() => {
                window.location.reload();
            }, 2000);
            
        } else {
            throw new Error('Failed to clear all data');
        }
    } catch (error) {
        console.error('Failed to clear all data:', error);
        showNotification('Failed to clear all data', 'error');
    }
}

// Export session data
async function exportSession() {
    try {
        const stats = await fetch(`${API_BASE}/api/admin/stats`).then(r => r.json());
        const personasData = await fetch(`${API_BASE}/api/personas/`).then(r => r.json());
        
        const exportData = {
            exported_at: new Date().toISOString(),
            stats: stats,
            personas: personasData,
            version: '1.0'
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-simulator-export-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        showNotification('Session exported successfully', 'success');
    } catch (error) {
        console.error('Failed to export session:', error);
        showNotification('Failed to export session', 'error');
    }
}

console.log('✅ Admin controls loaded');

