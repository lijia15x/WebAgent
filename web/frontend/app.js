const agents = {
  jenkins: { initials: "JL", title: "Jenkins Log Analyst", avatar: "avatar-jenkins", ready: true, descriptionKey: "agentDescription" },
  mrc: { initials: "MA", title: "MRC Automation", avatar: "avatar-mrc", ready: true, descriptionKey: "mrcDescription" },
  "pdf-yaml": { initials: "PY", title: "PDF-to-YAML Architecture", avatar: "avatar-pdf", ready: true, descriptionKey: "pdfYamlDescription" },
  i2c: { initials: "IA", title: "I2C Automation", avatar: "avatar-i2c", ready: true, descriptionKey: "i2cDescription" },
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
    pdfYamlDescription: "从 PDF 架构图提取可追溯的结构化 YAML",
    i2cDescription: "解析示波器 CSV 波形，生成 I2C/SMBus 协议交易和导出报告",
    workspaceReady: "工作区就绪",
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
    workingDetails: "正在执行…",
    completedSteps: "已完成 {steps} 个步骤，耗时 {duration}",
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
    pptUploadStarted: "PPT 上传任务已启动",
    scanCompleted: "MRC 扫描已完成并保存",
    noSavedScan: "该报告周期还没有已保存的扫描",
    noDrafts: "当前筛选没有负责人",
    snapshotLoadFailed: "无法加载已保存的扫描",
    reminderTemplate: "提醒邮件模板",
    scanSharePoint: "扫描 SharePoint",
    sendMail: "发送邮件",
    confirmMailTitle: "确认发送邮件",
    confirmMailScopeAll: "将发送 {cycle} 的全部邮件草稿。",
    confirmMailScopeMissing: "将发送 {cycle} 中仅未填写负责人的邮件草稿。",
    confirmMailWarning: "邮件将立即发送，且无法撤回。",
    sendTestMail: "测试邮件",
    recipientEmail: "收件邮箱",
    recipientEmailPlaceholder: "name@example.com",
    testMailHint: "使用所选报告周期中第一个未填写负责人的邮件内容。",
    cancel: "取消",
    confirmSend: "发送",
    testMailStarted: "测试邮件发送任务已启动",
    testMailCompleted: "测试邮件已发送",
    generatePpt: "生成 PPT",
    uploadPpt: "上传 PPT",
    allOwnersOption: "全部",
    notUpdated: "未填写",
    mailCompleted: "邮件发送完成",
    pptCompleted: "PPT 生成完成",
    pptUploadCompleted: "PPT 已上传到 SharePoint",
    generatePptFirst: "请先生成 PPT",
    excelFiles: "Excel 文件",
    weeklyExcel: "当周 Excel",
    generatedPpt: "生成的 PPT",
    noExcelArtifacts: "暂无本地 Excel 文件",
    noPptArtifacts: "选择“生成 PPT”创建演示文稿",
    projectOwners: "项目负责人",
    individualDrafts: "每位负责人一封独立草稿",
    missingUpdates: "缺失更新",
    lastReminderRecipients: "最终提醒收件人",
    schedule: "提醒计划",
    allOwners: "全部负责人",
    firstReminder: "首次提醒",
    secondReminder: "再次提醒",
    missingOnly: "仅未填写者",
    finalReminder: "最终提醒",
    weeklyReport: "周报",
    summary: "摘要",
    recipients: "收件人",
    draftQueue: "草稿队列",
    drafts: "封草稿",
    draftQueuePages: "草稿队列分页",
    previousPage: "上一页",
    nextPage: "下一页",
    dataQuality: "数据质量",
    dataQualityDetail: "跳过 1 行：负责人邮箱缺失。重复项目行已合并。",
    emailPreview: "邮件预览",
    openTemplate: "打开模板",
    subject: "主题",
    previewScanComplete: "静态扫描预览已更新",
    architecturePipeline: "架构处理流程",
    pdfWorkspaceTitle: "将架构图转换为可追溯的 YAML",
    pdfWorkspaceDescription: "配置 SharePoint 来源或直接上传 PDF。参考指南将作为 AI 提取时使用的编写规则。",
    configurationStage: "配置阶段",
    sharePointSource: "SharePoint 来源",
    futureSource: "未来来源",
    sourceLocation: "来源位置",
    notSaved: "未保存",
    saved: "已保存",
    sharePointAddress: "SharePoint 文件夹地址",
    saveAddress: "保存地址",
    sharePointHint: "SharePoint 集成启用后，Agent 将扫描该位置中的 PDF 文件。",
    directUpload: "直接上传",
    architecturePdf: "架构 PDF",
    requiredInput: "必需输入",
    choosePdf: "选择架构 PDF",
    pdfUploadHint: "仅支持 PDF · 每次转换一个文档",
    authoringContext: "编写上下文",
    referenceFiles: "AI 参考文件",
    workspaceResource: "Workspace",
    addFiles: "添加文件",
    referenceHint: "上传 YAML 编写指南和相关规范。上传后可在此工作区下载。",
    noReferenceFiles: "尚未上传参考文件",
    referenceTypes: "支持 Markdown、PDF、YAML 和文本",
    conversionRun: "转换任务",
    generateYaml: "生成 YAML",
    readDocument: "读取文档",
    readDocumentDetail: "定位架构图",
    extractTopology: "提取拓扑",
    extractTopologyDetail: "板卡、器件、端口和连接",
    validateYaml: "校验 YAML",
    validateYamlDetail: "Schema 与可追溯性检查",
    runRequirement: "选择本地 PDF 后即可准备转换。",
    enginePending: "PDF 与参考文件仅在本次转换中发送给 Copilot。",
    addressSaved: "SharePoint 地址已保存",
    enterValidAddress: "请输入有效的 SharePoint 地址",
    pdfSelected: "已选择 PDF 文件",
    invalidPdf: "请选择 PDF 文件",
    preparingPdf: "正在上传并定位架构图",
    filteringPdf: "正在精简 PDF",
    pdfPrepared: "精简 PDF 已就绪",
    pdfPreparationFailed: "PDF 精简失败",
    preparedPdfDownloaded: "精简 PDF 已下载",
    referenceAdded: "参考文件已添加",
    invalidReference: "仅支持 Markdown、PDF、YAML 或文本参考文件",
    referenceLoadFailed: "无法加载服务器参考文件",
    referenceUploadFailed: "参考文件上传失败",
    referenceDeleted: "参考文件已删除",
    referenceDeleteFailed: "参考文件删除失败",
    generatedArtifact: "生成产物",
    generatedOutput: "Copilot 结果",
    copyYaml: "复制",
    downloadYaml: "下载 .yml",
    regenerateYaml: "重新生成",
    sourceDocument: "来源文档",
    sourcePages: "来源页码",
    sourcePagesPending: "等待 AI 识别",
    generatedAt: "生成时间",
    yamlCopied: "YAML 已复制",
    yamlDownloaded: "YAML 文件已下载",
    generatingYaml: "Copilot 正在生成…",
    generationReady: "等待生成",
    generationStarting: "正在启动生成任务",
    generationFiltering: "正在读取架构图",
    generationGenerating: "Copilot 正在提取拓扑",
    generationValidating: "正在校验 YAML",
    generationRepairing: "正在自动修复 YAML",
    generationRevalidating: "正在校验修复结果",
    generationCompleted: "生成并校验完成",
    generationReviewRequired: "已生成，需要复核拓扑警告",
    generationFailed: "生成失败",
    elapsedTime: "已用时间",
    copilotActivity: "Copilot 运行动态",
    copilotWaiting: "等待开始",
    viewCopilotHistory: "查看全部记录",
    copilotHistoryTitle: "Copilot 运行记录",
    copilotHistoryHint: "当前转换中 Copilot SDK 返回的过程、工具和输出消息",
    copilotHistoryProcess: "过程",
    copilotHistoryOutput: "输出",
    copilotHistoryTool: "工具",
    activityContextReady: "已提交精简架构图和参考文件",
    activityAnalyzing: "Copilot 正在分析板卡、器件和连接",
    activityInspectingInputs: "Copilot 正在检查输入内容",
    activityWritingYaml: "Copilot 正在生成 YAML",
    activityResponseReceived: "已收到 Copilot 输出，准备校验",
    activityRepairingYaml: "Copilot 正在生成最小修复补丁",
    yamlGenerated: "YAML 已生成并通过校验",
    yamlReviewRequired: "YAML 结构有效，但存在需要复核的拓扑警告",
    yamlGenerationFailed: "YAML 生成失败",
    i2cPipeline: "波形解码器",
    i2cWorkspaceTitle: "解码 I2C 和 SMBus CSV 波形",
    i2cWorkspaceDescription: "上传包含 time、SCL 和 SDA 列的示波器 CSV。解码器会导出协议明细、文本报告和表格摘要。",
    i2cCaptureCsv: "采样 CSV",
    chooseI2cCsv: "选择示波器 CSV",
    i2cUploadHint: "仅支持 CSV · 每次解码一个采样文件",
    timeColumn: "时间列",
    sclColumn: "SCL 列",
    sdaColumn: "SDA 列",
    sclThreshold: "SCL 阈值",
    sdaThreshold: "SDA 阈值",
    hysteresis: "迟滞比例",
    decodeI2c: "解码采样",
    decodeResult: "解码结果",
    waitingForCapture: "等待采样文件",
    transactions: "交易数",
    completeTransactions: "完整交易",
    addresses: "地址",
    sclFrequency: "SCL 频率",
    noI2cArtifacts: "运行解码后生成产物",
    noDecodedTransactions: "暂无解码交易",
    i2cCsvSelected: "已选择 CSV 文件",
    i2cInvalidCsv: "请选择 CSV 文件",
    i2cDecoding: "正在解码 I2C 采样…",
    i2cDecodeStarted: "I2C 解码已启动",
    i2cDecodeCompleted: "I2C 解码完成",
    i2cDecodeFailed: "I2C 解码失败",
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
    pdfYamlDescription: "Extract traceable, structured YAML from PDF architecture diagrams",
    i2cDescription: "Decode oscilloscope CSV waveforms into I2C/SMBus transactions and export reports",
    workspaceReady: "Workspace ready",
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
    workingDetails: "Working…",
    completedSteps: "Completed {steps} steps in {duration}",
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
    pptUploadStarted: "PPT upload started",
    scanCompleted: "MRC scan completed and saved",
    noSavedScan: "No saved scan exists for this reporting cycle",
    noDrafts: "No owners match this filter",
    snapshotLoadFailed: "Unable to load the saved scan",
    reminderTemplate: "Reminder template",
    scanSharePoint: "Scan SharePoint",
    sendMail: "Send Mail",
    confirmMailTitle: "Confirm mail delivery",
    confirmMailScopeAll: "Send all email drafts for {cycle}.",
    confirmMailScopeMissing: "Send email drafts only to owners with missing updates for {cycle}.",
    confirmMailWarning: "Emails will be sent immediately and cannot be recalled.",
    sendTestMail: "Test Mail",
    recipientEmail: "Recipient email",
    recipientEmailPlaceholder: "name@example.com",
    testMailHint: "Uses the first owner with a missing update in the selected reporting cycle.",
    cancel: "Cancel",
    confirmSend: "Send",
    testMailStarted: "Test mail delivery started",
    testMailCompleted: "Test mail sent",
    generatePpt: "Generate PPT",
    uploadPpt: "Upload PPT",
    allOwnersOption: "All",
    notUpdated: "Not Updated",
    mailCompleted: "Mail delivery completed",
    pptCompleted: "PPT generation completed",
    pptUploadCompleted: "PPT uploaded to SharePoint",
    generatePptFirst: "Please generate PPT first",
    excelFiles: "Excel files",
    weeklyExcel: "Weekly Excel",
    generatedPpt: "Generated PPT",
    noExcelArtifacts: "No local Excel files",
    noPptArtifacts: "Choose Generate PPT to create presentations",
    projectOwners: "Project owners",
    individualDrafts: "One individual draft per owner",
    missingUpdates: "Missing updates",
    lastReminderRecipients: "Final reminder recipients",
    schedule: "Schedule",
    allOwners: "All owners",
    firstReminder: "First reminder",
    secondReminder: "Second reminder",
    missingOnly: "Missing only",
    finalReminder: "Final reminder",
    weeklyReport: "Weekly report",
    summary: "Summary",
    recipients: "Recipients",
    draftQueue: "Draft queue",
    drafts: "drafts",
    draftQueuePages: "Draft queue pages",
    previousPage: "Previous page",
    nextPage: "Next page",
    dataQuality: "Data quality",
    dataQualityDetail: "1 row skipped: missing owner email. Duplicate project rows were merged.",
    emailPreview: "Email preview",
    openTemplate: "Open template",
    subject: "Subject",
    previewScanComplete: "Static scan preview refreshed",
    architecturePipeline: "Architecture pipeline",
    pdfWorkspaceTitle: "Turn architecture diagrams into traceable YAML",
    pdfWorkspaceDescription: "Configure a SharePoint source or upload a PDF directly. Reference guides provide the authoring rules used during extraction.",
    configurationStage: "Configuration stage",
    sharePointSource: "SharePoint source",
    futureSource: "Future source",
    sourceLocation: "Source location",
    notSaved: "Not saved",
    saved: "Saved",
    sharePointAddress: "SharePoint folder address",
    saveAddress: "Save address",
    sharePointHint: "The agent will scan PDF files from this location when SharePoint integration is enabled.",
    directUpload: "Direct upload",
    architecturePdf: "Architecture PDF",
    requiredInput: "Required input",
    choosePdf: "Choose an architecture PDF",
    pdfUploadHint: "PDF only · one document per conversion",
    authoringContext: "Authoring context",
    referenceFiles: "AI reference files",
    workspaceResource: "Workspace",
    addFiles: "Add files",
    referenceHint: "Upload the YAML authoring guide and related specifications. Uploaded files remain available for download in this workspace.",
    noReferenceFiles: "No reference files uploaded",
    referenceTypes: "Accepted formats: Markdown, PDF, YAML and text",
    conversionRun: "Conversion run",
    generateYaml: "Generate YAML",
    readDocument: "Read document",
    readDocumentDetail: "Locate architecture diagrams",
    extractTopology: "Extract topology",
    extractTopologyDetail: "Boards, elements, ports, connections",
    validateYaml: "Validate YAML",
    validateYamlDetail: "Schema and traceability checks",
    runRequirement: "Choose a local PDF to prepare a conversion.",
    enginePending: "The PDF and reference files are sent to Copilot for this conversion only.",
    addressSaved: "SharePoint address saved",
    enterValidAddress: "Enter a valid SharePoint address",
    pdfSelected: "PDF selected",
    invalidPdf: "Choose a PDF file",
    preparingPdf: "Uploading and locating architecture figures",
    filteringPdf: "Reducing PDF",
    pdfPrepared: "Reduced PDF ready",
    pdfPreparationFailed: "PDF reduction failed",
    preparedPdfDownloaded: "Reduced PDF downloaded",
    referenceAdded: "Reference files added",
    invalidReference: "Only Markdown, PDF, YAML or text reference files are supported",
    referenceLoadFailed: "Unable to load server reference files",
    referenceUploadFailed: "Reference file upload failed",
    referenceDeleted: "Reference file deleted",
    referenceDeleteFailed: "Reference file deletion failed",
    generatedArtifact: "Generated artifact",
    generatedOutput: "Copilot output",
    copyYaml: "Copy",
    downloadYaml: "Download .yml",
    regenerateYaml: "Regenerate",
    sourceDocument: "Source document",
    sourcePages: "Source pages",
    sourcePagesPending: "Pending AI detection",
    generatedAt: "Generated",
    yamlCopied: "YAML copied",
    yamlDownloaded: "YAML file downloaded",
    generatingYaml: "Copilot is generating…",
    generationReady: "Ready to generate",
    generationStarting: "Starting generation",
    generationFiltering: "Reading architecture figures",
    generationGenerating: "Copilot is extracting topology",
    generationValidating: "Validating YAML",
    generationRepairing: "Automatically repairing YAML",
    generationRevalidating: "Validating repaired YAML",
    generationCompleted: "Generation and validation complete",
    generationReviewRequired: "Generated; topology review required",
    generationFailed: "Generation failed",
    elapsedTime: "Elapsed time",
    copilotActivity: "Copilot activity",
    copilotWaiting: "Waiting to start",
    viewCopilotHistory: "View full history",
    copilotHistoryTitle: "Copilot activity history",
    copilotHistoryHint: "Process, tool, and output messages returned by Copilot SDK for this conversion",
    copilotHistoryProcess: "Process",
    copilotHistoryOutput: "Output",
    copilotHistoryTool: "Tool",
    activityContextReady: "Reduced architecture and references submitted",
    activityAnalyzing: "Copilot is analyzing boards, elements, and connections",
    activityInspectingInputs: "Copilot is inspecting the input",
    activityWritingYaml: "Copilot is generating YAML",
    activityResponseReceived: "Copilot response received; validation is next",
    activityRepairingYaml: "Copilot is preparing a minimal repair patch",
    yamlGenerated: "YAML generated and validated",
    yamlReviewRequired: "YAML structure is valid, but topology warnings require review",
    yamlGenerationFailed: "YAML generation failed",
    i2cPipeline: "Waveform decoder",
    i2cWorkspaceTitle: "Decode I2C and SMBus CSV captures",
    i2cWorkspaceDescription: "Upload oscilloscope CSV captures with time, SCL and SDA columns. The decoder exports protocol detail, text report and a spreadsheet summary.",
    i2cCaptureCsv: "Capture CSV",
    chooseI2cCsv: "Choose an oscilloscope CSV",
    i2cUploadHint: "CSV only · one capture per decode",
    timeColumn: "Time column",
    sclColumn: "SCL column",
    sdaColumn: "SDA column",
    sclThreshold: "SCL threshold",
    sdaThreshold: "SDA threshold",
    hysteresis: "Hysteresis",
    decodeI2c: "Decode capture",
    decodeResult: "Decode result",
    waitingForCapture: "Waiting for capture",
    transactions: "Transactions",
    completeTransactions: "Complete",
    addresses: "Addresses",
    sclFrequency: "SCL frequency",
    noI2cArtifacts: "Run a decode to create artifacts",
    noDecodedTransactions: "No decoded transactions yet",
    i2cCsvSelected: "CSV selected",
    i2cInvalidCsv: "Choose a CSV file",
    i2cDecoding: "Decoding I2C capture…",
    i2cDecodeStarted: "I2C decode started",
    i2cDecodeCompleted: "I2C decode completed",
    i2cDecodeFailed: "I2C decode failed",
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
const pdfWorkspace = document.querySelector("#pdfWorkspace");
const i2cWorkspace = document.querySelector("#i2cWorkspace");
const contentGrid = document.querySelector(".content-grid");
const composerWrap = document.querySelector("#composerWrap");
let selectedAgent = "jenkins";
let currentLanguage = "en";
let toastTimer;
let eventSource;
let mrcEventSource;
let i2cEventSource;
let isRunning = false;
let i2cDecodeRunning = false;
let automationEnabled = false;
let mrcScanRunning = false;
let currentMrcDrafts = [];
let draftFilter = "all";
let currentDraftPage = 1;
const draftsPerPage = 10;
let runState = "ready";
let activitySequence = 0;
let assistantBody;
let processDetails;
let processContent;
let finalAnswer;
let runStartedAt = 0;

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
  toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 5000);
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
  document.querySelectorAll('input[name="reminderType"]').forEach(input => {
    input.disabled = automationEnabled || mrcScanRunning;
  });
  document.querySelector("#previousWeek").disabled = automationEnabled || mrcScanRunning;
  document.querySelector("#nextWeek").disabled = automationEnabled || mrcScanRunning;
  document.querySelector("#sendMail").disabled = automationEnabled || mrcScanRunning;
  document.querySelector("#sendTestMail").disabled = automationEnabled || mrcScanRunning;
  document.querySelector("#sendAll").disabled = automationEnabled || mrcScanRunning;
  document.querySelector("#generatePpt").disabled = automationEnabled || mrcScanRunning;
  document.querySelector("#uploadPpt").disabled = automationEnabled || mrcScanRunning;
  document.querySelector("#openTemplate").disabled = automationEnabled || mrcScanRunning;
  document.querySelectorAll("[data-draft-filter]").forEach(button => {
    button.disabled = automationEnabled || mrcScanRunning;
  });
  const visibleDraftCount = draftFilter === "missing"
    ? currentMrcDrafts.filter(draft => Number(draft.missing_updates || 0) > 0).length
    : currentMrcDrafts.length;
  const pageCount = Math.max(1, Math.ceil(visibleDraftCount / draftsPerPage));
  document.querySelector("#previousDraftPage").disabled = automationEnabled || mrcScanRunning || currentDraftPage === 1;
  document.querySelector("#nextDraftPage").disabled = automationEnabled || mrcScanRunning || currentDraftPage === pageCount;
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
  const pageCount = Math.max(1, Math.ceil(drafts.length / draftsPerPage));
  currentDraftPage = Math.min(currentDraftPage, pageCount);
  const pageDrafts = drafts.slice((currentDraftPage - 1) * draftsPerPage, currentDraftPage * draftsPerPage);
  document.querySelector("#draftCount").textContent = drafts.length;
  document.querySelector("#draftPagination").classList.toggle("is-hidden", pageCount <= 1);
  document.querySelector("#draftPageStatus").textContent = `${currentDraftPage} / ${pageCount}`;
  document.querySelector("#previousDraftPage").disabled = currentDraftPage === 1 || automationEnabled || mrcScanRunning;
  document.querySelector("#nextDraftPage").disabled = currentDraftPage === pageCount || automationEnabled || mrcScanRunning;
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
  pageDrafts.forEach((draft, index) => {
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
  if (pageDrafts[0]) selectMrcDraft(pageDrafts[0], draftList.firstElementChild);
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
  currentDraftPage = 1;
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
        } else if (event.operation === "test_mail") {
          showToast(`${t("testMailCompleted")}: ${event.recipient}`);
        } else if (event.operation === "ppt") {
          showToast(t("pptCompleted"));
        } else if (event.operation === "ppt_upload") {
          showToast(t("pptUploadCompleted"));
        } else {
          showToast(t("scanCompleted"));
        }
        mrcScanRunning = false;
        updateAutomationControls();
        mrcEventSource.close();
      }
      if (event.type === "error") {
        showToast(event.code === "ppt_not_found" ? t("generatePptFirst") : event.message);
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
  const reminderType = document.querySelector('input[name="reminderType"]:checked').value;
  return runMrcAction(
    "/api/agents/mrc-automation/scans",
    { cycle_code: cycleCode, reminder_type: reminderType },
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

function sendMrcTestMail(recipientEmail) {
  const cycleCode = document.querySelector("#targetWeek").textContent;
  return runMrcAction(
    `/api/agents/mrc-automation/cycles/${cycleCode}/test-mail`,
    { recipient_email: recipientEmail },
    t("testMailStarted"),
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

function uploadMrcPpt() {
  const cycleCode = document.querySelector("#targetWeek").textContent;
  return runMrcAction(
    `/api/agents/mrc-automation/cycles/${cycleCode}/ppt/upload`,
    {},
    t("pptUploadStarted"),
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
  const isPdfYaml = id === "pdf-yaml";
  const isI2c = id === "i2c";
  const isToolWorkspace = isMrc || isPdfYaml || isI2c;
  document.querySelector(".chat-workspace").classList.toggle("mrc-mode", isToolWorkspace);
  contentGrid.classList.toggle("is-hidden", isToolWorkspace);
  composerWrap.classList.toggle("is-hidden", isToolWorkspace);
  mrcWorkspace.classList.toggle("is-hidden", !isMrc);
  pdfWorkspace.classList.toggle("is-hidden", !isPdfYaml);
  i2cWorkspace.classList.toggle("is-hidden", !isI2c);
  document.querySelector("#clearButton").classList.toggle("is-hidden", isToolWorkspace);
  document.querySelector("#activityToggle").classList.toggle("is-hidden", isToolWorkspace);
  document.querySelector("#runStrip").classList.add("is-hidden");
  sendButton.disabled = !agent.ready || isRunning || isToolWorkspace;
  input.disabled = !agent.ready || isRunning || isToolWorkspace;
  input.placeholder = t("messagePlaceholder");
  sidebar.classList.remove("is-open");
  if (isMrc) {
    const currentCycle = cycleCodeForDate(new Date());
    setTargetWeek(currentCycle, false);
    loadMrcAutomation();
    loadMrcSnapshot(currentCycle);
  }
  if (isPdfYaml) restorePdfWorkspace();
}

const sharePointAddress = document.querySelector("#sharePointAddress");
const sharePointSavedState = document.querySelector("#sharePointSavedState");
const architecturePdfInput = document.querySelector("#architecturePdfInput");
const selectedPdf = document.querySelector("#selectedPdf");
const pdfPreparation = document.querySelector("#pdfPreparation");
const pdfPreparationStatus = document.querySelector("#pdfPreparationStatus");
const pdfPreparationPercent = document.querySelector("#pdfPreparationPercent");
const pdfPreparationBar = document.querySelector("#pdfPreparationBar");
const referenceFilesInput = document.querySelector("#referenceFilesInput");
const referenceFileList = document.querySelector("#referenceFileList");
const generateYamlButton = document.querySelector("#generateYaml");
const regenerateYamlButton = document.querySelector("#regenerateYaml");
const generationStatus = document.querySelector("#generationStatus");
const generationPercent = document.querySelector("#generationPercent");
const generationProgressBar = document.querySelector("#generationProgressBar");
const generationTimer = document.querySelector("#generationTimer");
const copilotActivityDot = document.querySelector("#copilotActivityDot");
const copilotActivityList = document.querySelector("#copilotActivityList");
const showCopilotHistoryButton = document.querySelector("#showCopilotHistory");
const copilotHistoryDialog = document.querySelector("#copilotHistoryDialog");
const copilotHistoryList = document.querySelector("#copilotHistoryList");
const generationSteps = Array.from(document.querySelectorAll("[data-generation-step]"));
const yamlResult = document.querySelector("#yamlResult");
const yamlPreview = document.querySelector("#yamlPreview");
const i2cForm = document.querySelector("#i2cForm");
const i2cCaptureInput = document.querySelector("#i2cCaptureInput");
const selectedI2cCapture = document.querySelector("#selectedI2cCapture");
const selectedI2cName = document.querySelector("#selectedI2cName");
const selectedI2cMeta = document.querySelector("#selectedI2cMeta");
const i2cDecodeButton = document.querySelector("#i2cDecodeButton");
const i2cResultTitle = document.querySelector("#i2cResultTitle");
const i2cArtifacts = document.querySelector("#i2cArtifacts");
const i2cSummaryBody = document.querySelector("#i2cSummaryBody");
let architecturePdf;
let i2cCapture;
let preparedPdfName = "";
let preparedPdfPages = "";
let preparedPdfUrl = "";
let pdfPreparationRequest;
let referenceFiles = [];
let generatedYaml = "";
let generatedFileName = "architecture.yml";
let generationStartedAt;
let generationTimerId;
let copilotHistory = [];
let copilotHistoryCurrentType;
let copilotHistoryCurrentText;
let copilotHistoryScrollFrame;

const copilotActivityKeys = {
  context_ready: "activityContextReady",
  analyzing: "activityAnalyzing",
  inspecting_inputs: "activityInspectingInputs",
  writing_yaml: "activityWritingYaml",
  response_received: "activityResponseReceived",
  repairing_yaml: "activityRepairingYaml",
};

function resetCopilotActivity() {
  copilotHistory = [];
  copilotHistoryCurrentType = undefined;
  copilotHistoryCurrentText = undefined;
  copilotHistoryList.replaceChildren();
  showCopilotHistoryButton.disabled = true;
  copilotActivityList.replaceChildren();
  const item = document.createElement("li");
  item.dataset.i18n = "copilotWaiting";
  item.textContent = t("copilotWaiting");
  copilotActivityList.append(item);
}

function scheduleCopilotHistoryScroll() {
  if (!copilotHistoryDialog.open || copilotHistoryScrollFrame) return;
  copilotHistoryScrollFrame = window.requestAnimationFrame(() => {
    copilotHistoryList.scrollTop = copilotHistoryList.scrollHeight;
    copilotHistoryScrollFrame = undefined;
  });
}

function createCopilotHistoryItem(type) {
  const elapsed = generationStartedAt === undefined
    ? "00:00"
    : formatElapsed(performance.now() - generationStartedAt);
  const labels = {
    process: t("copilotHistoryProcess"),
    output: t("copilotHistoryOutput"),
    tool: t("copilotHistoryTool"),
  };
  const entry = { elapsed, content: "", type };
  copilotHistory.push(entry);
  const item = document.createElement("li");
  item.className = `is-${type}`;
  const time = document.createElement("time");
  time.textContent = elapsed;
  const body = document.createElement("div");
  const kind = document.createElement("strong");
  kind.textContent = labels[type];
  const text = document.createElement("span");
  body.append(kind, text);
  item.append(time, body);
  copilotHistoryList.append(item);
  showCopilotHistoryButton.disabled = false;
  scheduleCopilotHistoryScroll();
  return { entry, text };
}

function appendCopilotHistoryDelta(content, type) {
  const delta = String(content || "");
  if (!delta) return;
  if (copilotHistoryCurrentType !== type || !copilotHistoryCurrentText) {
    const item = createCopilotHistoryItem(type);
    copilotHistoryCurrentType = type;
    copilotHistoryCurrentText = item;
  }
  copilotHistoryCurrentText.entry.content += delta;
  copilotHistoryCurrentText.text.textContent += delta;
  scheduleCopilotHistoryScroll();
}

function appendCopilotToolActivity(message) {
  const text = String(message || "").trim();
  if (!text) return;
  copilotHistoryCurrentType = undefined;
  copilotHistoryCurrentText = undefined;
  const item = createCopilotHistoryItem("tool");
  item.entry.content = text;
  item.text.textContent = text;
}

function appendCopilotActivity(activity) {
  const key = copilotActivityKeys[activity];
  if (!key) return;
  const message = t(key);
  if (copilotActivityList.lastElementChild?.textContent === message) return;
  if (copilotActivityList.children.length === 1 && copilotActivityList.firstElementChild?.dataset.i18n === "copilotWaiting") {
    copilotActivityList.replaceChildren();
  }
  const item = document.createElement("li");
  item.dataset.i18n = key;
  item.textContent = message;
  copilotActivityList.append(item);
  while (copilotActivityList.children.length > 4) copilotActivityList.firstElementChild.remove();
}

function appendCopilotProcess(message) {
  const text = String(message || "").replace(/\s+/g, " ").trim().slice(0, 180);
  if (!text || copilotActivityList.lastElementChild?.textContent === text) return;
  if (copilotActivityList.children.length === 1 && copilotActivityList.firstElementChild?.dataset.i18n === "copilotWaiting") {
    copilotActivityList.replaceChildren();
  }
  const item = document.createElement("li");
  item.className = "is-process";
  item.textContent = text;
  copilotActivityList.append(item);
  while (copilotActivityList.children.length > 4) copilotActivityList.firstElementChild.remove();
}

showCopilotHistoryButton.addEventListener("click", () => {
  if (!copilotHistory.length) return;
  copilotHistoryDialog.showModal();
  copilotHistoryList.lastElementChild?.scrollIntoView({ block: "end" });
});

document.querySelector("#closeCopilotHistory").addEventListener("click", () => copilotHistoryDialog.close());

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function updateConversionAvailability() {
  generateYamlButton.disabled = !architecturePdf || Boolean(pdfPreparationRequest) || generateYamlButton.classList.contains("is-loading");
}

function formatElapsed(milliseconds) {
  const seconds = Math.max(0, Math.floor(milliseconds / 1000));
  return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

function startGenerationTimer() {
  window.clearInterval(generationTimerId);
  generationStartedAt = performance.now();
  const renderElapsed = () => {
    generationTimer.textContent = formatElapsed(performance.now() - generationStartedAt);
  };
  renderElapsed();
  generationTimerId = window.setInterval(renderElapsed, 1000);
}

function stopGenerationTimer() {
  if (generationStartedAt !== undefined) {
    generationTimer.textContent = formatElapsed(performance.now() - generationStartedAt);
  }
  window.clearInterval(generationTimerId);
  generationTimerId = undefined;
}

function updateGenerationProgress(stage, percent) {
  const statusKeys = {
    starting: "generationStarting",
    filtering: "generationFiltering",
    generating: "generationGenerating",
    validating: "generationValidating",
    repairing: "generationRepairing",
    revalidating: "generationRevalidating",
    completed: "generationCompleted",
    review_required: "generationReviewRequired",
    failed: "generationFailed",
  };
  const activeSteps = { starting: 0, filtering: 0, generating: 1, repairing: 1, validating: 2, revalidating: 2, completed: 3, review_required: 3, failed: -1 };
  const normalized = Math.max(0, Math.min(100, Math.round(percent)));
  const statusKey = statusKeys[stage] || "generationStarting";
  generationStatus.dataset.i18n = statusKey;
  generationStatus.textContent = t(statusKey);
  generationPercent.textContent = `${normalized}%`;
  generationProgressBar.style.width = `${normalized}%`;
  document.querySelector("#generationProgress").classList.toggle("is-error", stage === "failed");
  const activeStep = activeSteps[stage];
  generationSteps.forEach((step, index) => {
    step.classList.toggle("is-active", index === activeStep);
    step.classList.toggle("is-complete", activeStep === 3 || (activeStep >= 0 && index < activeStep));
  });
}

async function readGenerationStream(response) {
  if (!response.ok) {
    const payload = await response.json();
    throw new Error(payload.detail || t("yamlGenerationFailed"));
  }
  if (!response.body) throw new Error(t("yamlGenerationFailed"));
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result;
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (!line.trim()) continue;
      const event = JSON.parse(line);
      if (event.type === "progress") updateGenerationProgress(event.stage, event.percent);
      if (event.type === "activity") appendCopilotActivity(event.activity);
      if (event.type === "process") appendCopilotProcess(event.message);
      if (event.type === "process_delta") appendCopilotHistoryDelta(event.content, "process");
      if (event.type === "output_delta") appendCopilotHistoryDelta(event.content, "output");
      if (event.type === "copilot_activity") appendCopilotToolActivity(event.message);
      if (event.type === "error") throw new Error(event.detail || t("yamlGenerationFailed"));
      if (event.type === "result") result = event;
    }
    if (done) break;
  }
  if (buffer.trim()) {
    const event = JSON.parse(buffer);
    if (event.type === "activity") appendCopilotActivity(event.activity);
    if (event.type === "process") appendCopilotProcess(event.message);
    if (event.type === "process_delta") appendCopilotHistoryDelta(event.content, "process");
    if (event.type === "output_delta") appendCopilotHistoryDelta(event.content, "output");
    if (event.type === "copilot_activity") appendCopilotToolActivity(event.message);
    if (event.type === "error") throw new Error(event.detail || t("yamlGenerationFailed"));
    if (event.type === "result") result = event;
  }
  if (!result) throw new Error(t("yamlGenerationFailed"));
  return result;
}

function updatePdfPreparation(percent, statusKey) {
  const normalized = Math.max(0, Math.min(100, Math.round(percent)));
  pdfPreparation.classList.remove("is-hidden");
  pdfPreparationPercent.textContent = `${normalized}%`;
  pdfPreparationBar.style.width = `${normalized}%`;
  if (statusKey) {
    pdfPreparationStatus.dataset.i18n = statusKey;
    pdfPreparationStatus.textContent = t(statusKey);
  }
}

function decodeResponseHeader(request, name, fallback = "") {
  const value = request.getResponseHeader(name);
  return value ? decodeURIComponent(value) : fallback;
}

function clearPreparedPdfUrl() {
  if (preparedPdfUrl) URL.revokeObjectURL(preparedPdfUrl);
  preparedPdfUrl = "";
  const download = document.querySelector("#downloadPreparedPdf");
  download.href = "#";
  download.removeAttribute("download");
}

function prepareArchitecturePdf(file) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    pdfPreparationRequest = request;
    request.open("POST", "/api/agents/pdf-yaml/prepare");
    request.responseType = "blob";
    request.upload.addEventListener("progress", event => {
      if (event.lengthComputable) updatePdfPreparation((event.loaded / event.total) * 90, "preparingPdf");
    });
    request.upload.addEventListener("load", () => updatePdfPreparation(92, "filteringPdf"));
    request.addEventListener("load", async () => {
      pdfPreparationRequest = undefined;
      if (request.status < 200 || request.status >= 300) {
        let message = t("pdfPreparationFailed");
        try {
          const payload = JSON.parse(await request.response.text());
          message = payload.detail || message;
        } catch {
          // Keep the localized fallback when the server did not return JSON.
        }
        reject(new Error(message));
        return;
      }
      preparedPdfName = decodeResponseHeader(request, "X-Prepared-Name", `${file.name.replace(/\.pdf$/i, "")}_smbus_figures.pdf`);
      preparedPdfPages = request.getResponseHeader("X-Architecture-Pages") || "";
      const product = decodeResponseHeader(request, "X-Architecture-Product");
      architecturePdf = new File([request.response], file.name, { type: "application/pdf" });
      preparedPdfUrl = URL.createObjectURL(architecturePdf);
      const download = document.querySelector("#downloadPreparedPdf");
      download.href = preparedPdfUrl;
      download.download = preparedPdfName;
      document.querySelector("#selectedPdfName").textContent = preparedPdfName;
      document.querySelector("#selectedPdfMeta").textContent = [formatFileSize(architecturePdf.size), product, preparedPdfPages ? `pages ${preparedPdfPages}` : ""].filter(Boolean).join(" · ");
      selectedPdf.classList.remove("is-hidden");
      updatePdfPreparation(100, "pdfPrepared");
      updateConversionAvailability();
      resolve();
    });
    request.addEventListener("error", () => {
      pdfPreparationRequest = undefined;
      reject(new Error(t("pdfPreparationFailed")));
    });
    request.addEventListener("abort", () => {
      pdfPreparationRequest = undefined;
      updateConversionAvailability();
    });
    const form = new FormData();
    form.append("pdf", file, file.name);
    request.send(form);
  });
}

function restorePdfWorkspace() {
  const savedAddress = localStorage.getItem("pdfYamlSharePointAddress") || "";
  if (!sharePointAddress.value) sharePointAddress.value = savedAddress;
  const isSaved = Boolean(savedAddress) && sharePointAddress.value === savedAddress;
  sharePointSavedState.textContent = t(isSaved ? "saved" : "notSaved");
  sharePointSavedState.classList.toggle("is-saved", isSaved);
  updateConversionAvailability();
  loadReferenceFiles();
}

function renderReferenceFiles() {
  if (!referenceFiles.length) {
    referenceFileList.innerHTML = `<div class="reference-empty"><span>REF</span><p><strong>${t("noReferenceFiles")}</strong><small>${t("referenceTypes")}</small></p></div>`;
    return;
  }
  referenceFileList.innerHTML = "";
  referenceFiles.forEach(entry => {
    const row = document.createElement("div");
    row.className = "reference-file";
    const suffix = entry.name.toLowerCase().split(".").pop();
    const type = suffix === "yaml" || suffix === "yml" ? "YML" : suffix.toUpperCase();
    row.innerHTML = `<span class="file-type">${type}</span><a></a><small>${formatFileSize(entry.size)}</small><button class="icon-button" type="button" aria-label="Remove file" title="Remove">×</button>`;
    const link = row.querySelector("a");
    link.textContent = entry.name;
    link.href = `/api/agents/pdf-yaml/references/${encodeURIComponent(entry.name)}`;
    link.download = entry.name;
    row.querySelector("button").addEventListener("click", () => deleteReferenceFile(entry.name));
    referenceFileList.appendChild(row);
  });
}

async function loadReferenceFiles() {
  try {
    const response = await fetch("/api/agents/pdf-yaml/references");
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || t("referenceLoadFailed"));
    referenceFiles = payload.files;
    renderReferenceFiles();
  } catch (error) {
    showToast(error.message || t("referenceLoadFailed"));
  }
}

