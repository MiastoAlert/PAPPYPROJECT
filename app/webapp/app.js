const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;

const state = {
  balance: 0,
  selectedAmount: null,
  selectedTitle: "",
};

const elements = {
  balance: document.getElementById("balance-value"),
  referrals: document.getElementById("referrals-value"),
  level: document.getElementById("level-value"),
  activity: document.getElementById("activity-value"),
  progressText: document.getElementById("progress-text"),
  progressFill: document.getElementById("progress-fill"),
  leaderboardList: document.getElementById("leaderboard-list"),
  modal: document.getElementById("modal"),
  modalReward: document.getElementById("modal-reward"),
  modalConfirm: document.getElementById("modal-confirm"),
  modalCancel: document.getElementById("modal-cancel"),
  modalError: document.getElementById("modal-error"),
  steamLink: document.getElementById("steam-link"),
};

const API_BASE = window.location.origin;

function getHeaders() {
  const headers = {
    "Content-Type": "application/json",
  };
  if (tg && tg.initData) {
    headers["X-Tg-Init-Data"] = tg.initData;
  }
  return headers;
}

async function fetchJSON(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...getHeaders(),
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Ошибка запроса.");
  }
  return response.json();
}

function animateBalance(target) {
  const start = state.balance;
  const duration = 600;
  const startTime = performance.now();

  function step(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const value = start + (target - start) * progress;
    elements.balance.textContent = value.toFixed(2);
    if (progress < 1) {
      requestAnimationFrame(step);
    } else {
      state.balance = target;
    }
  }

  requestAnimationFrame(step);
}

async function loadProfile() {
  try {
    const data = await fetchJSON("/api/me");
    animateBalance(data.balance);
    elements.referrals.textContent = data.total_referrals;
    elements.level.textContent = data.level.name;
    elements.activity.textContent = data.total_referral_messages;
    elements.progressText.textContent = `${data.level.progress_percent}%`;
    elements.progressFill.style.width = `${data.level.progress_percent}%`;
  } catch (error) {
    showAlert(error.message);
  }
}

async function loadLeaderboard() {
  try {
    const data = await fetchJSON("/api/leaderboard");
    elements.leaderboardList.innerHTML = "";
    data.items.forEach((item, index) => {
      const row = document.createElement("div");
      row.className = "leaderboard-item";
      row.innerHTML = `
        <div class="leaderboard-name">
          <strong>${index + 1}. ${item.name}</strong>
          <span>${item.level}</span>
        </div>
        <div class="leaderboard-score">${item.balance.toFixed(2)} Pappy</div>
      `;
      elements.leaderboardList.appendChild(row);
    });
  } catch (error) {
    showAlert(error.message);
  }
}

function showAlert(message) {
  if (tg && tg.showAlert) {
    tg.showAlert(message);
  } else {
    alert(message);
  }
}

function openModal(amount, title) {
  state.selectedAmount = amount;
  state.selectedTitle = title;
  elements.modalReward.textContent = `${amount} Pappy — ${title}`;
  elements.modalError.textContent = "";
  elements.steamLink.value = "";
  elements.modal.classList.remove("hidden");
}

function closeModal() {
  elements.modal.classList.add("hidden");
  elements.modalError.textContent = "";
}

async function handleExchange() {
  const steamLink = elements.steamLink.value.trim();
  if (!steamLink) {
    elements.modalError.textContent = "Введите SteamLink.";
    return;
  }

  try {
    await fetchJSON("/api/exchange", {
      method: "POST",
      body: JSON.stringify({
        amount: state.selectedAmount,
        steam_link: steamLink,
      }),
    });
    closeModal();
    showAlert("Обмен выполнен.");
    await loadProfile();
    await loadLeaderboard();
  } catch (error) {
    elements.modalError.textContent = error.message;
  }
}

function setupTabs() {
  const buttons = document.querySelectorAll(".tab-button");
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      buttons.forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");

      const target = button.dataset.tab;
      document.querySelectorAll(".tab-content").forEach((section) => {
        section.classList.toggle("active", section.id === target);
      });
    });
  });
}

function setupRewards() {
  document.querySelectorAll(".reward-card").forEach((card) => {
    const amount = Number(card.dataset.amount);
    const title = card.querySelector(".reward-name").textContent;
    const button = card.querySelector(".primary-button");
    button.addEventListener("click", () => openModal(amount, title));
    card.addEventListener("click", (event) => {
      if (event.target === button) {
        return;
      }
      openModal(amount, title);
    });
  });
}

elements.modalConfirm.addEventListener("click", handleExchange);
elements.modalCancel.addEventListener("click", closeModal);
elements.modal.addEventListener("click", (event) => {
  if (event.target === elements.modal) {
    closeModal();
  }
});

setupTabs();
setupRewards();
loadProfile();
loadLeaderboard();

if (tg) {
  tg.ready();
  tg.expand();
}
