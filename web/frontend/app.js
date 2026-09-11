const agents = {
  jenkins: { initials: "JL", title: "Jenkins Log Analyst", avatar: "avatar-jenkins", ready: true },
};

const translations = {
  zh: {
    pageTitle: "Agent Desk",
    brandSubtitle: "运维工作台",
    closeAgentList: "关闭 Agent 列表",
    close: "关闭",
    agentList: "Agent 列表",
    idle: "空闲",
    moreAgents: "更多 Agent",
    comingSoon: "即将推出",
    servicesOnline: "服务在线",
    settings: "设置",
    openAgentList: "打开 Agent 列表",
    agentDescription: "定位构建失败原因，并结合 Workspace 源码给出修复建议",
    newSession: "新会话",
    showActivity: "显示执行轨迹",
    activityTitle: "执行轨迹",
    preparingTask: "正在准备任务",
    waitingAgent: "等待 Agent 响应",
    agentStages: "Agent 执行阶段",
    collapseStatus: "收起状态栏",
    collapse: "收起",
    emptyTitle: "从一次构建开始",
    emptyDescription: "粘贴 Jenkins Job 或 Build 链接。Agent 会获取日志、定位相关源码并给出可验证的根因分析。",
    closeActivity: "关闭执行轨迹",
    activityEmpty: "任务开始后将在这里显示实时轨迹。",
    status: "状态",
    messagePlaceholder: "输入 Jenkins 链接或描述问题…",
    message: "消息",
    addAttachment: "添加附件",
    composerHint: "Enter 发送 · Shift + Enter 换行",
    send: "发送",
    disclaimer: "Agent 输出可能包含错误，请在执行修复前验证关键结论。",
    switchLanguage: "Switch to English",
    settingsUnavailable: "设置将在接入后端时开放",
    runningNewSession: "Agent 正在运行，完成后再开始新会话",
    newSessionStarted: "已开始新会话",
    ready: "Ready",
    running: "Running",
    completed: "Completed",
    failed: "Failed",
    analyzingRequest: "正在分析请求",
    connectingAgent: "正在连接 Agent",
    taskCompleted: "任务已完成",
    taskFailed: "任务失败",
    finalResult: "Agent 已返回最终结果",
    checkServerLog: "请检查服务端日志",
    requestNotSubmitted: "请求未能提交",
    progress: "Agent 进度",
    selectSkill: "选择 Skill",
    executeCommand: "执行命令",
    commandCompleted: "命令完成",
    commandFailed: "命令失败",
    copilotTool: "Copilot 工具",
    generateAnalysis: "生成分析",
    executionFailed: "执行失败",
    taskDoneFallback: "任务已完成。",
    agentFailed: "Agent 执行失败，请稍后重试。",
    connectionInterrupted: "与 Agent 的实时连接已中断，请稍后重试。",
    connectionClosed: "SSE 连接已关闭",
    requestFailed: "Agent 请求失败",
    cannotConnect: "无法连接 Agent 服务。",
    live: "实时",
  },
  en: {
    pageTitle: "Agent Desk",
    brandSubtitle: "Operations workspace",
    closeAgentList: "Close agent list",
    close: "Close",
    agentList: "Agent list",
    idle: "Idle",
    moreAgents: "More agents",
    comingSoon: "Coming soon",
    servicesOnline: "Services online",
    settings: "Settings",
    openAgentList: "Open agent list",
    agentDescription: "Find build failures and verify root causes against workspace source code",
    newSession: "New session",
    showActivity: "Show execution activity",
    activityTitle: "Execution activity",
    preparingTask: "Preparing task",
    waitingAgent: "Waiting for the agent",
    agentStages: "Agent execution stages",
    collapseStatus: "Collapse status bar",
    collapse: "Collapse",
    emptyTitle: "Start with a build",
    emptyDescription: "Paste a Jenkins job or build link. The agent will retrieve logs, inspect relevant source code, and provide a verifiable root-cause analysis.",
    closeActivity: "Close execution activity",
    activityEmpty: "Live execution activity will appear here after a task starts.",
    status: "Status",
    messagePlaceholder: "Enter a Jenkins link or describe the issue…",
    message: "Message",
    addAttachment: "Add attachment",
    composerHint: "Enter to send · Shift + Enter for a new line",
    send: "Send",
    disclaimer: "Agent output may be inaccurate. Verify critical conclusions before applying fixes.",
    switchLanguage: "切换到中文",
    settingsUnavailable: "Settings will be available after backend integration",
    runningNewSession: "The agent is running. Start a new session after it finishes.",
    newSessionStarted: "New session started",
    ready: "Ready",
    running: "Running",
    completed: "Completed",
    failed: "Failed",
    analyzingRequest: "Analyzing request",
    connectingAgent: "Connecting to the agent",
    taskCompleted: "Task completed",
    taskFailed: "Task failed",
    finalResult: "The agent returned the final result",
    checkServerLog: "Check the server log",
    requestNotSubmitted: "The request was not submitted",
    progress: "Agent progress",
    selectSkill: "Select skill",
    executeCommand: "Execute command",
    commandCompleted: "Command completed",
    commandFailed: "Command failed",
    copilotTool: "Copilot tool",
    generateAnalysis: "Generate analysis",
    executionFailed: "Execution failed",
    taskDoneFallback: "Task completed.",
    agentFailed: "Agent execution failed. Try again later.",
    connectionInterrupted: "The live agent connection was interrupted. Try again later.",
    connectionClosed: "SSE connection closed",
    requestFailed: "Agent request failed",
    cannotConnect: "Unable to connect to the agent service.",
    live: "live",
  },
};