async function deleteReferenceFile(fileName) {
  try {
    const response = await fetch(`/api/agents/pdf-yaml/references/${encodeURIComponent(fileName)}`, { method: "DELETE" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || t("referenceDeleteFailed"));
    referenceFiles = payload.files;
    renderReferenceFiles();
    showToast(t("referenceDeleted"));
  } catch (error) {
    showToast(error.message || t("referenceDeleteFailed"));
  }
}

document.querySelector("#saveSharePoint").addEventListener("click", () => {
  const address = sharePointAddress.value.trim();
  try {
    const url = new URL(address);
    if (url.protocol !== "https:" && url.protocol !== "http:") throw new Error();
  } catch {
    showToast(t("enterValidAddress"));
    sharePointAddress.focus();
    return;
  }
  localStorage.setItem("pdfYamlSharePointAddress", address);
  sharePointSavedState.textContent = t("saved");
  sharePointSavedState.classList.add("is-saved");
  updateConversionAvailability();
  showToast(t("addressSaved"));
});

sharePointAddress.addEventListener("input", () => {
  const savedAddress = localStorage.getItem("pdfYamlSharePointAddress") || "";
  const isSaved = sharePointAddress.value.trim() === savedAddress && Boolean(savedAddress);
  sharePointSavedState.textContent = t(isSaved ? "saved" : "notSaved");
  sharePointSavedState.classList.toggle("is-saved", isSaved);
  updateConversionAvailability();
});

architecturePdfInput.addEventListener("change", async () => {
  const file = architecturePdfInput.files[0];
  if (!file) return;
  if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
    architecturePdfInput.value = "";
    showToast(t("invalidPdf"));
    return;
  }
  if (pdfPreparationRequest) pdfPreparationRequest.abort();
  clearPreparedPdfUrl();
  architecturePdf = undefined;
  preparedPdfName = "";
  preparedPdfPages = "";
  selectedPdf.classList.add("is-hidden");
  updatePdfPreparation(0, "preparingPdf");
  updateConversionAvailability();
  try {
    await prepareArchitecturePdf(file);
    showToast(t("pdfPrepared"));
  } catch (error) {
    architecturePdf = undefined;
    updatePdfPreparation(0, "pdfPreparationFailed");
    showToast(error.message || t("pdfPreparationFailed"));
  } finally {
    architecturePdfInput.value = "";
    updateConversionAvailability();
  }
});

