const agents = {
  jenkins: { initials: "JL", title: "Jenkins Log Analyst", description: "定位构建失败原因，并结合 Workspace 源码给出修复建议", avatar: "avatar-jenkins", ready: true },
  release: { initials: "RN", title: "Release Notes", description: "汇总变更记录并生成清晰的发布说明", avatar: "avatar-release", ready: false },
  triage: { initials: "BT", title: "Bug Triage", description: "关联缺陷、日志与代码所有者", avatar: "avatar-triage", ready: false },
};

const sidebar = document.querySelector("#agentSidebar");
const activityPanel = document.querySelector("#activityPanel");
const conversation = document.querySelector("#conversation");
const input = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const toast = document.querySelector("#toast");
const activityList = document.querySelector("#activityList");
const activityStatus = document.querySelector("#activityStatus");
let selectedAgent = "jenkins";
let toastTimer;
let eventSource;
let isRunning = false;
let activitySequence = 0;
let assistantBody;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("is-visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 2400);
}

function setAgent(id) {
  const agent = agents[id];
  selectedAgent = id;
  document.querySelectorAll(".agent-item").forEach(item => item.classList.toggle("is-active", item.dataset.agent === id));
  const avatar = document.querySelector("#headerAvatar");
  avatar.className = `agent-avatar ${agent.avatar}`;
  avatar.textContent = agent.initials;
  document.querySelector("#agentTitle").textContent = agent.title;
  document.querySelector("#agentDescription").textContent = agent.description;
  document.querySelector("#agentStatus").textContent = agent.ready ? "Ready" : "Offline";
  sendButton.disabled = !agent.ready || isRunning;
  input.disabled = !agent.ready || isRunning;
  input.placeholder = agent.ready ? "输入 Jenkins 链接或描述问题…" : "此 Agent 尚未配置";
  sidebar.classList.remove("is-open");
  showToast(`已切换到 ${agent.title}`);
}

document.querySelectorAll(".agent-item").forEach(item => item.addEventListener("click", () => setAgent(item.dataset.agent)));
document.querySelector("#openSidebar").addEventListener("click", () => sidebar.classList.add("is-open"));
document.querySelector("#closeSidebar").addEventListener("click", () => sidebar.classList.remove("is-open"));
document.querySelector("#activityToggle").addEventListener("click", () => activityPanel.classList.toggle("is-hidden"));
document.querySelector("#closeActivity").addEventListener("click", () => activityPanel.classList.add("is-hidden"));
document.querySelector("#stripClose").addEventListener("click", () => document.querySelector("#runStrip").classList.add("is-hidden"));
document.querySelector("#settingsButton").addEventListener("click", () => showToast("设置将在接入后端时开放"));
document.querySelector("#clearButton").addEventListener("click", () => {
  if (isRunning) {
    showToast("Agent 正在运行，完成后再开始新会话");
    return;
  }
  conversation.innerHTML = `<div class="empty-state" id="emptyState"><span class="empty-mark">JL</span><h2>从一次构建开始</h2><p>粘贴 Jenkins Job 或 Build 链接。Agent 会获取日志、定位相关源码并给出可验证的根因分析。</p></div>`;
  activityList.innerHTML = `<p class="activity-empty">任务开始后将在这里显示实时轨迹。</p>`;
  activityStatus.textContent = "Ready";
  document.querySelector("#runStrip").classList.add("is-hidden");
  showToast("已开始新会话");
  input.focus();
});

document.querySelectorAll(".copy-answer").forEach(button => button.addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(button.closest(".message-body").innerText); showToast("分析结果已复制"); }
  catch { showToast("浏览器未授权剪贴板访问"); }
}));

function appendMessage(role, content) {
  document.querySelector("#emptyState")?.remove();
  const article = document.createElement("article");
  article.className = `message ${role === "user" ? "user-message" : "assistant-message"}`;
  const now = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  article.innerHTML = role === "user"
    ? `<div class="message-label"><strong>You</strong><time>${now}</time></div><div class="message-body"></div>`
    : `<div class="message-label"><span class="mini-avatar">${agents[selectedAgent].initials}</span><strong>${agents[selectedAgent].title}</strong><time>${now}</time></div><div class="message-body result-message"></div>`;
  article.querySelector(".message-body").textContent = content;
  conversation.appendChild(article);
  conversation.scrollTo({ top: conversation.scrollHeight, behavior: "smooth" });
  return article.querySelector(".message-body");
}

