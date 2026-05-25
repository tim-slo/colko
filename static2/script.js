document.querySelectorAll("[data-like]").forEach((button) => {
    button.addEventListener("click", async () => {
        const response = await fetch(`/api/post/${button.dataset.like}/like`, {
            method: "POST",
        });

        if (response.status === 401) {
            alert("Za všečkanje se moraš prijaviti.");
            return;
        }

        const result = await response.json();
        button.querySelector("span").textContent = result.likes;
        button.classList.toggle("liked", result.liked);
    });
});
