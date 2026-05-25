document.querySelectorAll("[data-preview]").forEach((button) => {
    button.addEventListener("click", async () => {
        const response = await fetch(`/api/note/${button.dataset.preview}/preview`);
        const note = await response.json();

        document.querySelector("#previewTitle").textContent = note.title;
        document.querySelector("#previewContent").textContent = note.content;
        document.querySelector("#previewDialog").showModal();
    });
});
