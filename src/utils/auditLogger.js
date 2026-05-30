const AuditLog = require('../models/AuditLog');

/**
 * Create an audit log entry.
 * Audit log failures are intentionally non-blocking for the main request.
 */
const createAuditLog = async ({ userId, action, entityType, entityId, metadata = {} }) => {
  try {
    await AuditLog.create({ userId, action, entityType, entityId, metadata });
  } catch (error) {
    console.error('Audit log creation failed:', error.message);
  }
};

module.exports = { createAuditLog };
