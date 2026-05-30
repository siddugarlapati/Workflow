# WorkFlow Backend API

An AI-powered, role-based employee task & accountability platform built with Node.js, Express, MongoDB, and Mongoose.

---

## 🚀 Quick Start

```bash
# 1. Clone / extract the project
cd workflow-backend

# 2. Install dependencies
npm install

# 3. Configure environment
cp .env.example .env
# Edit .env with your MongoDB URI and JWT secret

# 4. Start (development)
npm run dev

# 5. Start (production)
npm start
```

---

## 📁 Folder Structure

```
workflow-backend/
├── src/
│   ├── config/
│   │   └── database.js          # MongoDB connection
│   ├── models/
│   │   ├── User.js              # User model (manager/employee)
│   │   ├── Task.js              # Task model
│   │   ├── WorkLog.js           # Work log model
│   │   └── AuditLog.js          # Audit trail model
│   ├── controllers/
│   │   ├── authController.js    # Register, login, me
│   │   ├── taskController.js    # CRUD + my-tasks
│   │   ├── logController.js     # Submit + retrieve logs
│   │   ├── dashboardController.js # Manager & employee dashboards
│   │   └── auditController.js   # Audit log retrieval
│   ├── routes/
│   │   ├── authRoutes.js
│   │   ├── taskRoutes.js
│   │   ├── logRoutes.js
│   │   └── otherRoutes.js       # Dashboard + audit routes
│   ├── middleware/
│   │   ├── auth.js              # JWT verify + role authorize
│   │   ├── errorHandler.js      # Global error handler + 404
│   │   └── validate.js          # express-validator middleware
│   ├── utils/
│   │   ├── aiService.js         # AI log verification + summaries
│   │   └── auditLogger.js       # Audit log helper
│   └── server.js                # Express app entry point
├── .env.example
├── .gitignore
├── package.json
└── README.md
```

---

## 🔑 Environment Variables

```env
PORT=5050
MONGODB_URI=mongodb://localhost:27017/workflow
JWT_SECRET=your_super_secret_jwt_key_change_this_in_production
JWT_EXPIRES_IN=7d
NODE_ENV=development
CORS_ORIGIN=http://localhost:3000

# Optional: AI Integration
AI_API_KEY=your_anthropic_api_key
AI_MODEL=claude-sonnet-4-20250514
```

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/auth/register` | Public | Register a new user |
| POST | `/api/auth/login` | Public | Login and get token |
| GET | `/api/auth/me` | Private | Get current user |

### Tasks

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/tasks` | Manager | Create task |
| GET | `/api/tasks` | Both | Get all tasks (role-filtered) |
| GET | `/api/tasks/my-tasks` | Employee | Get own tasks |
| GET | `/api/tasks/:id` | Both | Get single task |
| PUT | `/api/tasks/:id` | Both | Update task |
| DELETE | `/api/tasks/:id` | Manager | Delete task |

### Work Logs

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/logs` | Employee | Submit work log |
| GET | `/api/logs` | Manager | Get all logs |
| GET | `/api/logs/my-logs` | Employee | Get own logs |
| GET | `/api/logs/task/:taskId` | Both | Get logs for a task |

### Dashboard

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/dashboard/manager` | Manager | Full team dashboard + AI summary |
| GET | `/api/dashboard/employee` | Employee | Personal task dashboard |

### Audit

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/audit` | Both | Get audit logs (role-filtered) |

---

## 🔐 Authentication

All protected routes require a Bearer token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

---

## 🤖 AI Features

### Work Log Verification
When a work log is submitted, the AI analyzes it against the task and returns:
- **aiScore** (0–100): Credibility score
- **aiFeedback**: Plain-English feedback for the manager
- **verificationStatus**: `genuine` | `verified` | `flagged` | `pending`

### Manager Summary
`GET /api/dashboard/manager` includes an AI-generated plain-English briefing of team status.

> Requires `AI_API_KEY` in `.env`. Without it, the system works fully — AI fields return `null` or informational messages.

---

## 📬 Postman Collection Examples

### Register
```json
POST /api/auth/register
{
  "name": "Alice Manager",
  "email": "alice@company.com",
  "password": "password123",
  "role": "manager"
}
```

### Login
```json
POST /api/auth/login
{
  "email": "alice@company.com",
  "password": "password123"
}
```

### Create Task
```json
POST /api/tasks
Authorization: Bearer <manager_token>
{
  "title": "Prepare Q2 Sales Report",
  "description": "Compile all sales data for Q2 and produce a summary PDF.",
  "assignedTo": "<employee_user_id>",
  "priority": "high",
  "deadline": "2026-06-15T18:00:00.000Z"
}
```

### Submit Work Log
```json
POST /api/logs
Authorization: Bearer <employee_token>
{
  "taskId": "<task_id>",
  "logText": "Spent 3 hours collecting raw sales data from the CRM. Exported to Excel and started cleaning duplicate entries. About 40% done with data cleaning."
}
```

### Update Task Status (Employee)
```json
PUT /api/tasks/:id
Authorization: Bearer <employee_token>
{
  "status": "in_progress"
}
```

---

## 🛡️ Role Permissions Summary

| Action | Manager | Employee |
|--------|---------|----------|
| Create task | ✅ | ❌ |
| Assign task | ✅ | ❌ |
| Delete task | ✅ | ❌ |
| View all tasks | ✅ | ❌ (own only) |
| Update task (all fields) | ✅ | ❌ (status only) |
| Submit work log | ✅ | ✅ (own tasks) |
| View all logs | ✅ | ❌ (own only) |
| View manager dashboard | ✅ | ❌ |
| View employee dashboard | ❌ | ✅ |
| View audit logs | ✅ (all) | ✅ (own only) |