function addActivity(title, detail = "") {
  activityList.querySelector(".activity-empty")?.remove();
  activitySequence += 1;
  const event = document.createElement("div");
  event.className = "activity-event";
  event.innerHTML = `<span class="event-icon">${activitySequence}</span><div><strong></strong><p></p><time>live</time></div>`;
  event.querySelector("strong").textContent = title;
  event.querySelector("p").textContent = detail;
  activityList.appendChild(event);
  event.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function setRunning(running) {
  isRunning = running;
  const agent = agents[selectedAgent];
  sendButton.disabled = running || !agent.ready;
  input.disabled = running || !agent.ready;
  document.querySelector("#agentStatus").textContent = running ? "Running" : "Ready";
  activityStatus.textContent = running ? "Running" : "Ready";
}

function finishRun(status, message) {
  eventSource?.close();
  eventSource = undefined;
  setRunning(false);
  document.querySelector("#runTitle").textContent = status === "completed" ? "任务已完成" : "任务失败";
  document.querySelector("#runMeta").textContent = message;
  activityStatus.textContent = status === "completed" ? "Completed" : "Failed";
}

function handleAgentEvent(event) {
  switch (event.type) {
    case "progress":
      document.querySelector("#runMeta").textContent = event.message;
      addActivity("Agent 进度", event.message);
      break;
    case "skill_selected":
      addActivity("选择 Skill", `${event.skill} · ${event.task}`);
      break;
    case "command_started":
      addActivity("执行命令", event.skill);
      break;
    case "command_completed":
      addActivity(event.success ? "命令完成" : "命令失败", event.skill);
      break;
    case "copilot_activity":
      addActivity("Copilot 工具", event.message);
      break;
    case "answer_delta":
      if (!assistantBody) {
        assistantBody = appendMessage("assistant", "");
        assistantBody.classList.add("streaming-answer");
      }
      assistantBody.textContent += event.content || "";
      conversation.scrollTo({ top: conversation.scrollHeight, behavior: "smooth" });
      break;
    case "completed":
      if (!assistantBody) assistantBody = appendMessage("assistant", event.answer || "任务已完成。");
      else assistantBody.textContent = event.answer || assistantBody.textContent;
      addActivity("生成分析", "Completed");
      finishRun("completed", "Agent 已返回最终结果");
      assistantBody = undefined;
      break;
    case "error":
      appendMessage("assistant", event.message || "Agent 执行失败，请稍后重试。");
      addActivity("执行失败", event.message || "Unknown error");
      finishRun("error", "请检查服务端日志");
      assistantBody = undefined;
      break;
  }
}

async function submitMessage() {
  const content = input.value.trim();
  if (!content || sendButton.disabled) return;
  appendMessage("user", content);
  input.value = "";
  input.style.height = "auto";
  setRunning(true);
  assistantBody = undefined;
  activitySequence = 0;
  activityList.innerHTML = "";
  document.querySelector("#runStrip").classList.remove("is-hidden");
  document.querySelector("#runTitle").textContent = "正在分析请求";
  document.querySelector("#runMeta").textContent = "正在连接 Agent";

  try {
    const response = await fetch("/api/agents/jenkins-log-analyst/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Agent request failed");

    eventSource = new EventSource(`/api/runs/${payload.run_id}/events`);
    eventSource.onmessage = message => handleAgentEvent(JSON.parse(message.data));
    eventSource.onerror = () => {
      if (isRunning) {
        appendMessage("assistant", "与 Agent 的实时连接已中断，请稍后重试。");
        finishRun("error", "SSE connection closed");
      }
    };
  } catch (error) {
    appendMessage("assistant", error.message || "无法连接 Agent 服务。");
    finishRun("error", "请求未能提交");
  }
}

document.querySelector("#messageForm").addEventListener("submit", event => { event.preventDefault(); submitMessage(); });
input.addEventListener("keydown", event => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submitMessage(); } });
input.addEventListener("input", () => { input.style.height = "auto"; input.style.height = `${Math.min(input.scrollHeight, 130)}px`; });
