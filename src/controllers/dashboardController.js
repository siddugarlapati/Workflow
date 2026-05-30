const Task = require('../models/Task');
const User = require('../models/User');
const WorkLog = require('../models/WorkLog');
const { generateManagerSummary } = require('../utils/aiService');

// @desc    Manager dashboard statistics
// @route   GET /api/dashboard/manager
// @access  Private/Manager
const managerDashboard = async (req, res, next) => {
  try {
    const now = new Date();

    // Aggregate task statistics
    const [
      totalTasks,
      pendingTasks,
      inProgressTasks,
      completedTasks,
      overdueTasks,
      tasksByEmployee,
      recentLogs,
      allTasks,
      employees,
    ] = await Promise.all([
      Task.countDocuments(),
      Task.countDocuments({ status: 'pending' }),
      Task.countDocuments({ status: 'in_progress' }),
      Task.countDocuments({ status: 'completed' }),
      Task.countDocuments({ status: { $ne: 'completed' }, deadline: { $lt: now } }),
      // Group tasks by employee
      Task.aggregate([
        {
          $group: {
            _id: '$assignedTo',
            total: { $sum: 1 },
            pending: { $sum: { $cond: [{ $eq: ['$status', 'pending'] }, 1, 0] } },
            in_progress: { $sum: { $cond: [{ $eq: ['$status', 'in_progress'] }, 1, 0] } },
            completed: { $sum: { $cond: [{ $eq: ['$status', 'completed'] }, 1, 0] } },
            overdue: {
              $sum: {
                $cond: [
                  {
                    $and: [
                      { $ne: ['$status', 'completed'] },
                      { $lt: ['$deadline', now] },
                    ],
                  },
                  1,
                  0,
                ],
              },
            },
          },
        },
        {
          $lookup: {
            from: 'users',
            localField: '_id',
            foreignField: '_id',
            as: 'employee',
          },
        },
        { $unwind: '$employee' },
        {
          $project: {
            employee: { name: 1, email: 1 },
            total: 1,
            pending: 1,
            in_progress: 1,
            completed: 1,
            overdue: 1,
          },
        },
      ]),
      // Recent work logs (last 5)
      WorkLog.find()
        .populate('employeeId', 'name')
        .populate('taskId', 'title')
        .sort({ submittedAt: -1 })
        .limit(5),
      // For AI summary
      Task.find({ status: { $ne: 'completed' } })
        .populate('assignedTo', 'name')
        .limit(30),
      User.find({ role: 'employee' }).select('name email'),
    ]);

    // Generate AI summary (non-blocking)
    const aiSummary = await generateManagerSummary(allTasks, employees);

    res.status(200).json({
      success: true,
      data: {
        stats: {
          totalTasks,
          pendingTasks,
          inProgressTasks,
          completedTasks,
          overdueTasks,
          totalEmployees: employees.length,
        },
        tasksByEmployee,
        recentLogs,
        aiSummary,
      },
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Employee dashboard
// @route   GET /api/dashboard/employee
// @access  Private/Employee
const employeeDashboard = async (req, res, next) => {
  try {
    const now = new Date();
    const employeeId = req.user._id;

    const [
      totalTasks,
      pendingTasks,
      inProgressTasks,
      completedTasks,
      overdueTasks,
      upcomingTasks,
      recentLogs,
    ] = await Promise.all([
      Task.countDocuments({ assignedTo: employeeId }),
      Task.countDocuments({ assignedTo: employeeId, status: 'pending' }),
      Task.countDocuments({ assignedTo: employeeId, status: 'in_progress' }),
      Task.countDocuments({ assignedTo: employeeId, status: 'completed' }),
      Task.countDocuments({
        assignedTo: employeeId,
        status: { $ne: 'completed' },
        deadline: { $lt: now },
      }),
      // Next 5 upcoming tasks by deadline
      Task.find({
        assignedTo: employeeId,
        status: { $ne: 'completed' },
        deadline: { $gte: now },
      })
        .sort({ deadline: 1 })
        .limit(5)
        .populate('assignedBy', 'name'),
      // Recent own logs
      WorkLog.find({ employeeId })
        .populate('taskId', 'title')
        .sort({ submittedAt: -1 })
        .limit(5),
    ]);

    res.status(200).json({
      success: true,
      data: {
        stats: {
          totalTasks,
          pendingTasks,
          inProgressTasks,
          completedTasks,
          overdueTasks,
        },
        upcomingTasks,
        recentLogs,
      },
    });
  } catch (error) {
    next(error);
  }
};

module.exports = { managerDashboard, employeeDashboard };
