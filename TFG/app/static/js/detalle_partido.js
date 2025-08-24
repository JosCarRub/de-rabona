document.addEventListener('DOMContentLoaded', function() {
    let currentMode = 'drag';
    const teamAssignments = { local: [], visitante: [], bench: [] };

    const modeButtons = document.querySelectorAll('.mode-btn');
    const assignmentModes = document.querySelectorAll('.assignment-mode');
    const infoCards = document.querySelectorAll('.assignment-info .info-card');
    const saveTeamsBtn = document.getElementById('saveTeamsBtn');
    const teamForm = document.getElementById('teamAssignmentForm');
    
    const teamSelects = document.querySelectorAll('.team-select');
    const dropdownCounters = {
        local: document.getElementById('localCountDropdown'),
        visitante: document.getElementById('visitanteCountDropdown'),
        bench: document.getElementById('benchCountDropdown')
    };
    const dropdownPreviews = {
        local: document.getElementById('localPlayersPreview'),
        visitante: document.getElementById('visitantePlayersPreview'),
        bench: document.getElementById('benchPlayersPreview')
    };

    const autoAssignBtn = document.getElementById('autoAssignBtn');
    const autoResult = document.getElementById('autoResult');

    function init() {
        setupModeToggle();
        setupDropdownMode();
        setupAutoMode();
        setupFormSubmission();
        
        initializeDragAndDrop({
            onDrop: () => {
                updateTeamAssignments();
                updateAllCounters();
                updateSaveButton();
            },
            getCurrentMode: () => currentMode
        });
        
        loadInitialTeamState();
    }

    function setupModeToggle() {
        modeButtons.forEach(button => {
            button.addEventListener('click', () => switchMode(button.dataset.mode));
        });
    }

    function switchMode(newMode) {
        if (newMode === currentMode) return;
        currentMode = newMode;

        modeButtons.forEach(btn => btn.classList.toggle('active', btn.dataset.mode === newMode));
        assignmentModes.forEach(mode => mode.classList.toggle('active', mode.dataset.assignment === newMode));
        infoCards.forEach(card => card.classList.toggle('active', card.dataset.info === newMode));

        if (newMode === 'dropdown') syncToDropdownMode();
        else if (newMode === 'drag') syncToDragMode();
        
        updateSaveButton();
    }

    function setupDropdownMode() {
        teamSelects.forEach(select => select.addEventListener('change', handleTeamSelectChange));
    }

    function handleTeamSelectChange() {
        updateTeamAssignmentsFromDropdown();
        updateAllCounters();
        updateSaveButton();
    }

    function setupAutoMode() {
        if (autoAssignBtn) autoAssignBtn.addEventListener('click', handleAutoAssignment);
    }

    function handleAutoAssignment() {
        const selectedMode = document.querySelector('input[name="autoMode"]:checked')?.value;
        if (!selectedMode) return;
        
        autoAssignBtn.classList.add('loading');
        autoAssignBtn.disabled = true;

        setTimeout(() => {
            const assignment = generateAutoAssignment(selectedMode);
            applyAutoAssignment(assignment);
            showAutoResult(assignment);
            
            autoAssignBtn.classList.remove('loading');
            autoAssignBtn.disabled = false;
            updateSaveButton();
        }, 500);
    }

    function generateAutoAssignment(mode) {
        const allPlayers = Array.from(document.querySelectorAll('[data-jugador-id]'));
        const playerData = allPlayers.map(p => ({
            id: p.dataset.jugadorId,
            element: p,
            name: p.querySelector('.player-name')?.textContent || '',
            avatar: p.querySelector('.player-avatar')?.src || ''
        }));
        
        const shuffled = [...playerData].sort(() => 0.5 - Math.random());
        const half = Math.ceil(shuffled.length / 2);
        const local = shuffled.slice(0, half);
        const visitante = shuffled.slice(half);

        return { local, visitante, bench: [] };
    }

    function applyAutoAssignment(assignment) {
        Object.entries(assignment).forEach(([team, players]) => {
            players.forEach(player => movePlayerToTeam(player.element, team));
        });
        syncToDropdownMode();
        updateTeamAssignments();
        updateAllCounters();
    }

    function showAutoResult(assignment) {
        if (!autoResult) return;
        const containers = {
            local: document.getElementById('autoLocalPlayers'),
            visitante: document.getElementById('autoVisitantePlayers'),
            bench: document.getElementById('autoBenchPlayers')
        };
        Object.values(containers).forEach(c => c.innerHTML = '');
        
        Object.entries(assignment).forEach(([team, players]) => {
            players.forEach(player => {
                const playerEl = document.createElement('div');
                playerEl.className = 'result-player';
                playerEl.innerHTML = `<img src="${player.avatar}" alt="${player.name}"><span>${player.name}</span>`;
                containers[team].appendChild(playerEl);
            });
        });
        autoResult.style.display = 'block';
    }

    function setupFormSubmission() {
        if (saveTeamsBtn) saveTeamsBtn.addEventListener('click', handleSaveTeams);
    }

    function handleSaveTeams() {
        if (saveTeamsBtn.disabled) return;
        updateTeamAssignments();
        
        document.getElementById('localPlayersInput').value = teamAssignments.local.join(',');
        document.getElementById('visitantePlayersInput').value = teamAssignments.visitante.join(',');
        
        if (teamForm) teamForm.submit();
    }

    function updateTeamAssignments() {
        teamAssignments.local = Array.from(document.querySelectorAll('#local-players [data-jugador-id]')).map(p => p.dataset.jugadorId);
        teamAssignments.visitante = Array.from(document.querySelectorAll('#visitante-players [data-jugador-id]')).map(p => p.dataset.jugadorId);
        teamAssignments.bench = Array.from(document.querySelectorAll('#bench-players [data-jugador-id]')).map(p => p.dataset.jugadorId);
    }
    
    function updateTeamAssignmentsFromDropdown() {
        teamSelects.forEach(select => {
            const playerId = select.dataset.jugadorId;
            const playerEl = document.querySelector(`[data-jugador-id="${playerId}"]`);
            if (playerEl) movePlayerToTeam(playerEl, select.value);
        });
        updateTeamAssignments();
    }

    function loadInitialTeamState() {
        updateTeamAssignments();
        syncToDropdownMode();
        updateAllCounters();
        updateSaveButton();
    }

    function syncToDropdownMode() {
        updateTeamAssignments();
        teamSelects.forEach(select => {
            const playerId = select.dataset.jugadorId;
            if (teamAssignments.local.includes(playerId)) select.value = 'local';
            else if (teamAssignments.visitante.includes(playerId)) select.value = 'visitante';
            else select.value = 'bench';
        });
        updateDropdownUI();
    }

    function syncToDragMode() {
        teamSelects.forEach(select => {
            const playerEl = document.querySelector(`[data-jugador-id="${select.dataset.jugadorId}"]`);
            if (playerEl) movePlayerToTeam(playerEl, select.value);
        });
        updateAllCounters();
    }

    function updateAllCounters() {
        updateDragCounters();
        updateDropdownUI();
    }

    function updateDragCounters() {
        document.querySelector('.local-counter').textContent = document.querySelectorAll('#local-players .field-player').length;
        document.querySelector('.visitante-counter').textContent = document.querySelectorAll('#visitante-players .field-player').length;
        document.querySelector('.bench-counter').textContent = document.querySelectorAll('#bench-players .bench-player').length;
    }

    function updateDropdownUI() {
        const counts = { local: 0, visitante: 0, bench: 0 };
        Object.values(dropdownPreviews).forEach(p => p.innerHTML = '');

        teamSelects.forEach(select => {
            counts[select.value]++;
            const playerRow = select.closest('.player-assignment-row');
            const playerName = playerRow.querySelector('.player-name').textContent;
            const playerAvatar = playerRow.querySelector('.player-avatar').src;
            const previewEl = document.createElement('div');
            previewEl.className = 'preview-player';
            previewEl.innerHTML = `<img src="${playerAvatar}" alt="${playerName}">`;
            dropdownPreviews[select.value].appendChild(previewEl);
        });

        Object.entries(counts).forEach(([team, count]) => dropdownCounters[team].textContent = count);
    }
    
    function updateSaveButton() {
        if (!saveTeamsBtn) return;
        updateTeamAssignments();
        const canSave = teamAssignments.local.length > 0 && teamAssignments.visitante.length > 0;
        saveTeamsBtn.disabled = !canSave;
    }

    function movePlayerToTeam(playerElement, targetTeam) {
        let targetContainer;
        if (targetTeam === 'local') {
            targetContainer = document.getElementById('local-players');
            playerElement.className = 'field-player local-player';
        } else if (targetTeam === 'visitante') {
            targetContainer = document.getElementById('visitante-players');
            playerElement.className = 'field-player visitante-player';
        } else {
            targetContainer = document.getElementById('bench-players');
            playerElement.className = 'bench-player';
        }
        targetContainer.appendChild(playerElement);
    }

    init();
});