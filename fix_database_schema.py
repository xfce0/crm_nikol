#!/usr/bin/env python3
"""
Скрипт для исправления схемы БД - добавление недостающих полей
"""

import sqlite3
import sys
from pathlib import Path

def fix_database_schema(db_path):
    """Добавляет недостающие поля в БД"""
    print(f"🔧 Исправление схемы БД: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Получаем список существующих колонок в tasks
        cursor.execute("PRAGMA table_info(tasks);")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"📋 Существующие колонки в tasks: {existing_columns}")

        # Добавляем недостающие поля в tasks
        if 'project_id' not in existing_columns:
            print("➕ Добавляем поле project_id в tasks...")
            cursor.execute("""
                ALTER TABLE tasks
                ADD COLUMN project_id INTEGER REFERENCES projects(id);
            """)
            print("✅ Поле project_id добавлено")
        else:
            print("✓ Поле project_id уже существует")

        if 'deploy_url' not in existing_columns:
            print("➕ Добавляем поле deploy_url в tasks...")
            cursor.execute("""
                ALTER TABLE tasks
                ADD COLUMN deploy_url VARCHAR(1000);
            """)
            print("✅ Поле deploy_url добавлено")
        else:
            print("✓ Поле deploy_url уже существует")

        if 'tags' not in existing_columns:
            print("➕ Добавляем поле tags в tasks...")
            cursor.execute("""
                ALTER TABLE tasks
                ADD COLUMN tags JSON DEFAULT '[]';
            """)
            print("✅ Поле tags добавлено")
        else:
            print("✓ Поле tags уже существует")

        # Проверяем существование таблиц, которые нужны коду
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        existing_tables = {row[0] for row in cursor.fetchall()}

        # Создаем таблицу payments если её нет
        if 'payments' not in existing_tables:
            print("➕ Создаем таблицу payments...")
            cursor.execute("""
                CREATE TABLE payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER REFERENCES projects(id),
                    client_id INTEGER REFERENCES clients(id),
                    amount FLOAT NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    description TEXT,
                    due_date DATETIME,
                    paid_date DATETIME,
                    payment_method VARCHAR(100),
                    transaction_id VARCHAR(200),
                    invoice_number VARCHAR(100),
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by_id INTEGER REFERENCES admin_users(id)
                );
            """)
            print("✅ Таблица payments создана")
        else:
            print("✓ Таблица payments уже существует")

        # Создаем таблицу task_deadline_notifications если её нет
        if 'task_deadline_notifications' not in existing_tables:
            print("➕ Создаем таблицу task_deadline_notifications...")
            cursor.execute("""
                CREATE TABLE task_deadline_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL REFERENCES tasks(id),
                    notification_type VARCHAR(50) NOT NULL,
                    sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    deadline_at DATETIME NOT NULL
                );
            """)
            print("✅ Таблица task_deadline_notifications создана")
        else:
            print("✓ Таблица task_deadline_notifications уже существует")

        conn.commit()
        print("\n✅ Схема БД успешно обновлена!")

    except Exception as e:
        print(f"\n❌ Ошибка при обновлении схемы: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

    return True

def main():
    # Путь к БД
    db_path = Path(__file__).parent / "admin_panel.db"

    if not db_path.exists():
        print(f"❌ База данных не найдена: {db_path}")
        sys.exit(1)

    # Создаем бэкап
    backup_path = db_path.parent / f"{db_path.stem}_backup_before_fix.db"
    print(f"💾 Создаем бэкап: {backup_path}")

    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ Бэкап создан")

    # Исправляем схему
    if fix_database_schema(str(db_path)):
        print("\n🎉 Готово! Можете перезапустить сервер.")
    else:
        print("\n❌ Не удалось обновить схему БД")
        sys.exit(1)

if __name__ == "__main__":
    main()
