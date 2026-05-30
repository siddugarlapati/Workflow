const express = require('express');
const { managerDashboard, employeeDashboard } = require('../controllers/dashboardController');
const { getAuditLogs } = require('../controllers/auditController');
const { protect, authorize } = require('../middleware/auth');

const dashboardRouter = express.Router();
const auditRouter = express.Router();

// Dashboard routes
dashboardRouter.use(protect);
dashboardRouter.get('/manager', authorize('manager'), managerDashboard);
dashboardRouter.get('/employee', authorize('employee'), employeeDashboard);

// Audit routes
auditRouter.use(protect);
auditRouter.get('/', getAuditLogs);

module.exports = { dashboardRouter, auditRouter };
