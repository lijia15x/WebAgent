const agents = {
  jenkins: { initials: "JL", title: "Jenkins Log Analyst", avatar: "avatar-jenkins", ready: true, descriptionKey: "agentDescription" },
  mrc: { initials: "MA", title: "MRC Automation", avatar: "avatar-mrc", ready: true, descriptionKey: "mrcDescription" },
};

const translations = {
  zh: {
    pageTitle: "Agent Desk",
    brandSubtitle: "运维工作台",
    closeAgentList: "关闭 Agent 列表",
    close: "关闭",
    agentList: "Agent 列表",
    idle: "空闲",
    previewReady: "预览就绪",
    moreAgents: "更多 Agent",
    comingSoon: "即将推出",
    servicesOnline: "服务在线",
    settings: "设置",
    openAgentList: "打开 Agent 列表",
    agentDescription: "定位构建失败原因，并结合 Workspace 源码给出修复建议",
    mrcDescription: "扫描每周 MRC Excel，筛选负责人、发送提醒邮件或生成汇报 PPT",
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
    mrcCycle: "报告周期",
    staticPreview: "手动操作模式",
    enableAutomation: "开启自动化",
    automationOn: "自动化已开启",
    automationEnabledPreview: "自动化已开启，手动操作已禁用",
    automationDisabledPreview: "自动化已关闭，手动操作已恢复",
    automationUpdateFailed: "无法更新自动化设置",
    scanningSharePoint: "正在扫描 SharePoint…",
    scanStarted: "MRC 扫描已启动",
    mailStarted: "邮件发送任务已启动",
    pptStarted: "PPT 生成任务已启动",
    scanCompleted: "MRC 扫描已完成并保存",
    noSavedScan: "该报告周期还没有已保存的扫描",
    noDrafts: "当前筛选没有负责人",
    snapshotLoadFailed: "无法加载已保存的扫描",
    scanSharePoint: "扫描 SharePoint",
    sendMail: "发送邮件",
    generatePpt: "生成 PPT",
    allOwnersOption: "全部",
    notUpdated: "未填写",
    mailCompleted: "邮件发送完成",
    pptCompleted: "PPT 生成完成",
    excelFiles: "Excel 文件",
    weeklyExcel: "当周 Excel",
    generatedPpt: "生成的 PPT",
    noExcelArtifacts: "暂无本地 Excel 文件",
    noPptArtifacts: "选择“生成 PPT”创建演示文稿",
    projectOwners: "项目负责人",
    individualDrafts: "每位负责人一封独立草稿",
    missingUpdates: "缺失更新",
    mondayRecipients: "周一提醒收件人",
    schedule: "提醒计划",
    allOwners: "全部负责人",
    firstReminder: "首次提醒",
    secondReminder: "再次提醒",
    missingOnly: "仅未填写者",
    finalReminder: "最终提醒",
    weeklyReport: "周报",
    recipients: "收件人",
    draftQueue: "草稿队列",
    drafts: "封草稿",
    dataQuality: "数据质量",
    dataQualityDetail: "跳过 1 行：负责人邮箱缺失。重复项目行已合并。",
    emailPreview: "邮件预览",
    openTemplate: "打开模板",
    subject: "主题",
    previewScanComplete: "静态扫描预览已更新",
  },
  en: {
    pageTitle: "Agent Desk",
    brandSubtitle: "Operations workspace",
    closeAgentList: "Close agent list",
    close: "Close",
    agentList: "Agent list",
    idle: "Idle",
    previewReady: "Preview ready",
    moreAgents: "More agents",
    comingSoon: "Coming soon",
    servicesOnline: "Services online",
    settings: "Settings",
    openAgentList: "Open agent list",
    agentDescription: "Find build failures and verify root causes against workspace source code",
    mrcDescription: "Scan weekly MRC workbooks, filter owners, send reminders, or generate report PPTs",
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
    mrcCycle: "Reporting cycle",
    staticPreview: "Manual operation mode",
    enableAutomation: "Enable automation",
    automationOn: "Automation on",
    automationEnabledPreview: "Automation enabled; manual controls are disabled",
    automationDisabledPreview: "Automation disabled; manual controls are available",
    automationUpdateFailed: "Unable to update automation settings",
    scanningSharePoint: "Scanning SharePoint…",
    scanStarted: "MRC scan started",
    mailStarted: "Mail delivery started",
    pptStarted: "PPT generation started",
    scanCompleted: "MRC scan completed and saved",
    noSavedScan: "No saved scan exists for this reporting cycle",
    noDrafts: "No owners match this filter",
    snapshotLoadFailed: "Unable to load the saved scan",
    scanSharePoint: "Scan SharePoint",
    sendMail: "Send Mail",
    generatePpt: "Generate PPT",
    allOwnersOption: "All",
    notUpdated: "Not Updated",
    mailCompleted: "Mail delivery completed",
    pptCompleted: "PPT generation completed",
    excelFiles: "Excel files",
    weeklyExcel: "Weekly Excel",
    generatedPpt: "Generated PPT",
    noExcelArtifacts: "No local Excel files",
    noPptArtifacts: "Choose Generate PPT to create presentations",
    projectOwners: "Project owners",
    individualDrafts: "One individual draft per owner",
    missingUpdates: "Missing updates",
    mondayRecipients: "Monday reminder recipients",
    schedule: "Schedule",
    allOwners: "All owners",
    firstReminder: "First reminder",
    secondReminder: "Second reminder",
    missingOnly: "Missing only",
    finalReminder: "Final reminder",
    weeklyReport: "Weekly report",
    recipients: "Recipients",
    draftQueue: "Draft queue",
    drafts: "drafts",
    dataQuality: "Data quality",
    dataQualityDetail: "1 row skipped: missing owner email. Duplicate project rows were merged.",
    emailPreview: "Email preview",
    openTemplate: "Open template",
    subject: "Subject",
    previewScanComplete: "Static scan preview refreshed",
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
const mrcWorkspace = document.querySelector("#mrcWorkspace");
const contentGrid = document.querySelector(".content-grid");
const composerWrap = document.querySelector("#composerWrap");
let selectedAgent = "jenkins";
let currentLanguage = "en";
let toastTimer;
let eventSource;
let mrcEventSource;
let isRunning = false;
let automationEnabled = false;
let mrcScanRunning = false;
let currentMrcDrafts = [];
let draftFilter = "all";
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
  document.querySelector("#agentDescription").textContent = t(agents[selectedAgent].descriptionKey);
  activityStatus.textContent = t(runState);
  document.querySelector("#agentStatus").textContent = isRunning ? t("running") : t("ready");
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("is-visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 2400);
}

function updateAutomationControls() {
  const toggle = document.querySelector("#automationToggle");
  toggle.classList.toggle("is-active", automationEnabled);
  toggle.setAttribute("aria-pressed", String(automationEnabled));
  const label = toggle.querySelector("[data-i18n]");
  label.dataset.i18n = automationEnabled ? "automationOn" : "enableAutomation";
  label.textContent = t(label.dataset.i18n);
  toggle.disabled = mrcScanRunning;
  document.querySelector("#scanPreview").disabled = automationEnabled || mrcScanRunning;
  document.querySelector("#previousWeek").disabled = automationEnabled || mrcScanRunning;
  document.querySelector("#nextWeek").disabled = automationEnabled || mrcScanRunning;
  document.querySelector("#sendMail").disabled = automationEnabled || mrcScanRunning;
  document.querySelector("#sendAll").disabled = automationEnabled || mrcScanRunning;
  document.querySelector("#generatePpt").disabled = automationEnabled || mrcScanRunning;
  document.querySelector("#openTemplate").disabled = automationEnabled || mrcScanRunning;
  document.querySelectorAll("[data-draft-filter]").forEach(button => {
    button.disabled = automationEnabled || mrcScanRunning;
  });
}

function renderArtifacts(artifacts) {
  const groups = { excel: [], ppt: [] };
  (artifacts || []).forEach(artifact => {
    if (groups[artifact.kind]) groups[artifact.kind].push(artifact);
  });
  Object.entries(groups).forEach(([kind, items]) => {
    const container = document.querySelector(`#${kind}Artifacts`);
    container.replaceChildren();
    if (!items.length) {
      const empty = document.createElement("span");
      empty.className = "artifact-empty";
      empty.textContent = t(kind === "excel" ? "noExcelArtifacts" : "noPptArtifacts");
      container.append(empty);
      return;
    }
    items.forEach(artifact => {
      const link = document.createElement("a");
      link.className = "artifact-link";
      link.href = artifact.download_url;
      link.download = artifact.file_name;
      link.textContent = artifact.file_name;
      container.append(link);
    });
  });
}

function renderDraftQueue() {
  const drafts = draftFilter === "missing"
    ? currentMrcDrafts.filter(draft => Number(draft.missing_updates || 0) > 0)
    : currentMrcDrafts;
  document.querySelector("#draftCount").textContent = drafts.length;
  const draftList = document.querySelector("#draftList");
  draftList.replaceChildren();
  if (!drafts.length) {
    const empty = document.createElement("p");
    empty.className = "activity-empty";
    empty.textContent = t("noDrafts");
    draftList.append(empty);
    document.querySelector("#previewRecipient").textContent = "—";
    document.querySelector("#emailSubject").textContent = "—";
    document.querySelector("#emailCanvas").replaceChildren();
    return;
  }
  drafts.forEach((draft, index) => {
    const row = document.createElement("button");
    row.className = `draft-row${index === 0 ? " is-selected" : ""}`;
    row.type = "button";
    const initials = (draft.owner_name || draft.owner_email)
      .split(/[\s.@_-]+/).filter(Boolean).slice(0, 2)
      .map(part => part[0].toUpperCase()).join("");
    const mark = document.createElement("span");
    mark.className = "owner-mark";
    mark.textContent = initials;
    const details = document.createElement("span");
    const email = document.createElement("strong");
    email.textContent = draft.owner_email;
    const count = document.createElement("small");
    count.textContent = `${draft.project_count ?? 0} project(s)`;
    details.append(email, count);
    const badge = document.createElement("b");
    badge.textContent = draft.project_count ?? 0;
    row.append(mark, details, badge);
    row.addEventListener("click", () => selectMrcDraft(draft, row));
    draftList.append(row);
  });
  if (drafts[0]) selectMrcDraft(drafts[0], draftList.firstElementChild);
}

function applyMrcSnapshot(snapshot) {
  document.querySelector("#fileCount").textContent = snapshot.files_found ?? 0;
  document.querySelector("#ownerCount").textContent = snapshot.owners_found ?? 0;
  document.querySelector("#missingCount").textContent = snapshot.missing_comments ?? 0;
  if (snapshot.workbook_names) {
    document.querySelector("#workbookNames").textContent = snapshot.workbook_names.join(" · ");
  }
  renderArtifacts(snapshot.artifacts || []);
  currentMrcDrafts = snapshot.drafts || [];
  renderDraftQueue();
}

function selectMrcDraft(draft, selectedRow) {
  document.querySelectorAll(".draft-row").forEach(row => row.classList.toggle("is-selected", row === selectedRow));
  document.querySelector("#previewRecipient").textContent = draft.owner_email;
  const previewOwner = document.querySelector("#previewOwner");
  if (previewOwner) previewOwner.textContent = draft.owner_name || draft.owner_email;
  document.querySelector("#emailSubject").textContent = draft.subject;
  if (draft.body_html) {
    const emailDocument = new DOMParser().parseFromString(draft.body_html, "text/html");
    document.querySelector("#emailCanvas").innerHTML = emailDocument.body.innerHTML;
  }
}

async function loadMrcSnapshot(cycleCode) {
  try {
    const response = await fetch(`/api/agents/mrc-automation/cycles/${cycleCode}/latest`);
    if (response.status === 404) {
      applyMrcSnapshot({
        files_found: 0,
        owners_found: 0,
        missing_comments: 0,
        workbook_names: [],
        drafts: [],
        artifacts: [],
      });
      showToast(t("noSavedScan"));
      return;
    }
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || t("snapshotLoadFailed"));
    applyMrcSnapshot(payload);
  } catch (error) {
    showToast(error.message || t("snapshotLoadFailed"));
  }
}

async function loadMrcAutomation() {
  try {
    const response = await fetch("/api/agents/mrc-automation/automation");
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || t("automationUpdateFailed"));
    automationEnabled = Boolean(payload.enabled);
    updateAutomationControls();
  } catch (error) {
    showToast(error.message || t("automationUpdateFailed"));
  }
}

