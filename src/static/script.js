var download_button = document.getElementById("download-button");
var download_spinner = document.getElementById("download-spinner");
var clear_button = document.getElementById("clear-button");
var search_box = document.getElementById("search-box");
var config_modal = document.getElementById("config-modal");
var save_message = document.getElementById("save-message");
var save_changes_button = document.getElementById("save-changes-button");
var spotify_client_id = document.getElementById("spotify_client_id");
var spotify_client_secret = document.getElementById("spotify_client_secret");
var sleep_interval = document.getElementById("sleep_interval");
var progress_bar = document.getElementById("progress-status-bar");
var progress_table = document
  .getElementById("progress-table")
  .getElementsByTagName("tbody")[0];
var socket = io();

/**
 * Update the progress bar
 * @param {number} percentage - The percentage of the progress bar
 * @param {string} status - The status of the progress bar
 */
function updateProgressBar(percentage, status) {
  const statusClasses = {
    Running: "bg-success progress-bar-animated",
    Stopped: "bg-danger",
    Idle: "bg-primary",
    Complete: "bg-dark",
  };

  progress_bar.style.width = `${percentage}%`;
  progress_bar.ariaValueNow = `${percentage}`;

  // Remove all possible status classes
  progress_bar.classList.remove(
    "bg-primary",
    "bg-success",
    "bg-danger",
    "bg-dark",
    "progress-bar-animated"
  );

  // Add new status class
  const newClasses = statusClasses[status]?.split(" ") || [];
  progress_bar.classList.add(...newClasses, "progress-bar-striped");
}

download_button.addEventListener("click", function () {
  socket.emit("download", { Link: search_box.value });
  download_spinner.style.display = "inline-block";
});

search_box.addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    socket.emit("download", { Link: search_box.value });
    download_spinner.style.display = "inline-block";
  }
});

socket.on("download", (response) => {
  if (response.Status == "Success") {
    search_box.value = "";
  } else {
    search_box.value = response.Data;
    setTimeout(function () {
      search_box.value = "";
    }, 3000);
  }
  download_spinner.style.display = "none";
});

clear_button.addEventListener("click", function () {
  socket.emit("clear");
});

config_modal.addEventListener("show.bs.modal", function (event) {
  socket.emit("loadSettings");

  function handleSettingsLoaded(settings) {
    spotify_client_id.value = settings.spotify_client_id;
    spotify_client_secret.value = settings.spotify_client_secret;
    sleep_interval.value = settings.sleep_interval;
    ignored_keywords.value = settings.ignored_keywords;
    socket.off("settingsLoaded", handleSettingsLoaded);
  }
  socket.on("settingsLoaded", handleSettingsLoaded);
});

save_changes_button.addEventListener("click", () => {
  socket.emit("updateSettings", {
    spotify_client_id: spotify_client_id.value,
    spotify_client_secret: spotify_client_secret.value,
    sleep_interval: sleep_interval.value,
    ignored_keywords: ignored_keywords.value,
  });
  save_message.style.display = "block";
  setTimeout(function () {
    save_message.style.display = "none";
  }, 1000);
});

socket.on("progress_status", (response) => {
  progress_table.innerHTML = "";
  response.data.forEach((item, index) => {
    const row = progress_table.insertRow();
    const cells = ["artist", "title", "status"].map((key) => {
      const cell = row.insertCell();
      if (key === "status" && item[key] === "Running") {
        cell.textContent = `${item[key]} (${item.percent_downloaded}%)`;
      } else {
        cell.textContent = item[key];
      }
      return cell;
    });

    const actionsCell = row.insertCell();
    actionsCell.innerHTML = `
      <button 
        class="btn btn-danger" 
        onclick="socket.emit('remove_track', ${index})"
        aria-label="Remove ${item.title}"
      >
        Remove
      </button>
    `;
  });

  updateProgressBar(response.percent_completion, response.status);
});

const themeSwitch = document.getElementById("themeSwitch");
const savedTheme = localStorage.getItem("theme");
const savedSwitchPosition = localStorage.getItem("switchPosition");

if (savedSwitchPosition) {
  themeSwitch.checked = savedSwitchPosition === "true";
}

if (savedTheme) {
  document.documentElement.setAttribute("data-bs-theme", savedTheme);
}

const initializeTheme = () => {
  const theme = localStorage.getItem("theme") || "light";
  const switchPosition = localStorage.getItem("switchPosition") === "true";

  themeSwitch.checked = switchPosition;
  document.documentElement.setAttribute("data-bs-theme", theme);
};

const toggleTheme = () => {
  const currentTheme = document.documentElement.getAttribute("data-bs-theme");
  const newTheme = currentTheme === "dark" ? "light" : "dark";

  document.documentElement.setAttribute("data-bs-theme", newTheme);
  localStorage.setItem("theme", newTheme);
  localStorage.setItem("switchPosition", themeSwitch.checked);
};

initializeTheme();
themeSwitch.addEventListener("click", toggleTheme);
