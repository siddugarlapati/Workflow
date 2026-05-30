const express = require('express');
const { body, param } = require('express-validator');
const { submitLog, getLogsByTask, getAllLogs, getMyLogs } = require('../controllers/logController');
const { protect, authorize } = require('../middleware/auth');
const validate = require('../middleware/validate');

const router = express.Router();

router.use(protect);

// Employee: submit a work log
router.post(
  '/',
  [
    body('taskId').isMongoId().withMessage('Valid task ID is required'),
    body('logText')
      .trim()
      .notEmpty()
      .withMessage('Log text is required')
      .isLength({ min: 10 })
      .withMessage('Log must be at least 10 characters')
      .isLength({ max: 3000 })
      .withMessage('Log cannot exceed 3000 characters'),
  ],
  validate,
  submitLog
);

// Employee: view own logs
router.get('/my-logs', getMyLogs);

// Manager: view all logs
router.get('/', authorize('manager'), getAllLogs);

// Both: view logs for a specific task
router.get(
  '/task/:taskId',
  [param('taskId').isMongoId().withMessage('Invalid task ID')],
  validate,
  getLogsByTask
);

module.exports = router;
