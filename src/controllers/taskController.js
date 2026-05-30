const Task = require('../models/Task');
const User = require('../models/User');
const { createAuditLog } = require('../utils/auditLogger');

// @desc    Create a new task (Manager only)
// @route   POST /api/tasks
// @access  Private/Manager
const createTask = async (req, res, next) => {
  try {
    const { title, description, assignedTo, priority, deadline } = req.body;

    // Verify assignee exists and is an employee
    const employee = await User.findById(assignedTo);
    if (!employee) {
      return res.status(404).json({ success: false, message: 'Assigned employee not found.' });
    }
    if (employee.role !== 'employee') {
      return res.status(400).json({ success: false, message: 'Tasks can only be assigned to employees.' });
    }

    const task = await Task.create({
      title,
      description,
      assignedTo,
      assignedBy: req.user._id,
      priority,
      deadline,
    });

    await task.populate([
      { path: 'assignedTo', select: 'name email' },
      { path: 'assignedBy', select: 'name email' },
    ]);

    await createAuditLog({
      userId: req.user._id,
      action: 'task_created',
      entityType: 'task',
      entityId: task._id,
      metadata: { title, assignedTo, priority, deadline },
    });

    res.status(201).json({ success: true, message: 'Task created successfully.', data: { task } });
  } catch (error) {
    next(error);
  }
};

// @desc    Get all tasks (Manager) or assigned tasks (Employee)
// @route   GET /api/tasks
// @access  Private
const getTasks = async (req, res, next) => {
  try {
    const { status, priority, assignedTo, page = 1, limit = 20 } = req.query;
    const query = {};

    // Employees only see their own tasks
    if (req.user.role === 'employee') {
      query.assignedTo = req.user._id;
    } else {
      if (assignedTo) query.assignedTo = assignedTo;
    }

    if (status) query.status = status;
    if (priority) query.priority = priority;

    const skip = (parseInt(page) - 1) * parseInt(limit);
    const [tasks, total] = await Promise.all([
      Task.find(query)
        .populate('assignedTo', 'name email')
        .populate('assignedBy', 'name email')
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(parseInt(limit)),
      Task.countDocuments(query),
    ]);

    res.status(200).json({
      success: true,
      data: {
        tasks,
        pagination: { total, page: parseInt(page), limit: parseInt(limit), pages: Math.ceil(total / limit) },
      },
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get a single task by ID
// @route   GET /api/tasks/:id
// @access  Private
const getTask = async (req, res, next) => {
  try {
    const task = await Task.findById(req.params.id)
      .populate('assignedTo', 'name email')
      .populate('assignedBy', 'name email');

    if (!task) {
      return res.status(404).json({ success: false, message: 'Task not found.' });
    }

    // Employees can only view their own tasks
    if (req.user.role === 'employee' && task.assignedTo._id.toString() !== req.user._id.toString()) {
      return res.status(403).json({ success: false, message: 'Access denied.' });
    }

    res.status(200).json({ success: true, data: { task } });
  } catch (error) {
    next(error);
  }
};

// @desc    Update a task
// @route   PUT /api/tasks/:id
// @access  Private (Manager: all fields; Employee: status only)
const updateTask = async (req, res, next) => {
  try {
    const task = await Task.findById(req.params.id);
    if (!task) {
      return res.status(404).json({ success: false, message: 'Task not found.' });
    }

    const prevStatus = task.status;

    if (req.user.role === 'employee') {
      // Employees can only update status of their own tasks
      if (task.assignedTo.toString() !== req.user._id.toString()) {
        return res.status(403).json({ success: false, message: 'Access denied.' });
      }
      const { status } = req.body;
      if (!status) {
        return res.status(400).json({ success: false, message: 'Employees can only update task status.' });
      }
      task.status = status;
      if (status === 'completed') task.completedAt = new Date();
    } else {
      // Manager can update any field
      const { title, description, assignedTo, priority, deadline, status } = req.body;
      if (title !== undefined) task.title = title;
      if (description !== undefined) task.description = description;
      if (assignedTo !== undefined) task.assignedTo = assignedTo;
      if (priority !== undefined) task.priority = priority;
      if (deadline !== undefined) task.deadline = deadline;
      if (status !== undefined) {
        task.status = status;
        if (status === 'completed') task.completedAt = new Date();
      }
    }

    await task.save();
    await task.populate([
      { path: 'assignedTo', select: 'name email' },
      { path: 'assignedBy', select: 'name email' },
    ]);

    const action = prevStatus !== task.status ? 'status_changed' : 'task_updated';
    await createAuditLog({
      userId: req.user._id,
      action,
      entityType: 'task',
      entityId: task._id,
      metadata: { prevStatus, newStatus: task.status, changes: req.body },
    });

    res.status(200).json({ success: true, message: 'Task updated successfully.', data: { task } });
  } catch (error) {
    next(error);
  }
};

// @desc    Delete a task (Manager only)
// @route   DELETE /api/tasks/:id
// @access  Private/Manager
const deleteTask = async (req, res, next) => {
  try {
    const task = await Task.findById(req.params.id);
    if (!task) {
      return res.status(404).json({ success: false, message: 'Task not found.' });
    }

    await createAuditLog({
      userId: req.user._id,
      action: 'task_deleted',
      entityType: 'task',
      entityId: task._id,
      metadata: { title: task.title, assignedTo: task.assignedTo },
    });

    await task.deleteOne();

    res.status(200).json({ success: true, message: 'Task deleted successfully.' });
  } catch (error) {
    next(error);
  }
};

// @desc    Get tasks assigned to the logged-in employee
// @route   GET /api/tasks/my-tasks
// @access  Private/Employee
const getMyTasks = async (req, res, next) => {
  try {
    const { status } = req.query;
    const query = { assignedTo: req.user._id };
    if (status) query.status = status;

    const tasks = await Task.find(query)
      .populate('assignedBy', 'name email')
      .sort({ deadline: 1 });

    res.status(200).json({ success: true, data: { tasks, total: tasks.length } });
  } catch (error) {
    next(error);
  }
};

module.exports = { createTask, getTasks, getTask, updateTask, deleteTask, getMyTasks };
