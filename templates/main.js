const actionSelect = document.getElementById("action");
const resultSelect = document.getElementById("result");
const nasOptions = document.getElementById("nas_options");
const passwordOption = document.getElementById("password_option");
const manualPasswordInput = document.getElementById("manual_password_input");
const autoPasswordGenerate = document.getElementById("auto_password_generate");
const togglePasswordIcon = document.getElementById("toggle_password");
const passwordInput = document.getElementById("password");
const toggleNasPassword = document.getElementById("toggle_nas_password");
const nasPasswordInput = document.getElementById("nas_password");

// Generate Password
function generatePassword() {
    const length = 16;
    const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()";
    let password = "";
    for (let i = 0; i < length; i++) {
        password += charset.charAt(Math.floor(Math.random() * charset.length));
    }
    document.getElementById("generated_password").textContent = `Password: ${password}`;
    document.getElementById("password").value = password; // Set the value in the hidden input
}

// Toggle Password Input Options
passwordOption.addEventListener("change", function () {
    const selectedOption = passwordOption.value;
    manualPasswordInput.classList.toggle("hidden", selectedOption === "auto");
    autoPasswordGenerate.classList.toggle("hidden", selectedOption === "manual");
});

// Event Listener untuk Klik pada Ikon Gembok
togglePasswordIcon.addEventListener("click", function () {
    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        togglePasswordIcon.textContent = "🔓";
    } else {
        passwordInput.type = "password";
        togglePasswordIcon.textContent = "🔒";
    }
});

toggleNasPassword.addEventListener("click", function () {
    const type = nasPasswordInput.getAttribute("type") === "password" ? "text" : "password";
    nasPasswordInput.setAttribute("type", type);
    toggleNasPassword.textContent = type === "password" ? "🔒" : "🔓"; // Update icon
});

// Update Result Options Based on Action
actionSelect.addEventListener("change", function () {
    const action = actionSelect.value;
    resultSelect.innerHTML = "";

    if (action === "encrypt") {
        const downloadOption = document.createElement("option");
        downloadOption.value = "download";
        downloadOption.textContent = "Download";
        resultSelect.appendChild(downloadOption);

        const uploadOption = document.createElement("option");
        uploadOption.value = "upload";
        uploadOption.textContent = "Upload to NAS";
        resultSelect.appendChild(uploadOption);
    } else if (action === "decrypt") {
        const downloadOption = document.createElement("option");
        downloadOption.value = "download";
        downloadOption.textContent = "Download";
        resultSelect.appendChild(downloadOption);

        nasOptions.classList.add("hidden");
    }

    // Trigger result change to update NAS visibility
    resultSelect.dispatchEvent(new Event("change"));
});

// Show NAS Options if "Upload to NAS" is Selected
resultSelect.addEventListener("change", function () {
    const result = resultSelect.value;
    nasOptions.classList.toggle("hidden", result !== "upload");
});

// Trigger initial action change to set the default state
actionSelect.dispatchEvent(new Event("change"));