async function runMrcAction(endpoint, body, startedMessage) {
  if (automationEnabled || mrcScanRunning) return;
  mrcScanRunning = true;
  updateAutomationControls();
  const cycleCode = document.querySelector("#targetWeek").textContent;
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || t("requestFailed"));
    showToast(startedMessage);
    mrcEventSource = new EventSource(`/api/runs/${payload.run_id}/events`);
    mrcEventSource.onmessage = message => {
      const event = JSON.parse(message.data);
      if (event.type === "progress") showToast(event.message);
      if (event.type === "completed") {
        loadMrcSnapshot(cycleCode);
        if (event.operation === "mail") {
          showToast(`${t("mailCompleted")}: ${event.sent} sent, ${event.failed} failed`);
        } else if (event.operation === "ppt") {
          showToast(t("pptCompleted"));
        } else {
          showToast(t("scanCompleted"));
        }
        mrcScanRunning = false;
        updateAutomationControls();
        mrcEventSource.close();
      }
      if (event.type === "error") {
        showToast(event.message);
        mrcScanRunning = false;
        updateAutomationControls();
        mrcEventSource.close();
      }
    };
    mrcEventSource.onerror = () => {
      if (!mrcScanRunning) return;
      showToast(t("connectionInterrupted"));
      mrcScanRunning = false;
      updateAutomationControls();
      mrcEventSource.close();
    };
  } catch (error) {
    showToast(error.message || t("cannotConnect"));
    mrcScanRunning = false;
    updateAutomationControls();
  }
}

