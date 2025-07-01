document.addEventListener('DOMContentLoaded', function() {
    const baseURL = "http://127.0.0.1:5001";  // ✅ Centralized backend URL (change here if your port or host changes)

    // === 1. Card Click Redirection (Navigation Between Pages) ===
    document.querySelectorAll(".card").forEach(card => {
        card.addEventListener("click", function() {
            const targetTab = this.getAttribute("data-tab");

            switch(targetTab) {
                case "identify":
                    window.location.href = "/medicine-identification";
                    break;
                case "prescriptions":
                    window.location.href = "/prescription-analyzer";
                    break;
                case "tracker":
                    window.location.href = "/medicine-tracker";
                    break;
                default:
                    console.warn("Unknown target tab:", targetTab);
            }
        });
    });

    // === 2. Image Upload for Medicine Identification ===
    const uploadForm = document.getElementById("uploadForm");
    if (uploadForm) {
        uploadForm.addEventListener("submit", function(event) {
            event.preventDefault();

            const fileInput = document.getElementById("fileInput").files[0];
            if (!fileInput) {
                alert("Please select an image first.");
                return;
            }

            const formData = new FormData();
            formData.append("file", fileInput);

            fetch(`${baseURL}/extract_medicine`, { method: "POST", body: formData })
            .then(response => response.json())
            .then(data => {
                alert(`Medicine: ${data.Medicine}\nDosage: ${data.Dosage}\nUses: ${data.Uses}\nSide Effects: ${data['Side Effects']}`);
            })
            .catch(error => {
                console.error("Error uploading:", error);
                alert("Failed to process the image. Try again.");
            });
        });
    }

    // === 3. Medicine Reminder Setup ===
    const reminderForm = document.getElementById("reminderForm");
    if (reminderForm) {
        reminderForm.addEventListener("submit", function(event) {
            event.preventDefault();

            const name = document.getElementById("reminder").value.trim();
            const date = document.getElementById("date").value;
            const time = document.getElementById("time").value;

            if (!name || !date || !time) {
                alert("Please fill all fields.");
                return;
            }

            const reminderItem = document.createElement("li");
            reminderItem.textContent = `⏰ Reminder for ${name} at ${date} ${time}`;
            document.getElementById("reminderList").appendChild(reminderItem);

            // Clear form after adding
            reminderForm.reset();
        });
    }

    // === 4. Trigger Prescription Analyzer (Dummy for Now) ===
    const prescriptionBtn = document.getElementById("runAppBtn");
    if (prescriptionBtn) {
        prescriptionBtn.addEventListener("click", function() {
            fetch(`${baseURL}/run_app2`, { method: "POST" })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
            })
            .catch(error => {
                console.error("Error starting app:", error);
                alert("Failed to start prescription analyzer.");
            });
        });
    }
});
