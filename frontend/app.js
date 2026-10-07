const API_BASE = "/api/v1/pricing";

const pricingTableBody = document.getElementById("pricingTableBody");
const uploadForm = document.getElementById("uploadForm");
const searchForm = document.getElementById("searchForm");
const uploadStatus = document.getElementById("uploadStatus");

async function fetchPricing(params = {}) {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) {
      query.append(key, value);
    }
  });

  const response = await fetch(`${API_BASE}?${query.toString()}`);
  if (!response.ok) {
    throw new Error("Unable to fetch pricing records");
  }

  return response.json();
}

function renderPricing(records) {
  pricingTableBody.innerHTML = "";

  if (!records.length) {
    pricingTableBody.innerHTML = `
      <tr>
        <td colspan="8">No pricing records found.</td>
      </tr>
    `;
    return;
  }

  records.forEach((record) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${record.id}</td>
      <td>${record.store_id}</td>
      <td>${record.sku}</td>
      <td>${record.product_name}</td>
      <td><span class="price-pill">$${Number(record.price).toFixed(2)}</span></td>
      <td>${record.price_date}</td>
      <td>${record.version}</td>
      <td>
        <div class="inline-edit">
          <input type="number" min="0" step="0.01" value="${Number(record.price).toFixed(2)}" data-price-input="${record.id}" />
          <button class="small-btn" data-price-update="${record.id}" data-version="${record.version}">Save</button>
        </div>
      </td>
    `;
    pricingTableBody.appendChild(row);
  });
}

async function loadPricing() {
  try {
    const records = await fetchPricing();
    renderPricing(records);
  } catch (error) {
    uploadStatus.textContent = error.message;
    uploadStatus.className = "status error";
  }
}

async function pollImportStatus(jobId) {
  const maxAttempts = 20;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const response = await fetch(`${API_BASE}/jobs/${jobId}`);

    if (!response.ok) {
      throw new Error("Unable to check import job status");
    }

    const job = await response.json();
    uploadStatus.textContent = `Import job ${jobId}: ${job.status}`;
    uploadStatus.className = job.status === "completed"
      ? "status success"
      : job.status === "failed"
        ? "status error"
        : "status";

    if (job.status === "completed") {
      await loadPricing();
      return;
    }

    if (job.status === "failed") {
      throw new Error(job.error_message || "CSV import failed");
    }

    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  throw new Error("Import job is still processing. Please refresh the page.");
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fileInput = document.getElementById("csvFile");
  const file = fileInput.files[0];

  if (!file) {
    uploadStatus.textContent = "Please choose a CSV file first.";
    uploadStatus.className = "status error";
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  uploadStatus.textContent = "Uploading...";
  uploadStatus.className = "status";

  try {
    const response = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
    });

    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.detail || "Upload failed");
    }

    const jobId = payload.job_id;
    fileInput.value = "";
    uploadStatus.textContent = `Upload queued for job ${jobId}. Processing...`;
    uploadStatus.className = "status";
    await pollImportStatus(jobId);
  } catch (error) {
    uploadStatus.textContent = error.message;
    uploadStatus.className = "status error";
  }
});

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const searchParams = {
    store_id: document.getElementById("storeId").value,
    sku: document.getElementById("sku").value,
    product_name: document.getElementById("productName").value,
    price_date: document.getElementById("priceDate").value,
  };

  try {
    const records = await fetchPricing(searchParams);
    renderPricing(records);
  } catch (error) {
    uploadStatus.textContent = error.message;
    uploadStatus.className = "status error";
  }
});

pricingTableBody.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-price-update]");
  if (!button) return;

  const id = Number(button.dataset.priceUpdate);
  const version = Number(button.dataset.version);
  const priceInput = document.querySelector(`[data-price-input="${id}"]`);
  const newPrice = priceInput.value;

  try {
    const response = await fetch(`${API_BASE}/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ price: newPrice, version }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Update failed");
    }

    uploadStatus.textContent = `Updated price for record ${id}.`;
    uploadStatus.className = "status success";
    await loadPricing();
  } catch (error) {
    uploadStatus.textContent = error.message;
    uploadStatus.className = "status error";
  }
});

loadPricing();
