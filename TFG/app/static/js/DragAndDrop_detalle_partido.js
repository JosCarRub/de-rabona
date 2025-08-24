function initializeDragAndDrop(options) {
    let draggedElement = null;
    const dragPreview = document.getElementById('dragPreview');
    const touchFeedback = document.getElementById('touchFeedback');

    const draggablePlayers = document.querySelectorAll('.field-player, .bench-player');
    const dropZones = document.querySelectorAll('.team-zone, .bench-players');

    function setupDraggablePlayer(player) {
        player.addEventListener('dragstart', handleDragStart);
        player.addEventListener('dragend', handleDragEnd);
        player.addEventListener('touchstart', handleTouchStart, { passive: false });
        player.addEventListener('touchmove', handleTouchMove, { passive: false });
        player.addEventListener('touchend', handleTouchEnd);
        player.setAttribute('tabindex', '0');
    }

    function setupDropZone(zone) {
        zone.addEventListener('dragover', handleDragOver);
        zone.addEventListener('drop', handleDrop);
        zone.addEventListener('dragenter', handleDragEnter);
        zone.addEventListener('dragleave', handleDragLeave);
    }

    function handleDragStart(e) {
        draggedElement = this;
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', this.dataset.jugadorId);
        createDragPreview(this, e);
    }

    function handleDragEnd() {
        this.classList.remove('dragging');
        draggedElement = null;
        if (dragPreview) dragPreview.style.display = 'none';
        dropZones.forEach(zone => zone.classList.remove('drag-over'));
        if (options.onDrop) options.onDrop();
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    function handleDragEnter(e) {
        e.preventDefault();
        this.classList.add('drag-over');
    }

    function handleDragLeave(e) {
        if (!this.contains(e.relatedTarget)) {
            this.classList.remove('drag-over');
        }
    }

    function handleDrop(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
        if (!draggedElement) return;
        movePlayerToZone(draggedElement, this);
    }

    let touchStartPos = { x: 0, y: 0 };
    let isDraggingTouch = false;

    function handleTouchStart(e) {
        if (options.getCurrentMode() !== 'drag') return;
        const touch = e.touches[0];
        touchStartPos = { x: touch.clientX, y: touch.clientY };
        draggedElement = this;
        showTouchFeedback(touch.clientX, touch.clientY);
    }

    function handleTouchMove(e) {
        if (!draggedElement || options.getCurrentMode() !== 'drag') return;
        const touch = e.touches[0];
        const distance = Math.hypot(touch.clientX - touchStartPos.x, touch.clientY - touchStartPos.y);

        if (distance > 10 && !isDraggingTouch) {
            isDraggingTouch = true;
            draggedElement.classList.add('dragging');
            createDragPreview(draggedElement);
            document.body.style.overflow = 'hidden';
        }

        if (isDraggingTouch) {
            e.preventDefault();
            updateDragPreview(touch.clientX, touch.clientY);
            const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
            const dropZone = elementBelow?.closest('.team-zone, .bench-players');
            dropZones.forEach(zone => zone.classList.toggle('drag-over', zone === dropZone));
        }
    }

    function handleTouchEnd(e) {
        if (!isDraggingTouch || !draggedElement) {
            resetTouchState();
            return;
        }
        
        const touch = e.changedTouches[0];
        const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
        const dropZone = elementBelow?.closest('.team-zone, .bench-players');

        if (dropZone) {
            movePlayerToZone(draggedElement, dropZone);
        }
        resetTouchState();
    }

    function resetTouchState() {
        if (draggedElement) draggedElement.classList.remove('dragging');
        dropZones.forEach(zone => zone.classList.remove('drag-over'));
        if (dragPreview) dragPreview.style.display = 'none';
        if (touchFeedback) touchFeedback.classList.remove('active');
        document.body.style.overflow = '';
        draggedElement = null;
        isDraggingTouch = false;
    }

    function createDragPreview(element, event) {
        if (!dragPreview) return;
        const isBenchPlayer = element.classList.contains('bench-player');
        if (isBenchPlayer) {
            dragPreview.innerHTML = `<div class="bench-player">${element.innerHTML}</div>`;
        } else {
            dragPreview.innerHTML = `<div class="field-player ${element.className.replace('dragging', '')}">${element.innerHTML}</div>`;
        }
        dragPreview.style.display = 'block';
        if (event) {
            event.dataTransfer.setDragImage(dragPreview, 30, 30);
        }
    }

    function updateDragPreview(x, y) {
        if (!dragPreview) return;
        dragPreview.style.left = `${x - 30}px`;
        dragPreview.style.top = `${y - 30}px`;
    }

    function showTouchFeedback(x, y) {
        if (!touchFeedback) return;
        touchFeedback.style.left = `${x - 40}px`;
        touchFeedback.style.top = `${y - 40}px`;
        touchFeedback.classList.add('active');
        setTimeout(() => touchFeedback.classList.remove('active'), 200);
    }

    function movePlayerToZone(playerElement, targetZone) {
        const targetTeam = getTeamFromZone(targetZone);
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

    function getTeamFromZone(zone) {
        if (zone.dataset.team) return zone.dataset.team;
        if (zone.id === 'local-players' || zone.closest('.local-zone')) return 'local';
        if (zone.id === 'visitante-players' || zone.closest('.visitante-zone')) return 'visitante';
        return 'bench';
    }

    draggablePlayers.forEach(setupDraggablePlayer);
    dropZones.forEach(setupDropZone);
}