// document.addEventListener("DOMContentLoaded", function () {
//   const maxSizeMB = 100;
//   const maxSizeBytes = maxSizeMB * 1024 * 1024;

//   const form = document.getElementById("uploadForm");
//   const convertBtn = document.getElementById("convertBtn");
//   const progressContainer = document.getElementById("progressContainer");
//   const progressBar = document.getElementById("progressBar");
//   const statusMessage = document.getElementById("statusMessage");
//   const fileInput = document.getElementById("file");

//   // Clear previous messages on new file select
//   fileInput.addEventListener("change", function (e) {
//     statusMessage.textContent = "";
//     const file = e.target.files[0];
//     if (file && file.size > maxSizeBytes) {
//       alert(`File size exceeds ${maxSizeMB}MB limit`);
//       e.target.value = ""; // Clear file input
//     }
//   });

//   convertBtn.addEventListener("click", function () {
//     statusMessage.textContent = "";
//     const file = fileInput.files[0];

//     if (!file) {
//       alert("Please select a file first");
//       return;
//     }

//     if (file.size > maxSizeBytes) {
//       alert(`File size exceeds ${maxSizeMB}MB limit`);
//       return;
//     }

//     convertBtn.disabled = true;
//     progressContainer.style.display = "block";
//     progressBar.style.width = "0%";
//     progressBar.style.backgroundColor = "#4caf50"; // green bar
//     statusMessage.textContent = "Uploading file...";

//     const formData = new FormData();
//     formData.append("file", file);

//     const xhr = new XMLHttpRequest();
//     xhr.open("POST", "/upload", true);

//     xhr.upload.onprogress = function (e) {
//       if (e.lengthComputable) {
//         const percent = Math.round((e.loaded / e.total) * 100);
//         progressBar.style.width = percent + "%";
//         statusMessage.textContent = `Uploading: ${percent}%`;
//       }
//     };

//     xhr.onload = function () {
//       if (xhr.status === 200) {
//         const response = JSON.parse(xhr.responseText);
//         if (response.redirect) {
//           monitorConversion(response.download_id);
//         } else {
//           statusMessage.textContent = "Upload successful!";
//           convertBtn.disabled = false;
//         }
//       } else {
//         try {
//           // Try parsing JSON error response
//           const errData = JSON.parse(xhr.responseText);
//           handleError(
//             errData.error || `Upload failed with status ${xhr.status}`
//           );
//         } catch {
//           // If parsing fails, show a generic error
//           handleError(`Upload failed with status ${xhr.status}`);
//         }
//       }
//     };

//     xhr.onerror = function () {
//       handleError("Network error during upload");
//     };

//     xhr.send(formData);
//   });

//   function monitorConversion(downloadId) {
//     statusMessage.textContent = "Converting file...";
//     progressBar.style.width = "0%";
//     progressBar.style.backgroundColor = "#4caf50";

//     function checkStatus() {
//       fetch(`/status/${downloadId}`)
//         .then((response) => response.json())
//         .then((data) => {
//           if (data.complete) {
//             window.location.href = `/conversion_success/${downloadId}`;
//           } else if (data.error) {
//             handleError(data.error);
//           } else {
//             const currentWidth = parseInt(progressBar.style.width) || 0;
//             progressBar.style.width = Math.min(currentWidth + 5, 100) + "%";
//             setTimeout(checkStatus, 3000);
//           }
//         })
//         .catch((error) => {
//           handleError(error.message);
//         });
//     }

//     checkStatus();
//   }

//   function handleError(message) {
//     statusMessage.textContent = "Error: " + message;
//     progressBar.style.backgroundColor = "#dc3545"; // red bar
//     convertBtn.disabled = false;
//   }
// });
