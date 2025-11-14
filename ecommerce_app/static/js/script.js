window.onload = function() {
    const messages = document.querySelectorAll(".message");
    messages.forEach(msg => {
        setTimeout(() => msg.style.display = "none", 3000);
    });
};
