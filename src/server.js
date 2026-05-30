require('dotenv').config();
const express = require('express');
const cors = require('cors');
const morgan = require('morgan');

const connectDB = require('./config/database');
const authRoutes = require('./routes/authRoutes');
const taskRoutes = require('./routes/taskRoutes');
const logRoutes = require('./routes/logRoutes');
const { dashboardRouter, auditRouter } = require('./routes/otherRoutes');
const { errorHandler, notFound } = require('./middleware/errorHandler');

const app = express();

app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

if (process.env.NODE_ENV === 'development') {
  app.use(morgan('dev'));
}

app.get('/health', (req, res) => {
  res.status(200).json({
    success: true,
    message: 'WorkFlow API is running',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development',
  });
});

app.use('/api/auth', authRoutes);
app.use('/api/tasks', taskRoutes);
app.use('/api/logs', logRoutes);
app.use('/api/dashboard', dashboardRouter);
app.use('/api/audit', auditRouter);

app.use(notFound);
app.use(errorHandler);

const PORT = process.env.PORT || 5000;
let server;

const startServer = async () => {
  await connectDB();

  server = app.listen(PORT, () => {
    console.log('\nWorkFlow API Server Started');
    console.log(`Server:  http://localhost:${PORT}`);
    console.log(`Health:  http://localhost:${PORT}/health`);
    console.log(`Env:     ${process.env.NODE_ENV || 'development'}\n`);
  });
};

process.on('unhandledRejection', (err) => {
  console.error(`Unhandled Promise Rejection: ${err.message}`);
  if (server) {
    server.close(() => process.exit(1));
  } else {
    process.exit(1);
  }
});

process.on('SIGTERM', () => {
  console.log('SIGTERM received. Shutting down gracefully...');
  if (server) {
    server.close(() => process.exit(0));
  } else {
    process.exit(0);
  }
});

startServer();

module.exports = app;