function runMrcScan() {
  const cycleCode = document.querySelector("#targetWeek").textContent;
  return runMrcAction(
    "/api/agents/mrc-automation/scans",
    { cycle_code: cycleCode },
    t("scanStarted"),
  );
}

function sendMrcMail() {
  const cycleCode = document.querySelector("#targetWeek").textContent;
  return runMrcAction(
    `/api/agents/mrc-automation/cycles/${cycleCode}/mail`,
    { include_all: document.querySelector("#sendAll").checked },
    t("mailStarted"),
  );
}

function generateMrcPpt() {
  const cycleCode = document.querySelector("#targetWeek").textContent;
  return runMrcAction(
    `/api/agents/mrc-automation/cycles/${cycleCode}/ppt`,
    {},
    t("pptStarted"),
  );
}

function isoWeekParts(date) {
  const localDate = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const day = localDate.getUTCDay() || 7;
  localDate.setUTCDate(localDate.getUTCDate() + 4 - day);
  const isoYear = localDate.getUTCFullYear();
  const yearStart = new Date(Date.UTC(isoYear, 0, 1));
  const week = Math.ceil((((localDate - yearStart) / 86400000) + 1) / 7);
  return { year: isoYear, week };
}

function cycleCodeForDate(date) {
  const { year, week } = isoWeekParts(date);
  return `${year}WW${String(week).padStart(2, "0")}`;
}

