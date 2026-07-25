document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('timelineSequence');
    if (!container) return;

    let draggedItem = null;

    // Helper: Converts time strings like "09:30 AM" or "02:15 PM" into total minutes from midnight
    function parseTimeToMinutes(timeStr) {
        if (!timeStr) return -1;
        const cleanedStr = timeStr.trim().toUpperCase();
        const parts = cleanedStr.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/);
        if (!parts) return -1;

        let hours = parseInt(parts[1], 10);
        const minutes = parseInt(parts[2], 10);
        const ampm = parts[3];

        if (ampm === 'PM' && hours < 12) hours += 12;
        if (ampm === 'AM' && hours === 12) hours = 0;

        return hours * 60 + minutes;
    }

    // Helper: Extracts minutes from a block element (returns -1 if it's a flexible task or has no time)
    function getBlockMinutes(block) {
        if (!block) return -1;
        const timeSpan = block.querySelector('.start-time');
        return timeSpan ? parseTimeToMinutes(timeSpan.textContent) : -1;
    }

    // Attach event listeners to all flexible task blocks
    const flexibleBlocks = container.querySelectorAll('.timeline-block.block-flexible');

    flexibleBlocks.forEach(block => {
        block.addEventListener('dragstart', (e) => {
            draggedItem = block;
            block.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', block.dataset.itemId);
        });

        block.addEventListener('dragend', () => {
            draggedItem = null;
            block.classList.remove('dragging');

            // Clean up drag-over indicators
            container.querySelectorAll('.timeline-block').forEach(b => {
                b.classList.remove('drag-over', 'drag-invalid');
            });

            // Trigger backend save request
            saveNewTaskOrder();
        });
    });

    // Helper to check whether placing 'draggedNode' before target element is valid
    function isValidMove(draggedNode, targetNode) {
        if (!draggedNode) return true;

        const draggedMinutes = getBlockMinutes(draggedNode);

        // If the dropped location is at the end of the container
        if (!targetNode) {
            const allBlocks = [...container.querySelectorAll('.timeline-block:not(.dragging)')];
            const lastBlock = allBlocks[allBlocks.length - 1];
            const lastMinutes = getBlockMinutes(lastBlock);

            // If dragged item has a time (is fixed) and is placed after a fixed item with a later time
            if (draggedMinutes !== -1 && lastMinutes !== -1 && draggedMinutes < lastMinutes) {
                return false;
            }
            return true;
        }

        const targetMinutes = getBlockMinutes(targetNode);

        // Rule A: Cannot place a LATER fixed task BEFORE an EARLIER fixed task
        if (draggedMinutes !== -1 && targetMinutes !== -1 && draggedMinutes > targetMinutes) {
            return false;
        }

        // Rule B: Cannot place an EARLIER fixed task AFTER a LATER fixed task
        const previousNode = targetNode.previousElementSibling;
        if (previousNode && previousNode !== draggedNode) {
            const prevMinutes = getBlockMinutes(previousNode);
            if (draggedMinutes !== -1 && prevMinutes !== -1 && draggedMinutes < prevMinutes) {
                return false;
            }
        }

        return true;
    }

    // Handle dragover within the sequence container
    container.addEventListener('dragover', (e) => {
        e.preventDefault();

        const afterElement = getDragAfterElement(container, e.clientY);

        container.querySelectorAll('.timeline-block').forEach(b => {
            b.classList.remove('drag-over', 'drag-invalid');
        });

        if (isValidMove(draggedItem, afterElement.element)) {
            e.dataTransfer.dropEffect = 'move';
            if (afterElement.element) {
                afterElement.element.classList.add('drag-over');
            }
        } else {
            e.dataTransfer.dropEffect = 'none';
            if (afterElement.element) {
                afterElement.element.classList.add('drag-invalid');
            }
        }
    });

    // Handle drop event
    container.addEventListener('drop', (e) => {
        e.preventDefault();
        container.querySelectorAll('.timeline-block').forEach(b => {
            b.classList.remove('drag-over', 'drag-invalid');
        });

        if (!draggedItem) return;

        const afterElement = getDragAfterElement(container, e.clientY);

        if (isValidMove(draggedItem, afterElement.element)) {
            if (afterElement.element == null) {
                container.appendChild(draggedItem);
            } else {
                container.insertBefore(draggedItem, afterElement.element);
            }
        } else {
            console.warn('Invalid move: Task placement violates schedule order.');
        }
    });

    // Helper function to calculate drag position relative to other blocks
    function getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.timeline-block:not(.dragging)')];

        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;

            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY });
    }

    // Send reordered sequence back to server
    function saveNewTaskOrder() {
        const updatedOrder = [...container.querySelectorAll('.timeline-block')].map((el, index) => ({
            id: el.dataset.itemId,
            type: el.dataset.itemType,
            position: index
        }));

        fetch('/reorder-timeline', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ order: updatedOrder })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Task order updated:', data);
        })
        .catch(error => {
            console.error('Error saving task order:', error);
        });
    }
});