document.querySelector("#removePdf").addEventListener("click", () => {
  if (pdfPreparationRequest) pdfPreparationRequest.abort();
  clearPreparedPdfUrl();
  architecturePdf = undefined;
  preparedPdfName = "";
  preparedPdfPages = "";
  architecturePdfInput.value = "";
  selectedPdf.classList.add("is-hidden");
  pdfPreparation.classList.add("is-hidden");
  updateConversionAvailability();
});

document.querySelector("#downloadPreparedPdf").addEventListener("click", event => {
  if (!architecturePdf) {
    event.preventDefault();
    return;
  }
  showToast(t("preparedPdfDownloaded"));
});

referenceFilesInput.addEventListener("change", async () => {
  let rejected = false;
  const acceptedFiles = Array.from(referenceFilesInput.files).filter(file => {
    const name = file.name.toLowerCase();
    if (![".md", ".pdf", ".txt", ".yaml", ".yml"].some(suffix => name.endsWith(suffix))) {
      rejected = true;
      return false;
    }
    return true;
  });
  referenceFilesInput.value = "";
  if (!acceptedFiles.length) {
    if (rejected) showToast(t("invalidReference"));
    return;
  }
  const form = new FormData();
  acceptedFiles.forEach(file => form.append("files", file, file.name));
  try {
    const response = await fetch("/api/agents/pdf-yaml/references", { method: "POST", body: form });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || t("referenceUploadFailed"));
    referenceFiles = payload.files;
    renderReferenceFiles();
    showToast(t(rejected ? "invalidReference" : "referenceAdded"));
  } catch (error) {
    showToast(error.message || t("referenceUploadFailed"));
  }
});

