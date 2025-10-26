// Group Management Functions

async function loadGroups() {
    try {
        const response = await fetch(`${API_BASE}/api/groups/`);
        groups = await response.json();
        renderGroups();
        updateGroupSelect();
    } catch (error) {
        console.error('Failed to load groups:', error);
    }
}

function renderGroups() {
    const container = document.getElementById('groupsList');
    
    if (groups.length === 0) {
        container.innerHTML = '<p class="empty-state">No groups yet. Create one to organize personas!</p>';
        return;
    }
    
    container.innerHTML = groups.map(group => `
        <div class="group-card ${selectedGroup === group.id ? 'selected' : ''}" 
             onclick="selectGroup('${group.id}')">
            <div class="group-name">
                <span>🗂️ ${group.name}</span>
                ${group.is_active ? '🟢' : '🔴'}
            </div>
            <div class="group-desc">${group.description || 'No description'}</div>
            <div class="group-members">
                👥 ${group.persona_ids.length} persona(s)
            </div>
            <div class="group-actions">
                <button class="btn btn-sm btn-info" onclick="viewGroupPersonas('${group.id}', event)">View</button>
                <button class="btn btn-sm btn-danger" onclick="deleteGroup('${group.id}', event)">Delete</button>
            </div>
        </div>
    `).join('');
}

function selectGroup(groupId) {
    selectedGroup = selectedGroup === groupId ? null : groupId;
    renderGroups();
    
    // Auto-select personas from group
    if (selectedGroup) {
        const group = groups.find(g => g.id === selectedGroup);
        if (group) {
            selectedPersonas = [...group.persona_ids];
            renderPersonas();
            updateStartButton();
        }
    }
}

function updateGroupSelect() {
    const select = document.getElementById('groupSelect');
    select.innerHTML = '<option value="">No Group</option>' + 
        groups.map(g => `<option value="${g.id}">${g.name}</option>`).join('');
}

async function createGroup(event) {
    event.preventDefault();
    
    const data = {
        name: document.getElementById('groupName').value,
        description: document.getElementById('groupDesc').value,
        persona_ids: selectedPersonas
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/groups/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showNotification('Group created successfully!', 'success');
            closeModal('createGroupModal');
            loadGroups();
            event.target.reset();
        } else {
            throw new Error('Failed to create group');
        }
    } catch (error) {
        showNotification('Failed to create group', 'error');
        console.error(error);
    }
}

async function deleteGroup(groupId, event) {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this group?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/groups/${groupId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Group deleted', 'success');
            if (selectedGroup === groupId) {
                selectedGroup = null;
            }
            loadGroups();
        }
    } catch (error) {
        showNotification('Failed to delete group', 'error');
        console.error(error);
    }
}

function viewGroupPersonas(groupId, event) {
    event.stopPropagation();
    const group = groups.find(g => g.id === groupId);
    if (group) {
        selectedPersonas = [...group.persona_ids];
        switchTab('personas');
        renderPersonas();
        updateStartButton();
        showNotification(`Selected ${group.persona_ids.length} persona(s) from ${group.name}`, 'info');
    }
}