function setTargetWeek(cycleCode, loadSnapshot = true) {
  const target = document.querySelector("#targetWeek");
  target.textContent = cycleCode;
  document.querySelector("#emailSubject").textContent = `Action required: update project status for ${cycleCode}`;
  if (loadSnapshot) loadMrcSnapshot(cycleCode);
}

function setAgent(id) {
  const agent = agents[id];
  selectedAgent = id;
  document.querySelectorAll(".agent-item").forEach(item => item.classList.toggle("is-active", item.dataset.agent === id));
  const avatar = document.querySelector("#headerAvatar");
  avatar.className = `agent-avatar ${agent.avatar}`;
  avatar.textContent = agent.initials;
  document.querySelector("#agentTitle").textContent = agent.title;
  document.querySelector("#agentDescription").textContent = t(agent.descriptionKey);
  document.querySelector("#agentStatus").textContent = t("ready");
  const isMrc = id === "mrc";
  document.querySelector(".chat-workspace").classList.toggle("mrc-mode", isMrc);
  contentGrid.classList.toggle("is-hidden", isMrc);
  composerWrap.classList.toggle("is-hidden", isMrc);
  mrcWorkspace.classList.toggle("is-hidden", !isMrc);
  document.querySelector("#activityToggle").classList.toggle("is-hidden", isMrc);
  document.querySelector("#runStrip").classList.add("is-hidden");
  sendButton.disabled = !agent.ready || isRunning || isMrc;
  input.disabled = !agent.ready || isRunning || isMrc;
  input.placeholder = t("messagePlaceholder");
  sidebar.classList.remove("is-open");
  if (isMrc) {
    const currentCycle = cycleCodeForDate(new Date());
    setTargetWeek(currentCycle, false);
    loadMrcAutomation();
    loadMrcSnapshot(currentCycle);
  }
}

