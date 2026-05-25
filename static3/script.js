async function refreshStats() {
    const response = await fetch("/api/stats");
    if (!response.ok) {
        return;
    }
    const stats = await response.json();
    document.querySelector("#stats").textContent = `Opravljenih ${stats.done} od ${stats.total} nalog.`;
}

document.querySelectorAll("[data-task]").forEach((checkbox) => {
    checkbox.addEventListener("change", async () => {
        const response = await fetch(`/api/task/${checkbox.dataset.task}/toggle`, {
            method: "POST",
        });
        const result = await response.json();
        checkbox.closest(".task").classList.toggle("done", result.done);
        refreshStats();
    });
});

refreshStats();
