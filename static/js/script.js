document.addEventListener("DOMContentLoaded", function () {

    // =========================
    // 1. Prevent empty notes
    // =========================
    const forms = document.querySelectorAll("form");

    forms.forEach(form => {
        form.addEventListener("submit", function (e) {
            const textarea = form.querySelector("textarea[name='note_text']");

            if (textarea && textarea.value.trim() === "") {
                e.preventDefault();
                alert("Note cannot be empty.");
            }
        });
    });

    // =========================
    // 2. Detect unsaved changes
    // =========================
    let formChanged = false;

    const inputs = document.querySelectorAll("input, textarea, select");

    inputs.forEach(input => {
        input.addEventListener("input", () => {
            formChanged = true;
        });

        input.addEventListener("change", () => {
            formChanged = true;
        });
    });

    window.addEventListener("beforeunload", function (e) {
        if (formChanged) {
            e.preventDefault();
            e.returnValue = '';
        }
    });

    forms.forEach(form => {
        form.addEventListener("submit", () => {
            formChanged = false;
        });
    });

    // =========================
    // 3. Auto-hide flash messages
    // =========================
    setTimeout(() => {
        document.querySelectorAll('.flash, .alert').forEach(el => {
            el.style.display = 'none';
        });
    }, 4000);

    // =========================
    // 4. Global Confirm Modal
    // =========================
    let activeForm = null;

    const modal = document.getElementById("confirmModal");
    const message = document.getElementById("modalMessage");
    const confirmYes = document.getElementById("confirmYes");
    const confirmNo = document.getElementById("confirmNo");

    if (modal && message && confirmYes && confirmNo) {

        document.addEventListener("click", function (e) {
            const trigger = e.target.closest("[data-confirm]");
            if (!trigger) return;

            e.preventDefault();

            const formId = trigger.getAttribute("data-form");
            const text = trigger.getAttribute("data-confirm");

            activeForm = document.getElementById(formId);

            if (!activeForm) {
                console.error("Form not found:", formId);
                return;
            }

            message.innerText = text;
            modal.classList.remove("hidden");
        });

        confirmNo.addEventListener("click", function () {
            modal.classList.add("hidden");
            activeForm = null;
        });

        confirmYes.addEventListener("click", function () {
            if (activeForm) {
                activeForm.submit();
            }
        });
    }


    // =========================
    // 5. Global Alert Modal
    // =========================

    const alertModal = document.getElementById("alertModal");
    const alertMessage = document.getElementById("alertMessage");
    const alertOk = document.getElementById("alertOk");

    function showAlert(messageText) {
        if (!alertModal) return;

        alertMessage.innerText = messageText;
        alertModal.classList.remove("hidden");
        }

    if (alertOk) {
        alertOk.addEventListener("click", function () {
            alertModal.classList.add("hidden");
        });
    }

    // =========================
    // 6. Bible Progress validation from database
    // =========================

    const book = document.getElementById("bookSelect");
    const chapter = document.getElementById("chapterInput");
    const verse = document.getElementById("verseInput");

    if (book && chapter && verse) {

        async function updateVerseLimit() {
            const selectedBook = book.value;
            const selectedChapter = chapter.value;

            if (!selectedBook || !selectedChapter) {
                verse.placeholder = "";
                verse.removeAttribute("max");
                return;
            }

            try {
                const response = await fetch(
                    `/bible/chapter-info?book=${encodeURIComponent(selectedBook)}&chapter=${selectedChapter}`
                );

                const data = await response.json();

                if (data.valid) {
                    verse.max = data.total_verses;
                    verse.placeholder = "1 - " + data.total_verses;
                } else {
                    verse.value = "";
                    verse.placeholder = data.message;
                    verse.removeAttribute("max");
                }

            } catch (error) {
                console.error("Bible chapter lookup error:", error);
            }
        }

        book.addEventListener("change", function () {
            chapter.value = "";
            verse.value = "";
            verse.placeholder = "";
            verse.removeAttribute("max");
        });

        chapter.addEventListener("input", updateVerseLimit);
        chapter.addEventListener("change", updateVerseLimit);
    }

    // =========================
    // 7. Show Flask flash messages in modal
    // =========================

    const flashData = document.getElementById("flashData");

    if (flashData) {
        const message = flashData.dataset.message;

        if (message) {
            showAlert(message);
        }
    }

    // =====================
    // 8. Mobile Hambuerger Menu
    // =====================

    const menuToggle = document.getElementById("menuToggle");
    const mainNav = document.getElementById("mainNav");

    if (menuToggle && mainNav) {

        menuToggle.addEventListener("click", () => {
            mainNav.classList.toggle("active");
        });

    }

})
