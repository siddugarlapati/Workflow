const WorkLog = require('../models/WorkLog');
const Task = require('../models/Task');
const { createAuditLog } = require('../utils/auditLogger');
const { verifyWorkLog } = require('../utils/aiService');

// @desc    Submit a work log for a task
// @route   POST /api/logs
// @access  Private/Employee
const submitLog = async (req, res, next) => {
  try {
    const { taskId, logText } = req.body;

    const task = await Task.findById(taskId);
    if (!task) {
      return res.status(404).json({ success: false, message: 'Task not found.' });
    }

    if (
      req.user.role === 'employee' &&
      task.assignedTo.toString() !== req.user._id.toString()
    ) {
      return res.status(403).json({
        success: false,
        message: 'You can only log work for tasks assigned to you.',
      });
    }

    const { aiScore, aiFeedback, verificationStatus } = await verifyWorkLog(
      task.title,
      task.description,
      logText
    );

    const workLog = await WorkLog.create({
      taskId,
      employeeId: req.user._id,
      logText,
      aiScore,
      aiFeedback,
      verificationStatus,
      aiVerifiedAt: aiScore !== null ? new Date() : null,
    });

    await workLog.populate([
      { path: 'taskId', select: 'title status priority' },
      { path: 'employeeId', select: 'name email' },
    ]);

    await createAuditLog({
      userId: req.user._id,
      action: 'worklog_submitted',
      entityType: 'worklog',
      entityId: workLog._id,
      metadata: { taskId, aiScore, verificationStatus },
    });

    res.status(201).json({
      success: true,
      message: 'Work log submitted successfully.',
      data: { workLog },
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get all logs for a specific task
// @route   GET /api/logs/task/:taskId
// @access  Private (Manager: any task; Employee: own tasks only)
const getLogsByTask = async (req, res, next) => {
  try {
    const { taskId } = req.params;

    const task = await Task.findById(taskId);
    if (!task) {
      return res.status(404).json({ success: false, message: 'Task not found.' });
    }

    if (
      req.user.role === 'employee' &&
      task.assignedTo.toString() !== req.user._id.toString()
    ) {
      return res.status(403).json({ success: false, message: 'Access denied.' });
    }

    const logs = await WorkLog.find({ taskId })
      .populate('employeeId', 'name email')
      .sort({ submittedAt: -1 });

    res.status(200).json({ success: true, data: { logs, total: logs.length } });
  } catch (error) {
    next(error);
  }
};

// @desc    Get all work logs (Manager only, can filter by employee)
// @route   GET /api/logs
// @access  Private/Manager
const getAllLogs = async (req, res, next) => {
  try {
    const { employeeId, verificationStatus, page = 1, limit = 20 } = req.query;
    const query = {};

    if (employeeId) query.employeeId = employeeId;
    if (verificationStatus) query.verificationStatus = verificationStatus;

    const parsedPage = parseInt(page, 10);
    const parsedLimit = parseInt(limit, 10);
    const skip = (parsedPage - 1) * parsedLimit;
    const [logs, total] = await Promise.all([
      WorkLog.find(query)
        .populate('taskId', 'title status priority deadline')
        .populate('employeeId', 'name email')
        .sort({ submittedAt: -1 })
        .skip(skip)
        .limit(parsedLimit),
      WorkLog.countDocuments(query),
    ]);

    res.status(200).json({
      success: true,
      data: {
        logs,
        pagination: { total, page: parsedPage, limit: parsedLimit, pages: Math.ceil(total / parsedLimit) },
      },
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get logged-in employee's own logs
// @route   GET /api/logs/my-logs
// @access  Private/Employee
const getMyLogs = async (req, res, next) => {
  try {
    const logs = await WorkLog.find({ employeeId: req.user._id })
      .populate('taskId', 'title status priority')
      .sort({ submittedAt: -1 });

    res.status(200).json({ success: true, data: { logs, total: logs.length } });
  } catch (error) {
    next(error);
  }
};

module.exports = { submitLog, getLogsByTask, getAllLogs, getMyLogs };
