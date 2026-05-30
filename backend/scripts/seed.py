"""
WorkFlow — Database Seeder
==========================
Creates demo manager and employee accounts, tasks, and initial work logs.
Run with: uv run python scripts/seed.py
"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.core.security import hash_password
from app.database import engine, init_db
from app.models.user import Role, User
from app.models.task import Priority, Status, Task
from app.models.work_log import AIConfidence, WorkLog


async def seed_data() -> None:
    print("Initializing database tables...")
    await init_db()
    print("Database tables initialized successfully.")

    # We use an async connection or session, but for the seeder, since it's a script,
    # we can use a synchronous session over the async engine by using run_sync or
    # simple async session. Let's do it using AsyncSession.
    from sqlalchemy.ext.asyncio import AsyncSession
    
    async with AsyncSession(engine, expire_on_commit=False) as session:
        # Check if users already exist
        result = await session.execute(select(User).where(User.email == "manager@demo.com"))
        existing_manager = result.scalar_one_or_none()
        if existing_manager:
            print("Database already seeded. Skipping...")
            return

        print("Seeding demo users...")
        
        # 1. Create Users
        manager = User(
            email="manager@demo.com",
            full_name="Alice Manager",
            hashed_password=hash_password("password123"),
            role=Role.MANAGER,
            department="Operations",
        )
        
        employee1 = User(
            email="employee1@demo.com",
            full_name="Bob Employee",
            hashed_password=hash_password("password123"),
            role=Role.EMPLOYEE,
            department="Logistics",
        )
        
        employee2 = User(
            email="employee2@demo.com",
            full_name="Charlie Employee",
            hashed_password=hash_password("password123"),
            role=Role.EMPLOYEE,
            department="Sales",
        )

        session.add(manager)
        session.add(employee1)
        session.add(employee2)
        await session.commit()
        await session.refresh(manager)
        await session.refresh(employee1)
        await session.refresh(employee2)
        print(f"Created users: {manager.full_name}, {employee1.full_name}, {employee2.full_name}")

        # 2. Create Tasks
        print("Seeding demo tasks...")
        now = datetime.now(timezone.utc)
        
        task1 = Task(
            title="Perform Inventory Audit in Warehouse A",
            description="Count all high-value items in A1-A4 racks and reconcile with ERP records. Highlight any discrepancies above 5%.",
            assigned_to=employee1.id,
            created_by=manager.id,
            priority=Priority.HIGH,
            status=Status.IN_PROGRESS,
            deadline=now + timedelta(days=2),
        )

        task2 = Task(
            title="Draft Regional Logistics Report",
            description="Compile transit delays for Q1. Include carrier SLA report and fuel surcharge analysis.",
            assigned_to=employee1.id,
            created_by=manager.id,
            priority=Priority.MEDIUM,
            status=Status.PENDING,
            deadline=now + timedelta(days=5),
        )

        task3 = Task(
            title="Overdue Client Contract Renewal",
            description="Follow up with Acme Corp regarding their logistics service level contract. Needs immediate signature.",
            assigned_to=employee2.id,
            created_by=manager.id,
            priority=Priority.CRITICAL,
            status=Status.OVERDUE,
            deadline=now - timedelta(days=1),
        )

        task4 = Task(
            title="Weekly Vehicle Fleet Maintenance Check",
            description="Inspect all delivery vans. Check tire pressure, fluid levels, and brake pads. Log issues in fleet sheet.",
            assigned_to=employee1.id,
            created_by=manager.id,
            priority=Priority.LOW,
            status=Status.COMPLETED,
            deadline=now - timedelta(days=2),
        )

        session.add(task1)
        session.add(task2)
        session.add(task3)
        session.add(task4)
        await session.commit()
        await session.refresh(task1)
        await session.refresh(task2)
        await session.refresh(task3)
        await session.refresh(task4)
        print("Demo tasks seeded successfully.")

        # 3. Create Work Logs
        print("Seeding demo work logs...")
        
        # Completed task has a log
        log1 = WorkLog(
            task_id=task4.id,
            employee_id=employee1.id,
            log_text="Completed inspections for all 8 vans. Fluid levels topped off on Van 3 and 5. Brake pads are in good condition. Fleet spreadsheet updated.",
            ai_confidence=AIConfidence.HIGH,
            ai_feedback="Highly detailed work log with specific quantitative metrics showing completed tasks.",
            ai_verified_at=now,
            submitted_at=now - timedelta(days=2),
        )
        
        # In progress task has a log
        log2 = WorkLog(
            task_id=task1.id,
            employee_id=employee1.id,
            log_text="Started audit on Rack A1. Counted 142 items, matching ERP. Moving to A2 tomorrow.",
            ai_confidence=AIConfidence.HIGH,
            ai_feedback="Clear progress log describing specific sections completed and plan for next steps.",
            ai_verified_at=now,
            submitted_at=now - timedelta(days=1),
        )

        # Let's add a low-effort bluffed log on the overdue task to demonstrate AI capabilities!
        log3 = WorkLog(
            task_id=task3.id,
            employee_id=employee2.id,
            log_text="Working on the acme renewal stuff. Will finish it soon.",
            ai_confidence=AIConfidence.LOW,
            ai_feedback="Vague and low-effort work log entry. Does not describe actual progress or concrete outcomes.",
            ai_verified_at=now,
            submitted_at=now - timedelta(hours=2),
        )

        session.add(log1)
        session.add(log2)
        session.add(log3)
        await session.commit()
        print("Demo work logs seeded.")
        print("\nReady! You can now run the backend and frontend.")


if __name__ == "__main__":
    asyncio.run(seed_data())
