// In your JavaScript
async function convertFile() {
  const fileInput = document.getElementById("fileInput");
  const file = fileInput.files[0];

  if (!file) return;

  // Show loading state
  const convertBtn = document.getElementById("convertBtn");
  convertBtn.disabled = true;
  convertBtn.textContent = "Converting...";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (response.ok && result.success) {
      // Trigger download automatically
      const a = document.createElement("a");
      a.href = result.download_url;
      a.download = result.filename; // This ensures the save dialog appears
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } else {
      alert(result.error || "Conversion failed");
    }
  } catch (error) {
    alert("Error during conversion");
    console.error(error);
  } finally {
    convertBtn.disabled = false;
    convertBtn.textContent = "Convert to PDF";
    fileInput.value = "";
  }
}
