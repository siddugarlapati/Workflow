const AuditLog = require('../models/AuditLog');

// @desc    Get audit logs (Manager sees all; Employee sees own)
// @route   GET /api/audit
// @access  Private
const getAuditLogs = async (req, res, next) => {
  try {
    const { action, entityType, page = 1, limit = 50 } = req.query;
    const query = {};

    // Employees only see their own audit trail
    if (req.user.role === 'employee') {
      query.userId = req.user._id;
    }

    if (action) query.action = action;
    if (entityType) query.entityType = entityType;

    const skip = (parseInt(page) - 1) * parseInt(limit);
    const [logs, total] = await Promise.all([
      AuditLog.find(query)
        .populate('userId', 'name email role')
        .sort({ timestamp: -1 })
        .skip(skip)
        .limit(parseInt(limit)),
      AuditLog.countDocuments(query),
    ]);

    res.status(200).json({
      success: true,
      data: {
        logs,
        pagination: {
          total,
          page: parseInt(page),
          limit: parseInt(limit),
          pages: Math.ceil(total / limit),
        },
      },
    });
  } catch (error) {
    next(error);
  }
};

module.exports = { getAuditLogs };
