window.addEventListener("DOMContentLoaded", function () {
    const popup = document.getElementById("disclaimerPopup");
    if (popup && !window.sessionStorage.getItem("mountZionPopupClosed")) {
        popup.style.display = "block";
        document.body.classList.add("blur-background");
    }
});

function closeDisclaimer() {
    const popup = document.getElementById("disclaimerPopup");
    if (popup) {
        popup.style.display = "none";
        document.body.classList.remove("blur-background");
        window.sessionStorage.setItem("mountZionPopupClosed", "1");
    }
}

function setupAutoDismissMessages() {
    document.querySelectorAll(".site-messages .alert").forEach(function (message) {
        window.setTimeout(function () {
            message.classList.add("is-dismissing");
            window.setTimeout(function () {
                message.remove();
                const container = document.querySelector(".site-messages");
                if (container && !container.querySelector(".alert")) {
                    container.remove();
                }
            }, 300);
        }, 5000);
    });
}

function setupPasswordFeedback() {
    const passwordInput = document.querySelector(
        'input[name="password1"], input[name="new_password1"]'
    );
    if (!passwordInput) {
        return;
    }

    const fieldGroup = passwordInput.closest(".mb-3");
    const requirements = fieldGroup
        ? fieldGroup.querySelector(".form-text ul, ul.helptext")
        : null;
    if (!requirements) {
        return;
    }

    requirements.classList.add("password-requirements");
    const requirementItems = Array.from(requirements.querySelectorAll("li"));
    const confirmationInput = document.querySelector(
        'input[name="password2"], input[name="new_password2"]'
    );
    const confirmationHelp = confirmationInput
        ? confirmationInput.closest(".mb-3")?.querySelector(".form-text")
        : null;
    if (confirmationHelp) {
        confirmationHelp.classList.add("password-confirmation-feedback");
    }

    const commonPasswords = new Set([
        "password",
        "password1",
        "password123",
        "12345678",
        "123456789",
        "qwerty",
        "qwerty123",
        "letmein",
        "welcome",
        "admin",
        "administrator",
        "mountzion",
    ]);

    function normalize(value) {
        return (value || "").toLowerCase().replace(/[^a-z0-9]/g, "");
    }

    function isDifferentFromPersonalInfo(password) {
        const normalizedPassword = normalize(password);
        if (!normalizedPassword) {
            return false;
        }
        const personalValues = ["username", "first_name", "last_name", "email"]
            .map((name) => document.querySelector(`[name="${name}"]`)?.value)
            .map(normalize)
            .filter((value) => value.length >= 3);
        return personalValues.every(
            (value) =>
                !normalizedPassword.includes(value) &&
                !value.includes(normalizedPassword)
        );
    }

    function setRequirementState(item, met, hasValue) {
        item.classList.toggle("requirement-met", hasValue && met);
        item.classList.toggle("requirement-unmet", hasValue && !met);
    }

    function updateFeedback() {
        const password = passwordInput.value;
        const hasValue = password.length > 0;
        const rules = [
            isDifferentFromPersonalInfo(password),
            password.length >= 8,
            password.length >= 8 && !commonPasswords.has(password.toLowerCase()),
            hasValue && !/^\d+$/.test(password),
        ];

        requirementItems.forEach((item, index) => {
            setRequirementState(item, Boolean(rules[index]), hasValue);
        });

        if (confirmationInput && confirmationHelp) {
            const matches =
                confirmationInput.value.length > 0 &&
                confirmationInput.value === password;
            confirmationHelp.classList.toggle("is-matching", matches);
        }
    }

    passwordInput.addEventListener("input", updateFeedback);
    confirmationInput?.addEventListener("input", updateFeedback);
    ["username", "first_name", "last_name", "email"].forEach((name) => {
        document.querySelector(`[name="${name}"]`)?.addEventListener("input", updateFeedback);
    });
    updateFeedback();
}

window.addEventListener("DOMContentLoaded", function () {
    setupAutoDismissMessages();
    setupPasswordFeedback();
});
