(function () {
  const panel = document.createElement("aside");

  panel.style.cssText = `
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 1100;
    width: 290px;
    max-height: 85vh;
    overflow-y: auto;
    background: white;
    padding: 16px;
    border-radius: 12px;
    box-shadow: 0 2px 14px rgba(0,0,0,.2);
    font-family: Arial, sans-serif;
  `;

  panel.innerHTML = `
    <h3>Report an accessibility barrier</h3>

    <p style="font-size:13px">
      Help improve Manchester's accessibility data.
    </p>

    <label>Barrier type</label>

    <select id="barrierType">
      <option value="blocked_pavement">
        Blocked pavement
      </option>
      <option value="broken_lift">
        Broken lift
      </option>
      <option value="missing_dropped_kerb">
        Missing dropped kerb
      </option>
      <option value="construction">
        Construction obstruction
      </option>
      <option value="stairs">
        Stairs
      </option>
      <option value="rough_surface">
        Rough surface
      </option>
      <option value="other">
        Other
      </option>
    </select>

    <label>Description</label>

    <textarea
      id="barrierDescription"
      rows="3"
      maxlength="500"
      placeholder="Describe the accessibility problem..."
      style="width:100%;box-sizing:border-box"
    ></textarea>

    <button id="pickBarrier">
      Select location on map
    </button>

    <button id="submitBarrier">
      Submit report
    </button>

    <p id="barrierStatus"
       aria-live="polite"
       style="font-size:13px">
      Reports require verification before use in routing.
    </p>
  `;

  document.body.appendChild(panel);

  let pickingLocation = false;
  let selectedLocation = null;
  let reportMarker = null;

  const status = document.getElementById("barrierStatus");

  document.getElementById("pickBarrier")
    .addEventListener("click", () => {
      pickingLocation = true;
      status.textContent =
        "Click the barrier location on the map.";
    });

  map.on("click", event => {
    if (!pickingLocation) return;

    pickingLocation = false;
    selectedLocation = event.latlng;

    if (reportMarker) {
      map.removeLayer(reportMarker);
    }

    reportMarker = L.marker(
      selectedLocation
    ).addTo(map);

    reportMarker.bindPopup(
      "Reported barrier location"
    ).openPopup();

    status.textContent =
      "Location selected. You can now submit.";
  });

  document.getElementById("submitBarrier")
    .addEventListener("click", async () => {
      if (!selectedLocation) {
        status.textContent =
          "Please select a location first.";
        return;
      }

      const payload = {
        latitude: selectedLocation.lat,
        longitude: selectedLocation.lng,
        report_type: document.getElementById(
          "barrierType"
        ).value,
        description: document.getElementById(
          "barrierDescription"
        ).value.trim()
      };

      if (payload.description.length < 10) {
        status.textContent =
          "Please provide at least 10 characters.";
        return;
      }

      status.textContent = "Submitting report...";

      try {
        const response = await fetch(
          "/barriers/reports",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
          }
        );

        const result = await response.json();

        if (!response.ok) {
          status.textContent =
            "Unable to save report. Please try again.";
          return;
        }

        status.textContent =
          `Report #${result.id} saved. ` +
          `Status: pending verification.`;

        document.getElementById(
          "barrierDescription"
        ).value = "";

      } catch (error) {
        status.textContent =
          "Unable to connect to the reporting service.";
      }
    });
})();
