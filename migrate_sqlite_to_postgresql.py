"""
Скрипт миграции данных из SQLite в PostgreSQL
"""
import sys
import sqlite3
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
import os

# Добавляем путь к модулям приложения
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.models import Base
from app.config.settings import settings

def init_postgresql_schema():
    """Инициализация схемы PostgreSQL"""
    print("🔧 Инициализация схемы PostgreSQL...")

    # Создаем синхронный движок для PostgreSQL
    pg_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    pg_engine = create_engine(pg_url)

    # Создаем все таблицы
    Base.metadata.create_all(bind=pg_engine)
    print("✅ Схема PostgreSQL создана успешно")

    return pg_engine

def get_sqlite_data(sqlite_path):
    """Получение данных из SQLite"""
    print(f"📖 Чтение данных из SQLite: {sqlite_path}")

    if not os.path.exists(sqlite_path):
        print(f"❌ Файл SQLite не найден: {sqlite_path}")
        return None

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Получаем список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]

    data = {}
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        data[table] = [dict(row) for row in rows]
        print(f"  📊 Таблица {table}: {len(rows)} записей")

    conn.close()
    return data

def get_boolean_columns():
    """Получение списка булевых колонок из моделей SQLAlchemy"""
    from sqlalchemy import Boolean, inspect as sa_inspect

    boolean_fields = {}

    # Обходим все модели
    for table_name, table in Base.metadata.tables.items():
        boolean_fields[table_name] = []
        for column in table.columns:
            if isinstance(column.type, Boolean):
                boolean_fields[table_name].append(column.name)

    return boolean_fields

def convert_row_types(row, table_name, boolean_columns):
    """Конвертация типов данных из SQLite в PostgreSQL"""
    converted_row = dict(row)

    # Конвертация булевых полей
    if table_name in boolean_columns:
        for bool_col in boolean_columns[table_name]:
            if bool_col in converted_row and converted_row[bool_col] is not None:
                # SQLite хранит boolean как 0/1, конвертируем в True/False
                converted_row[bool_col] = bool(converted_row[bool_col])

    return converted_row

def migrate_data(pg_engine, sqlite_data):
    """Перенос данных из SQLite в PostgreSQL"""
    print("\n🚀 Начало миграции данных...")

    Session = sessionmaker(bind=pg_engine)
    session = Session()

    # Получаем маппинг булевых колонок
    boolean_columns = get_boolean_columns()
    print(f"\n📋 Найдено булевых колонок: {sum(len(cols) for cols in boolean_columns.values())}")

    # Порядок миграции таблиц (с учетом внешних ключей)
    migration_order = [
        'users',
        'clients',
        'projects',
        'project_statuses',
        'tasks',
        'task_comments',
        'executors',
        'services',
        'revisions',
        'transactions',
        'payments',
        'files',
        'portfolio',
        'faq',
        'settings',
        'leads',
        'deals',
        'documents',
        'transcriptions',
        'ai_calls',
        'notifications',
        'chats',
        'chat_messages',
    ]

    migrated_count = {}
    success_count = 0
    error_count = 0

    try:
        for table_name in migration_order:
            if table_name not in sqlite_data:
                continue

            rows = sqlite_data[table_name]
            if not rows:
                continue

            print(f"\n📝 Миграция таблицы '{table_name}': {len(rows)} записей")
            if table_name in boolean_columns and boolean_columns[table_name]:
                print(f"  ℹ️ Булевые поля: {', '.join(boolean_columns[table_name])}")

            # Формируем SQL для вставки
            if rows:
                columns = list(rows[0].keys())
                placeholders = ', '.join([f':{col}' for col in columns])
                columns_str = ', '.join(columns)

                sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

                table_success = 0
                table_errors = 0

                # Вставляем данные пакетами
                for i, row in enumerate(rows):
                    try:
                        # Конвертируем типы данных
                        converted_row = convert_row_types(row, table_name, boolean_columns)
                        session.execute(text(sql), converted_row)
                        table_success += 1

                        if (i + 1) % 100 == 0:
                            session.commit()
                            print(f"  ✓ Обработано {i + 1}/{len(rows)}")
                    except Exception as e:
                        print(f"  ⚠️ Ошибка при вставке записи {i + 1}: {str(e)[:100]}")
                        session.rollback()
                        table_errors += 1
                        continue

                session.commit()
                migrated_count[table_name] = table_success
                success_count += table_success
                error_count += table_errors
                print(f"  ✅ Таблица '{table_name}' мигрирована: {table_success} записей (ошибок: {table_errors})")

        print("\n✅ Миграция завершена!")
        print(f"\n📊 Общая статистика:")
        print(f"  ✅ Успешно: {success_count} записей")
        print(f"  ⚠️ Ошибок: {error_count} записей")
        print("\n📋 Детальная статистика по таблицам:")
        for table, count in migrated_count.items():
            print(f"  {table}: {count} записей")

    except Exception as e:
        print(f"\n❌ Ошибка при миграции: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def main():
    """Основная функция"""
    print("=" * 60)
    print("🔄 МИГРАЦИЯ ДАННЫХ ИЗ SQLite В PostgreSQL")
    print("=" * 60)

    # Путь к SQLite базе
    sqlite_path = "/Users/paulosipov/Downloads/СРМ РЕАКТ/data/bot.db"

    # 1. Инициализация схемы PostgreSQL
    pg_engine = init_postgresql_schema()

    # 2. Получение данных из SQLite
    sqlite_data = get_sqlite_data(sqlite_path)
    if not sqlite_data:
        print("❌ Не удалось получить данные из SQLite")
        return

    # 3. Миграция данных
    migrate_data(pg_engine, sqlite_data)

    print("\n" + "=" * 60)
    print("🎉 МИГРАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 60)

if __name__ == "__main__":
    main()