function outputFileName() {
  return generatedFileName;
}

function highlightYaml(value) {
  const escapeHtml = (text) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  return value.split("\n").map((line) => {
    const escaped = escapeHtml(line);
    const parts = escaped.match(/^(\s*)(-\s+)?([^:#]+:)(.*)$/);
    if (!parts) return escaped;
    const content = parts[4]
      .replace(/(&quot;.*?&quot;)/g, '<span class="yaml-string">$1</span>')
      .replace(/\b(true|false|null)\b/g, '<span class="yaml-literal">$1</span>')
      .replace(/\b(\d+)\b/g, '<span class="yaml-number">$1</span>');
    return `${parts[1]}${parts[2] || ""}<span class="yaml-key">${parts[3]}</span>${content}`;
  }).join("\n");
}

function renderGeneratedYaml(payload) {
  generatedYaml = payload.yaml;
  generatedFileName = payload.file_name;
  document.querySelector("#yamlFileName").textContent = generatedFileName;
  document.querySelector("#yamlSourceDocument").textContent = payload.source_file;
  const sourcePages = document.querySelector("#yamlSourcePages");
  if (sourcePages && preparedPdfPages) sourcePages.textContent = preparedPdfPages;
  document.querySelector("#yamlGeneratedAt").textContent = new Date().toLocaleString(currentLanguage === "zh" ? "zh-CN" : "en-US");
  document.querySelector("#yamlLineCount").textContent = `${generatedYaml.trimEnd().split("\n").length} lines`;
  yamlPreview.innerHTML = highlightYaml(generatedYaml);
  yamlResult.classList.remove("is-hidden");
  yamlResult.scrollIntoView({ behavior: "smooth", block: "start" });
  const reviewRequired = Boolean(payload.validation?.review_required);
  if (reviewRequired) updateGenerationProgress("review_required", 100);
  showToast(t(reviewRequired ? "yamlReviewRequired" : "yamlGenerated"));
}

async function generateYaml() {
  if (!architecturePdf) {
    showToast(t("invalidPdf"));
    return;
  }
  const form = new FormData();
  form.append("pdf", architecturePdf, architecturePdf.name);
  generateYamlButton.classList.add("is-loading");
  generateYamlButton.querySelector("span").textContent = t("generatingYaml");
  regenerateYamlButton.disabled = true;
  updateGenerationProgress("starting", 0);
  resetCopilotActivity();
  copilotActivityDot.classList.add("is-running");
  startGenerationTimer();
  updateConversionAvailability();
  try {
    const response = await fetch("/api/agents/pdf-yaml/generate-stream", { method: "POST", body: form });
    const payload = await readGenerationStream(response);
    renderGeneratedYaml(payload);
  } catch (error) {
    updateGenerationProgress("failed", Number.parseInt(generationPercent.textContent, 10) || 0);
    showToast(error.message || t("yamlGenerationFailed"));
  } finally {
    stopGenerationTimer();
    copilotActivityDot.classList.remove("is-running");
    generateYamlButton.classList.remove("is-loading");
    generateYamlButton.querySelector("span").textContent = t("generateYaml");
    regenerateYamlButton.disabled = false;
    updateConversionAvailability();
  }
}

async function copyGeneratedYaml() {
  try {
    await navigator.clipboard.writeText(generatedYaml);
    showToast(t("yamlCopied"));
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(yamlPreview);
    selection.removeAllRanges();
    selection.addRange(range);
  }
}

function downloadGeneratedYaml() {
  const url = URL.createObjectURL(new Blob([generatedYaml], { type: "application/yaml;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = outputFileName();
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  showToast(t("yamlDownloaded"));
}

generateYamlButton.addEventListener("click", generateYaml);
regenerateYamlButton.addEventListener("click", generateYaml);
document.querySelector("#copyYaml").addEventListener("click", copyGeneratedYaml);
document.querySelector("#downloadYaml").addEventListener("click", downloadGeneratedYaml);

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
document.querySelectorAll('input[name="reminderType"]').forEach(input => {
  input.addEventListener("change", () => {
    if (!input.checked) {
      input.checked = true;
      return;
    }
    document.querySelectorAll('input[name="reminderType"]').forEach(other => {
      if (other !== input) other.checked = false;
    });
  });
});
document.querySelector("#sendMail").addEventListener("click", () => {
  const cycleCode = document.querySelector("#targetWeek").textContent;
  const scopeKey = document.querySelector("#sendAll").checked
    ? "confirmMailScopeAll"
    : "confirmMailScopeMissing";
  document.querySelector("#sendMailConfirmation").textContent = t(scopeKey).replace("{cycle}", cycleCode);
  document.querySelector("#sendMailDialog").showModal();
});
document.querySelector("#sendTestMail").addEventListener("click", () => {
  const dialog = document.querySelector("#testMailDialog");
  const recipient = document.querySelector("#testMailRecipient");
  recipient.value = "";
  dialog.showModal();
  recipient.focus();
});
document.querySelector("#generatePpt").addEventListener("click", generateMrcPpt);
document.querySelector("#uploadPpt").addEventListener("click", uploadMrcPpt);
document.querySelectorAll("[data-draft-filter]").forEach(button => {
  button.addEventListener("click", () => {
    draftFilter = button.dataset.draftFilter;
    currentDraftPage = 1;
    document.querySelectorAll("[data-draft-filter]").forEach(item => item.classList.toggle("is-active", item === button));
    renderDraftQueue();
  });
});
document.querySelector("#previousDraftPage").addEventListener("click", () => {
  currentDraftPage -= 1;
  renderDraftQueue();
});
document.querySelector("#nextDraftPage").addEventListener("click", () => {
  currentDraftPage += 1;
  renderDraftQueue();
});
document.querySelector("#openTemplate").addEventListener("click", () => {
  document.querySelector("#emailDialogBody").innerHTML = document.querySelector(".email-canvas").outerHTML;
  document.querySelector("#emailDialog").showModal();
});
document.querySelector("#closeEmailDialog").addEventListener("click", () => document.querySelector("#emailDialog").close());
document.querySelector("#closeSendMailDialog").addEventListener("click", () => document.querySelector("#sendMailDialog").close());
document.querySelector("#cancelSendMail").addEventListener("click", () => document.querySelector("#sendMailDialog").close());
document.querySelector("#sendMailForm").addEventListener("submit", event => {
  event.preventDefault();
  document.querySelector("#sendMailDialog").close();
  sendMrcMail();
});
document.querySelector("#closeTestMailDialog").addEventListener("click", () => document.querySelector("#testMailDialog").close());
document.querySelector("#cancelTestMail").addEventListener("click", () => document.querySelector("#testMailDialog").close());
document.querySelector("#testMailForm").addEventListener("submit", event => {
  event.preventDefault();
  const recipient = document.querySelector("#testMailRecipient");
  if (!recipient.reportValidity()) return;
  document.querySelector("#testMailDialog").close();
  sendMrcTestMail(recipient.value.trim());
});

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
  document.querySelector("#agentDescription").textContent = t(agents[selectedAgent].descriptionKey);
  updateAutomationControls();
  if (selectedAgent === "pdf-yaml") {
    restorePdfWorkspace();
    renderReferenceFiles();
  }
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

function ensureProcessView() {
  if (assistantBody) return;
  assistantBody = appendMessage("assistant", "");
  assistantBody.classList.add("streaming-answer");
  processDetails = document.createElement("details");
  processDetails.className = "process-details";
  processDetails.open = true;
  const summary = document.createElement("summary");
  summary.textContent = t("workingDetails");
  processContent = document.createElement("div");
  processContent.className = "process-content";
  processDetails.append(summary, processContent);
  assistantBody.append(processDetails);
}

function completedProcessLabel() {
  const elapsedSeconds = Math.max(0, (Date.now() - runStartedAt) / 1000);
  const duration = elapsedSeconds < 10
    ? `${elapsedSeconds.toFixed(1)}s`
    : `${Math.round(elapsedSeconds)}s`;
  return t("completedSteps")
    .replace("{steps}", String(activitySequence))
    .replace("{duration}", duration);
}

function beginFinalAnswer() {
  if (finalAnswer) return;
  if (!assistantBody) assistantBody = appendMessage("assistant", "");
  if (processDetails) {
    assistantBody.classList.remove("streaming-answer");
    processDetails.open = false;
    processDetails.querySelector("summary").textContent = completedProcessLabel();
  }
  finalAnswer = document.createElement("div");
  finalAnswer.className = "final-answer";
  assistantBody.append(finalAnswer);
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
    case "process_delta":
      ensureProcessView();
      processContent.textContent += event.content || "";
      conversation.scrollTo({ top: conversation.scrollHeight, behavior: "smooth" });
      break;
    case "answer_delta":
      beginFinalAnswer();
      finalAnswer.textContent += event.content || "";
      conversation.scrollTo({ top: conversation.scrollHeight, behavior: "smooth" });
      break;
    case "completed":
      addActivity(t("generateAnalysis"), t("completed"));
      if (!assistantBody) {
        assistantBody = appendMessage("assistant", event.answer || t("taskDoneFallback"));
      } else {
        beginFinalAnswer();
        finalAnswer.textContent = event.answer || t("taskDoneFallback");
      }
      finishRun("completed", t("finalResult"));
      assistantBody = undefined;
      processDetails = undefined;
      processContent = undefined;
      finalAnswer = undefined;
      break;
    case "error":
      appendMessage("assistant", event.message || t("agentFailed"));
      addActivity(t("executionFailed"), event.message || "Unknown error");
      finishRun("error", t("checkServerLog"));
      assistantBody = undefined;
      processDetails = undefined;
      processContent = undefined;
      finalAnswer = undefined;
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
  processDetails = undefined;
  processContent = undefined;
  finalAnswer = undefined;
  runStartedAt = Date.now();
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

function updateI2cControls() {
  i2cDecodeButton.disabled = !i2cCapture || i2cDecodeRunning;
  i2cDecodeButton.classList.toggle("is-loading", i2cDecodeRunning);
  i2cDecodeButton.querySelector("span").textContent = i2cDecodeRunning ? t("i2cDecoding") : t("decodeI2c");
}

function formatFrequency(value) {
  if (!value) return "—";
  if (value >= 1000) return `${(value / 1000).toFixed(1)} kHz`;
  return `${value.toFixed(1)} Hz`;
}

function renderI2cArtifacts(artifacts) {
  i2cArtifacts.replaceChildren();
  if (!artifacts?.length) {
    const empty = document.createElement("span");
    empty.className = "artifact-empty";
    empty.textContent = t("noI2cArtifacts");
    i2cArtifacts.append(empty);
    return;
  }
  artifacts.forEach(artifact => {
    const link = document.createElement("a");
    link.className = "artifact-link";
    link.href = artifact.download_url;
    link.download = artifact.file_name;
    link.textContent = artifact.file_name;
    i2cArtifacts.append(link);
  });
}

function renderI2cRows(rows) {
  i2cSummaryBody.replaceChildren();
  if (!rows?.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 5;
    cell.textContent = t("noDecodedTransactions");
    row.append(cell);
    i2cSummaryBody.append(row);
    return;
  }
  rows.forEach(item => {
    const row = document.createElement("tr");
    ["Txn", "Address", "Register", "Data", "Status"].forEach(key => {
      const cell = document.createElement("td");
      cell.textContent = item[key] || "";
      row.append(cell);
    });
    i2cSummaryBody.append(row);
  });
}

function renderI2cResult(payload) {
  const summary = payload.summary || {};
  i2cResultTitle.textContent = summary.source_file || t("i2cDecodeCompleted");
  document.querySelector("#i2cTxnCount").textContent = summary.transactions ?? "—";
  document.querySelector("#i2cCompleteCount").textContent = summary.complete ?? "—";
  document.querySelector("#i2cAddresses").textContent = summary.addresses?.length ? summary.addresses.join(", ") : "—";
  document.querySelector("#i2cSclFrequency").textContent = formatFrequency(summary.estimated_scl_frequency_hz);
  renderI2cArtifacts(payload.artifacts);
  renderI2cRows(payload.rows);
}

async function submitI2cDecode() {
  if (!i2cCapture || i2cDecodeRunning) return;
  i2cDecodeRunning = true;
  updateI2cControls();
  i2cResultTitle.textContent = t("i2cDecoding");
  const formData = new FormData();
  formData.append("capture", i2cCapture);
  ["time_col", "scl_col", "sda_col", "scl_threshold", "sda_threshold", "hysteresis_fraction"].forEach(name => {
    const value = i2cForm.elements[name]?.value?.trim();
    if (value) formData.append(name, value);
  });
  try {
    const response = await fetch("/api/agents/i2c-automation/decodes", { method: "POST", body: formData });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || t("requestFailed"));
    showToast(t("i2cDecodeStarted"));
    i2cEventSource = new EventSource(`/api/runs/${payload.run_id}/events`);
    i2cEventSource.onmessage = message => {
      const event = JSON.parse(message.data);
      if (event.type === "progress") i2cResultTitle.textContent = event.message;
      if (event.type === "completed") {
        renderI2cResult(event);
        showToast(t("i2cDecodeCompleted"));
        i2cDecodeRunning = false;
        updateI2cControls();
        i2cEventSource.close();
      }
      if (event.type === "error") {
        showToast(event.message || t("i2cDecodeFailed"));
        i2cResultTitle.textContent = t("i2cDecodeFailed");
        i2cDecodeRunning = false;
        updateI2cControls();
        i2cEventSource.close();
      }
    };
    i2cEventSource.onerror = () => {
      if (!i2cDecodeRunning) return;
      showToast(t("connectionInterrupted"));
      i2cDecodeRunning = false;
      updateI2cControls();
      i2cEventSource.close();
    };
  } catch (error) {
    showToast(error.message || t("cannotConnect"));
    i2cResultTitle.textContent = t("i2cDecodeFailed");
    i2cDecodeRunning = false;
    updateI2cControls();
  }
}

i2cCaptureInput.addEventListener("change", () => {
  const file = i2cCaptureInput.files?.[0];
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".csv")) {
    showToast(t("i2cInvalidCsv"));
    i2cCaptureInput.value = "";
    return;
  }
  i2cCapture = file;
  selectedI2cCapture.classList.remove("is-hidden");
  selectedI2cName.textContent = file.name;
  selectedI2cMeta.textContent = `${(file.size / 1024).toFixed(1)} KB`;
  showToast(t("i2cCsvSelected"));
  updateI2cControls();
});
document.querySelector("#removeI2cCapture").addEventListener("click", () => {
  i2cCapture = undefined;
  i2cCaptureInput.value = "";
  selectedI2cCapture.classList.add("is-hidden");
  updateI2cControls();
});
i2cForm.addEventListener("submit", event => { event.preventDefault(); submitI2cDecode(); });
applyTranslations();
