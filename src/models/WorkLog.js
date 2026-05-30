const mongoose = require('mongoose');

const workLogSchema = new mongoose.Schema(
  {
    taskId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Task',
      required: [true, 'Task ID is required'],
    },
    employeeId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: [true, 'Employee ID is required'],
    },
    logText: {
      type: String,
      required: [true, 'Log text is required'],
      trim: true,
      minlength: [10, 'Log must be at least 10 characters'],
      maxlength: [3000, 'Log cannot exceed 3000 characters'],
    },
    submittedAt: {
      type: Date,
      default: Date.now,
    },
    // AI Verification fields
    aiScore: {
      type: Number,
      min: 0,
      max: 100,
      default: null,
    },
    aiFeedback: {
      type: String,
      default: null,
    },
    verificationStatus: {
      type: String,
      enum: ['pending', 'verified', 'flagged', 'genuine'],
      default: 'pending',
    },
    aiVerifiedAt: {
      type: Date,
      default: null,
    },
  },
  {
    timestamps: true,
  }
);

// Indexes for fast queries
workLogSchema.index({ taskId: 1, employeeId: 1 });
workLogSchema.index({ employeeId: 1, submittedAt: -1 });

module.exports = mongoose.model('WorkLog', workLogSchema);
