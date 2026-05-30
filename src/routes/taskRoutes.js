const express = require('express');
const { body, param } = require('express-validator');
const {
  createTask,
  getTasks,
  getTask,
  updateTask,
  deleteTask,
  getMyTasks,
} = require('../controllers/taskController');
const { protect, authorize } = require('../middleware/auth');
const validate = require('../middleware/validate');

const router = express.Router();

router.use(protect);

// Must be before /:id.
router.get('/my-tasks', getMyTasks);

router.post(
  '/',
  authorize('manager'),
  [
    body('title')
      .trim()
      .notEmpty()
      .withMessage('Title is required')
      .isLength({ min: 3 })
      .withMessage('Title must be at least 3 characters'),
    body('assignedTo').isMongoId().withMessage('Valid employee ID is required'),
    body('priority').optional().isIn(['low', 'medium', 'high']).withMessage('Priority must be low, medium, or high'),
    body('deadline').isISO8601().withMessage('Valid deadline date is required').toDate(),
    body('description').optional().isLength({ max: 2000 }).withMessage('Description cannot exceed 2000 characters'),
  ],
  validate,
  createTask
);

router.get('/', getTasks);

router.get(
  '/:id',
  [param('id').isMongoId().withMessage('Invalid task ID')],
  validate,
  getTask
);

router.put(
  '/:id',
  [
    param('id').isMongoId().withMessage('Invalid task ID'),
    body('status').optional().isIn(['pending', 'in_progress', 'completed']).withMessage('Invalid status value'),
    body('priority').optional().isIn(['low', 'medium', 'high']).withMessage('Invalid priority value'),
    body('deadline').optional().isISO8601().withMessage('Invalid deadline date').toDate(),
  ],
  validate,
  updateTask
);

router.delete(
  '/:id',
  authorize('manager'),
  [param('id').isMongoId().withMessage('Invalid task ID')],
  validate,
  deleteTask
);

module.exports = router;