document.querySelectorAll("button.agent-item[data-agent]").forEach(item => item.addEventListener("click", () => setAgent(item.dataset.agent)));
document.querySelector("#openSidebar").addEventListener("click", () => sidebar.classList.add("is-open"));
document.querySelector("#closeSidebar").addEventListener("click", () => sidebar.classList.remove("is-open"));
document.querySelector("#activityToggle").addEventListener("click", () => activityPanel.classList.toggle("is-hidden"));
document.querySelector("#closeActivity").addEventListener("click", () => activityPanel.classList.add("is-hidden"));
document.querySelector("#stripClose").addEventListener("click", () => document.querySelector("#runStrip").classList.add("is-hidden"));
document.querySelector("#settingsButton").addEventListener("click", () => showToast(t("settingsUnavailable")));
document.querySelector("#automationToggle").addEventListener("click", async () => {
  const requestedState = !automationEnabled;
  try {
    const response = await fetch("/api/agents/mrc-automation/automation", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: requestedState }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || t("automationUpdateFailed"));
    automationEnabled = Boolean(payload.enabled);
    updateAutomationControls();
    showToast(t(automationEnabled ? "automationEnabledPreview" : "automationDisabledPreview"));
  } catch (error) {
    showToast(error.message || t("automationUpdateFailed"));
  }
});
document.querySelector("#scanPreview").addEventListener("click", runMrcScan);
document.querySelector("#sendMail").addEventListener("click", sendMrcMail);
document.querySelector("#generatePpt").addEventListener("click", generateMrcPpt);
document.querySelectorAll("[data-draft-filter]").forEach(button => {
  button.addEventListener("click", () => {
    draftFilter = button.dataset.draftFilter;
    document.querySelectorAll("[data-draft-filter]").forEach(item => item.classList.toggle("is-active", item === button));
    renderDraftQueue();
  });
});
document.querySelector("#openTemplate").addEventListener("click", () => {
  document.querySelector("#emailDialogBody").innerHTML = document.querySelector(".email-canvas").outerHTML;
  document.querySelector("#emailDialog").showModal();
});
document.querySelector("#closeEmailDialog").addEventListener("click", () => document.querySelector("#emailDialog").close());

const draftSamples = [
  { owner: "Alex", email: "alex.kim@example.com", projects: [["Core Platform", "Atlas Migration"], ["Core Platform", "Runtime Refresh"]] },
  { owner: "Maya", email: "maya.singh@example.com", projects: [["Data Systems", "Metrics Hub"]] },
  { owner: "Jordan", email: "jordan.lee@example.com", projects: [["Validation", "Falcon CI"]] },
];

document.querySelectorAll(".draft-row").forEach(button => button.addEventListener("click", () => {
  document.querySelectorAll(".draft-row").forEach(row => row.classList.toggle("is-selected", row === button));
  const draft = draftSamples[Number(button.dataset.draft)];
  document.querySelector("#previewRecipient").textContent = draft.email;
  document.querySelector("#previewOwner").textContent = draft.owner;
  document.querySelector("#previewProjects").innerHTML = draft.projects.map(([group, project]) => `<tr><td>${group}</td><td>${project}</td><td><span class="missing-pill">Missing</span></td></tr>`).join("");
}));

function shiftTargetWeek(offset) {
  const match = document.querySelector("#targetWeek").textContent.match(/^(\d{4})WW(\d{2})$/);
  if (!match) return;
  const isoYear = Number(match[1]);
  const isoWeek = Number(match[2]);
  const januaryFourth = new Date(isoYear, 0, 4);
  const januaryFourthDay = januaryFourth.getDay() || 7;
  const monday = new Date(isoYear, 0, 4 - januaryFourthDay + 1);
  monday.setDate(monday.getDate() + ((isoWeek - 1 + offset) * 7));
  setTargetWeek(cycleCodeForDate(monday));
}

document.querySelector("#previousWeek").addEventListener("click", () => shiftTargetWeek(-1));
document.querySelector("#nextWeek").addEventListener("click", () => shiftTargetWeek(1));
languageToggle.addEventListener("click", () => {
  currentLanguage = currentLanguage === "zh" ? "en" : "zh";
  applyTranslations();
  updateAutomationControls();
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
  if (selectedAgent !== "jenkins") return;
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
