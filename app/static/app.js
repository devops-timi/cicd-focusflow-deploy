function toggleTask(taskId, checkbox) {
    fetch(`/toggle/${taskId}`, { method: "POST" });

    const text = checkbox.nextElementSibling;
    text.classList.toggle("done");
    checkbox.parentElement.dataset.completed = checkbox.checked;
}

function filterTasks(type) {
    const items = document.querySelectorAll("#task-list li");

    items.forEach(item => {
        const completed = item.dataset.completed === "True" || item.dataset.completed === "true";

        if (type === "all") item.style.display = "list-item";
        if (type === "active") item.style.display = completed ? "none" : "list-item";
        if (type === "completed") item.style.display = completed ? "list-item" : "none";
    });
}