const sidebar = document.querySelector("#agentSidebar");
const activityPanel = document.querySelector("#activityPanel");
const conversation = document.querySelector("#conversation");
const input = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const toast = document.querySelector("#toast");
const activityList = document.querySelector("#activityList");
const activityStatus = document.querySelector("#activityStatus");
const languageToggle = document.querySelector("#languageToggle");
let selectedAgent = "jenkins";
let currentLanguage = "zh";
let toastTimer;
let eventSource;
let isRunning = false;
let runState = "ready";
let activitySequence = 0;
let assistantBody;

function t(key) {
  return translations[currentLanguage][key] || key;
}

function emptyConversationMarkup() {
  return `<div class="empty-state" id="emptyState"><span class="empty-mark">JL</span><h2 data-i18n="emptyTitle">${t("emptyTitle")}</h2><p data-i18n="emptyDescription">${t("emptyDescription")}</p></div>`;
}

function emptyActivityMarkup() {
  return `<p class="activity-empty" data-i18n="activityEmpty">${t("activityEmpty")}</p>`;
}

function applyTranslations() {
  document.documentElement.lang = currentLanguage === "zh" ? "zh-CN" : "en";
  document.title = t("pageTitle");
  document.querySelectorAll("[data-i18n]").forEach(element => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(element => {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-aria]").forEach(element => {
    element.setAttribute("aria-label", t(element.dataset.i18nAria));
  });
  document.querySelectorAll("[data-i18n-title]").forEach(element => {
    element.title = t(element.dataset.i18nTitle);
  });
  languageToggle.querySelector(".language-current").textContent = currentLanguage === "zh" ? "中" : "EN";
  languageToggle.querySelector(".language-next").textContent = currentLanguage === "zh" ? "EN" : "中";
  languageToggle.setAttribute("aria-label", t("switchLanguage"));
  languageToggle.title = t("switchLanguage");
  document.querySelector("#agentDescription").textContent = t("agentDescription");
  activityStatus.textContent = t(runState);
  document.querySelector("#agentStatus").textContent = isRunning ? t("running") : t("ready");
}

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
  document.querySelector("#agentDescription").textContent = t("agentDescription");
  document.querySelector("#agentStatus").textContent = t("ready");
  sendButton.disabled = !agent.ready || isRunning;
  input.disabled = !agent.ready || isRunning;
  input.placeholder = t("messagePlaceholder");
  sidebar.classList.remove("is-open");
}

