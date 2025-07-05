document.getElementById("predictionForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const resultDiv = document.getElementById("result");
  resultDiv.textContent = "⏳ Predicting... Please wait.";

  const data = {
    gender: document.getElementById("gender").value,
    pregnancies: parseInt(document.getElementById("pregnancies").value),
    glucose: parseFloat(document.getElementById("glucose").value),
    blood_pressure: parseFloat(document.getElementById("blood_pressure").value),
    skin_thickness: parseFloat(document.getElementById("skin_thickness").value),
    insulin: parseFloat(document.getElementById("insulin").value),
    bmi: parseFloat(document.getElementById("bmi").value),
    diabetes_pedigree: parseFloat(document.getElementById("diabetes_pedigree").value),
    age: parseInt(document.getElementById("age").value)
  };

  try {
    const response = await fetch("http://127.0.0.1:8000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    // Simulate 3-second delay
    setTimeout(async () => {
      if (!response.ok) {
        // Server responded but status is not OK
        resultDiv.textContent = `❌ Server Error: ${response.status} ${response.statusText}`;
        return;
      }

      const res = await response.json();
      resultDiv.textContent = `✅ ${res.data.result}`;
    }, 3000);

  } catch (error) {
    // Network error: server down, wrong URL, or CORS issue
    setTimeout(() => {
      resultDiv.textContent = `❌ Error: Failed to fetch. Is the API running?`;
    }, 3000);
  }
});

const genderSelect = document.getElementById("gender");
const pregnanciesGroup = document.getElementById("pregnancies-group");
const pregnanciesInput = document.getElementById("pregnancies");

// Handle visibility on gender change
genderSelect.addEventListener("change", () => {
  if (genderSelect.value === "male") {
    pregnanciesGroup.style.display = "none";
    pregnanciesInput.value = 0;  // Force value to zero
  } else {
    pregnanciesGroup.style.display = "block";
  }
});

// Trigger once on page load in case the default is "male"
if (genderSelect.value === "male") {
  pregnanciesGroup.style.display = "none";
  pregnanciesInput.value = 0;
}
