document.addEventListener("DOMContentLoaded", function () {
    
    const navbar = document.querySelector(".main-navbar");
    if (navbar) {
        window.addEventListener("scroll", function () {
            if (window.scrollY > 80) {
                navbar.classList.add("scrolled");
            } else {
                navbar.classList.remove("scrolled");
            }
        });
    }

    const menuToggle = document.querySelector(".menu-toggle");
    const navLinks = document.querySelector(".nav-links");
    if (menuToggle && navLinks) {
        menuToggle.addEventListener("click", () => {
            navLinks.classList.toggle("active");
        });
    }

    const toasts = document.querySelectorAll(".toast");
    if (toasts.length) {
        toasts.forEach((toast) => {
            const SHOW_TIME = 4500;
            setTimeout(() => {
                toast.style.transition = "opacity 0.4s ease, transform 0.4s ease";
                toast.style.opacity = "0";
                toast.style.transform = "translateY(-10px)";

                setTimeout(() => {
                    toast.remove();
                }, 400);
            }, SHOW_TIME);
        });
    }

    const alertBox = document.getElementById('auto-dismiss-alert');
    if (alertBox) {
        setTimeout(function () {
            alertBox.style.opacity = '0';
            alertBox.style.transform = 'translateY(-10px)';
            setTimeout(function () {
                alertBox.style.display = 'none';
            }, 600);
        }, 4000);
    }

});