document.querySelectorAll(".agent-item").forEach(item => item.addEventListener("click", () => setAgent(item.dataset.agent)));
document.querySelector("#openSidebar").addEventListener("click", () => sidebar.classList.add("is-open"));
document.querySelector("#closeSidebar").addEventListener("click", () => sidebar.classList.remove("is-open"));
document.querySelector("#activityToggle").addEventListener("click", () => activityPanel.classList.toggle("is-hidden"));
document.querySelector("#closeActivity").addEventListener("click", () => activityPanel.classList.add("is-hidden"));
document.querySelector("#stripClose").addEventListener("click", () => document.querySelector("#runStrip").classList.add("is-hidden"));
document.querySelector("#settingsButton").addEventListener("click", () => showToast(t("settingsUnavailable")));
languageToggle.addEventListener("click", () => {
  currentLanguage = currentLanguage === "zh" ? "en" : "zh";
  applyTranslations();
});
document.querySelector("#clearButton").addEventListener("click", () => {
  if (isRunning) {
    showToast(t("runningNewSession"));
    return;
  }
  conversation.innerHTML = emptyConversationMarkup();
  activityList.innerHTML = emptyActivityMarkup();
  runState = "ready";
  activityStatus.textContent = t("ready");
  document.querySelector("#runStrip").classList.add("is-hidden");
  showToast(t("newSessionStarted"));
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
  event.innerHTML = `<span class="event-icon">${activitySequence}</span><div><strong></strong><p></p><time>${t("live")}</time></div>`;
  event.querySelector("strong").textContent = title;
  event.querySelector("p").textContent = detail;
  activityList.appendChild(event);
  event.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function setRunning(running) {
  isRunning = running;
  runState = running ? "running" : "ready";
  const agent = agents[selectedAgent];
  sendButton.disabled = running || !agent.ready;
  input.disabled = running || !agent.ready;
  document.querySelector("#agentStatus").textContent = running ? t("running") : t("ready");
  activityStatus.textContent = running ? t("running") : t("ready");
}

function finishRun(status, message) {
  eventSource?.close();
  eventSource = undefined;
  setRunning(false);
  runState = status === "completed" ? "completed" : "failed";
  document.querySelector("#runTitle").textContent = status === "completed" ? t("taskCompleted") : t("taskFailed");
  document.querySelector("#runMeta").textContent = message;
  activityStatus.textContent = status === "completed" ? t("completed") : t("failed");
}

function handleAgentEvent(event) {
  switch (event.type) {
    case "progress":
      document.querySelector("#runMeta").textContent = event.message;
      addActivity(t("progress"), event.message);
      break;
    case "skill_selected":
      addActivity(t("selectSkill"), `${event.skill} · ${event.task}`);
      break;
    case "command_started":
      addActivity(t("executeCommand"), event.skill);
      break;
    case "command_completed":
      addActivity(event.success ? t("commandCompleted") : t("commandFailed"), event.skill);
      break;
    case "copilot_activity":
      addActivity(t("copilotTool"), event.message);
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
      if (!assistantBody) assistantBody = appendMessage("assistant", event.answer || t("taskDoneFallback"));
      else assistantBody.textContent = event.answer || assistantBody.textContent;
      addActivity(t("generateAnalysis"), t("completed"));
      finishRun("completed", t("finalResult"));
      assistantBody = undefined;
      break;
    case "error":
      appendMessage("assistant", event.message || t("agentFailed"));
      addActivity(t("executionFailed"), event.message || "Unknown error");
      finishRun("error", t("checkServerLog"));
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
  document.querySelector("#runTitle").textContent = t("analyzingRequest");
  document.querySelector("#runMeta").textContent = t("connectingAgent");

  try {
    const response = await fetch("/api/agents/jenkins-log-analyst/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || t("requestFailed"));

    eventSource = new EventSource(`/api/runs/${payload.run_id}/events`);
    eventSource.onmessage = message => handleAgentEvent(JSON.parse(message.data));
    eventSource.onerror = () => {
      if (isRunning) {
        appendMessage("assistant", t("connectionInterrupted"));
        finishRun("error", t("connectionClosed"));
      }
    };
  } catch (error) {
    appendMessage("assistant", error.message || t("cannotConnect"));
    finishRun("error", t("requestNotSubmitted"));
  }
}

document.querySelector("#messageForm").addEventListener("submit", event => { event.preventDefault(); submitMessage(); });
input.addEventListener("keydown", event => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submitMessage(); } });
input.addEventListener("input", () => { input.style.height = "auto"; input.style.height = `${Math.min(input.scrollHeight, 130)}px`; });
applyTranslations();
