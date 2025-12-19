# app/services/backup_service.py
import os
import shutil
import json
import gzip
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import schedule
import threading
import time

from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text

from ..config.settings import settings
from ..config.logging import get_logger
from ..database.database import SessionLocal, engine
from ..database.models import Base

logger = get_logger(__name__)


class BackupService:
    """Сервис резервного копирования базы данных"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.max_backups = getattr(settings, 'MAX_BACKUPS', 30)
        self.auto_backup_enabled = getattr(settings, 'AUTO_BACKUP_ENABLED', True)
        self.backup_time = getattr(settings, 'BACKUP_TIME', "03:00")
        self.is_running = False
        self.thread = None
        
    def create_backup(self, description: str = None) -> Dict[str, Any]:
        """Создать резервную копию базы данных"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            # Определяем тип БД
            db_url = str(settings.DATABASE_URL)
            
            if 'sqlite' in db_url:
                # Для SQLite просто копируем файл
                result = self._backup_sqlite(backup_path)
            elif 'postgresql' in db_url:
                # Для PostgreSQL используем pg_dump
                result = self._backup_postgresql(backup_path)
            else:
                # Для других БД экспортируем в JSON
                result = self._backup_to_json(backup_path)
            
            # Сохраняем метаданные
            metadata = {
                'timestamp': timestamp,
                'datetime': datetime.now().isoformat(),
                'description': description or 'Manual backup',
                'database_type': 'sqlite' if 'sqlite' in db_url else 'postgresql' if 'postgresql' in db_url else 'other',
                'tables': result.get('tables', []),
                'total_records': result.get('total_records', 0),
                'file_size': self._get_dir_size(backup_path),
                'compressed': False
            }
            
            with open(backup_path / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Сжимаем backup
            compressed_path = self._compress_backup(backup_path)
            if compressed_path:
                shutil.rmtree(backup_path)
                metadata['compressed'] = True
                metadata['file_size'] = os.path.getsize(compressed_path)
            
            # Удаляем старые бэкапы
            self._cleanup_old_backups()
            
            logger.info(f"Backup создан успешно: {backup_name}")
            
            return {
                'success': True,
                'backup_name': backup_name,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания backup: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _backup_sqlite(self, backup_path: Path) -> Dict[str, Any]:
        """Резервное копирование SQLite"""
        try:
            # Находим файл БД
            db_path = settings.DATABASE_URL.replace('sqlite:///', '')
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"База данных не найдена: {db_path}")
            
            # Копируем файл БД
            shutil.copy2(db_path, backup_path / 'database.db')
            
            # Получаем информацию о таблицах
            with engine.connect() as conn:
                tables_result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ))
                tables = [row[0] for row in tables_result]
                
                total_records = 0
                for table in tables:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    total_records += count_result.scalar()
            
            return {
                'tables': tables,
                'total_records': total_records
            }
            
        except Exception as e:
            logger.error(f"Ошибка backup SQLite: {str(e)}")
            raise
    
    def _backup_postgresql(self, backup_path: Path) -> Dict[str, Any]:
        """Резервное копирование PostgreSQL"""
        try:
            import subprocess
            
            # Парсим URL подключения
            from urllib.parse import urlparse
            parsed = urlparse(str(settings.DATABASE_URL))
            
            # Формируем команду pg_dump
            dump_file = backup_path / 'database.sql'
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password
            
            cmd = [
                'pg_dump',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path[1:],  # Убираем первый слэш
                '-f', str(dump_file),
                '--no-owner',
                '--no-privileges'
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            # Получаем информацию о таблицах
            with engine.connect() as conn:
                tables_result = conn.execute(text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                ))
                tables = [row[0] for row in tables_result]
                
                total_records = 0
                for table in tables:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    total_records += count_result.scalar()
            
            return {
                'tables': tables,
                'total_records': total_records
            }
            
        except Exception as e:
            logger.error(f"Ошибка backup PostgreSQL: {str(e)}")
            # Если pg_dump не доступен, используем JSON экспорт
            return self._backup_to_json(backup_path)
    
    def _backup_to_json(self, backup_path: Path) -> Dict[str, Any]:
        """Резервное копирование в JSON формат"""
        try:
            from ..database.models import User, Project, AdminUser, Task, Transaction, Portfolio
            
            db = SessionLocal()
            backup_data = {}
            tables = []
            total_records = 0
            
            # Экспортируем каждую таблицу
            models = {
                'users': User,
                'projects': Project,
                'admin_users': AdminUser,
                'tasks': Task,
                'transactions': Transaction,
                'portfolio': Portfolio
            }
            
            for table_name, model in models.items():
                try:
                    records = db.query(model).all()
                    backup_data[table_name] = [
                        {col.name: getattr(record, col.name) 
                         for col in model.__table__.columns}
                        for record in records
                    ]
                    
                    # Конвертируем datetime в строки
                    for record in backup_data[table_name]:
                        for key, value in record.items():
                            if isinstance(value, datetime):
                                record[key] = value.isoformat()
                    
                    tables.append(table_name)
                    total_records += len(records)
                    
                except Exception as e:
                    logger.warning(f"Не удалось экспортировать таблицу {table_name}: {str(e)}")
            
            # Сохраняем данные
            with open(backup_path / 'data.json', 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            db.close()
            
            return {
                'tables': tables,
                'total_records': total_records
            }
            
        except Exception as e:
            logger.error(f"Ошибка JSON backup: {str(e)}")
            raise
    
    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """Восстановить базу данных из резервной копии"""
        try:
            backup_file = self.backup_dir / f"{backup_name}.tar.gz"
            
            if not backup_file.exists():
                # Проверяем несжатую версию
                backup_path = self.backup_dir / backup_name
                if not backup_path.exists():
                    raise FileNotFoundError(f"Backup не найден: {backup_name}")
            else:
                # Распаковываем архив
                backup_path = self._decompress_backup(backup_file)
            
            # Читаем метаданные
            metadata_file = backup_path / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            # Восстанавливаем в зависимости от типа
            if metadata.get('database_type') == 'sqlite':
                result = self._restore_sqlite(backup_path)
            elif metadata.get('database_type') == 'postgresql':
                result = self._restore_postgresql(backup_path)
            else:
                result = self._restore_from_json(backup_path)
            
            # Удаляем временные файлы
            if backup_file.exists():
                shutil.rmtree(backup_path)
            
            logger.info(f"Backup восстановлен успешно: {backup_name}")
            
            return {
                'success': True,
                'backup_name': backup_name,
                'restored_tables': result.get('tables', []),
                'restored_records': result.get('total_records', 0)
            }
            
        except Exception as e:
            logger.error(f"Ошибка восстановления backup: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _restore_sqlite(self, backup_path: Path) -> Dict[str, Any]:
        """Восстановление SQLite"""
        try:
            backup_db = backup_path / 'database.db'
            if not backup_db.exists():
                raise FileNotFoundError(f"Файл БД не найден в backup")
            
            # Создаем резервную копию текущей БД
            current_db = settings.DATABASE_URL.replace('sqlite:///', '')
            if os.path.exists(current_db):
                shutil.copy2(current_db, f"{current_db}.before_restore")
            
            # Заменяем БД
            shutil.copy2(backup_db, current_db)
            
            # Получаем информацию о восстановленных таблицах
            with engine.connect() as conn:
                tables_result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ))
                tables = [row[0] for row in tables_result]
                
                total_records = 0
                for table in tables:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    total_records += count_result.scalar()
            
            return {
                'tables': tables,
                'total_records': total_records
            }
            
        except Exception as e:
            logger.error(f"Ошибка восстановления SQLite: {str(e)}")
            raise
    
    def _restore_postgresql(self, backup_path: Path) -> Dict[str, Any]:
        """Восстановление PostgreSQL"""
        try:
            import subprocess
            
            dump_file = backup_path / 'database.sql'
            if not dump_file.exists():
                # Пробуем восстановить из JSON
                return self._restore_from_json(backup_path)
            
            # Парсим URL подключения
            from urllib.parse import urlparse
            parsed = urlparse(str(settings.DATABASE_URL))
            
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password
            
            # Очищаем БД
            cmd_drop = [
                'psql',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path[1:],
                '-c', 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'
            ]
            
            subprocess.run(cmd_drop, env=env, capture_output=True)
            
            # Восстанавливаем из дампа
            cmd_restore = [
                'psql',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path[1:],
                '-f', str(dump_file)
            ]
            
            result = subprocess.run(cmd_restore, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"psql restore failed: {result.stderr}")
            
            # Получаем информацию о восстановленных таблицах
            with engine.connect() as conn:
                tables_result = conn.execute(text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                ))
                tables = [row[0] for row in tables_result]
                
                total_records = 0
                for table in tables:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    total_records += count_result.scalar()
            
            return {
                'tables': tables,
                'total_records': total_records
            }
            
        except Exception as e:
            logger.error(f"Ошибка восстановления PostgreSQL: {str(e)}")
            return self._restore_from_json(backup_path)
    
    def _restore_from_json(self, backup_path: Path) -> Dict[str, Any]:
        """Восстановление из JSON"""
        try:
            data_file = backup_path / 'data.json'
            if not data_file.exists():
                raise FileNotFoundError(f"Файл данных не найден в backup")
            
            with open(data_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            from ..database.models import User, Project, AdminUser, Task, Transaction, Portfolio
            
            db = SessionLocal()
            
            # Очищаем таблицы
            models = {
                'users': User,
                'projects': Project,
                'admin_users': AdminUser,
                'tasks': Task,
                'transactions': Transaction,
                'portfolio': Portfolio
            }
            
            for model in models.values():
                try:
                    db.query(model).delete()
                except:
                    pass
            
            db.commit()
            
            # Восстанавливаем данные
            total_records = 0
            restored_tables = []
            
            for table_name, model in models.items():
                if table_name in backup_data:
                    try:
                        for record_data in backup_data[table_name]:
                            # Конвертируем строки обратно в datetime
                            for key, value in record_data.items():
                                if isinstance(value, str) and 'T' in value:
                                    try:
                                        record_data[key] = datetime.fromisoformat(value)
                                    except:
                                        pass
                            
                            record = model(**record_data)
                            db.add(record)
                        
                        db.commit()
                        restored_tables.append(table_name)
                        total_records += len(backup_data[table_name])
                        
                    except Exception as e:
                        logger.warning(f"Не удалось восстановить таблицу {table_name}: {str(e)}")
                        db.rollback()
            
            db.close()
            
            return {
                'tables': restored_tables,
                'total_records': total_records
            }
            
        except Exception as e:
            logger.error(f"Ошибка восстановления из JSON: {str(e)}")
            raise
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """Получить список доступных резервных копий"""
        backups = []
        
        # Ищем все backup файлы
        for item in self.backup_dir.iterdir():
            metadata = {}
            
            if item.suffix == '.gz':
                # Сжатый backup
                backup_name = item.stem.replace('.tar', '')
                metadata['compressed'] = True
                metadata['file_size'] = item.stat().st_size
                
                # Пытаемся прочитать метаданные из архива
                try:
                    import tarfile
                    with tarfile.open(item, 'r:gz') as tar:
                        metadata_member = tar.getmember(f"{backup_name}/metadata.json")
                        metadata_file = tar.extractfile(metadata_member)
                        metadata.update(json.loads(metadata_file.read().decode('utf-8')))
                except:
                    pass
                    
            elif item.is_dir() and item.name.startswith('backup_'):
                # Несжатый backup
                backup_name = item.name
                metadata_file = item / 'metadata.json'
                
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                else:
                    metadata = {
                        'timestamp': backup_name.replace('backup_', ''),
                        'description': 'Unknown backup'
                    }
                
                metadata['compressed'] = False
                metadata['file_size'] = self._get_dir_size(item)
            else:
                continue
            
            backups.append({
                'name': backup_name,
                'metadata': metadata
            })
        
        # Сортируем по дате (новые первые)
        backups.sort(key=lambda x: x['metadata'].get('timestamp', ''), reverse=True)
        
        return backups
    
    def delete_backup(self, backup_name: str) -> bool:
        """Удалить резервную копию"""
        try:
            # Проверяем сжатую версию
            compressed_file = self.backup_dir / f"{backup_name}.tar.gz"
            if compressed_file.exists():
                compressed_file.unlink()
                logger.info(f"Backup удален: {backup_name}")
                return True
            
            # Проверяем несжатую версию
            backup_path = self.backup_dir / backup_name
            if backup_path.exists():
                shutil.rmtree(backup_path)
                logger.info(f"Backup удален: {backup_name}")
                return True
            
            logger.warning(f"Backup не найден: {backup_name}")
            return False
            
        except Exception as e:
            logger.error(f"Ошибка удаления backup: {str(e)}")
            return False
    
    def _compress_backup(self, backup_path: Path) -> Optional[Path]:
        """Сжать backup в tar.gz"""
        try:
            import tarfile
            
            archive_path = self.backup_dir / f"{backup_path.name}.tar.gz"
            
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(backup_path, arcname=backup_path.name)
            
            return archive_path
            
        except Exception as e:
            logger.error(f"Ошибка сжатия backup: {str(e)}")
            return None
    
    def _decompress_backup(self, archive_path: Path) -> Path:
        """Распаковать backup из tar.gz"""
        try:
            import tarfile
            
            extract_path = self.backup_dir
            
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(extract_path)
            
            # Находим распакованную папку
            backup_name = archive_path.stem.replace('.tar', '')
            return extract_path / backup_name
            
        except Exception as e:
            logger.error(f"Ошибка распаковки backup: {str(e)}")
            raise
    
    def _cleanup_old_backups(self):
        """Удалить старые резервные копии"""
        try:
            backups = self.list_backups()
            
            if len(backups) > self.max_backups:
                # Удаляем самые старые
                for backup in backups[self.max_backups:]:
                    self.delete_backup(backup['name'])
                    
        except Exception as e:
            logger.error(f"Ошибка очистки старых backup: {str(e)}")
    
    def _get_dir_size(self, path: Path) -> int:
        """Получить размер директории"""
        total = 0
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
        return total
    
    def start_auto_backup(self):
        """Запустить автоматическое резервное копирование"""
        if not self.auto_backup_enabled:
            logger.info("Автоматическое резервное копирование отключено")
            return
        
        if self.is_running:
            logger.warning("Автоматическое резервное копирование уже запущено")
            return
        
        self.is_running = True
        
        # Настраиваем расписание
        schedule.every().day.at(self.backup_time).do(
            lambda: self.create_backup("Automatic daily backup")
        )
        
        # Запускаем в отдельном потоке
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info(f"Автоматическое резервное копирование запущено (время: {self.backup_time})")
    
    def stop_auto_backup(self):
        """Остановить автоматическое резервное копирование"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Автоматическое резервное копирование остановлено")
    
    def _run_scheduler(self):
        """Основной цикл планировщика"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Проверяем каждую минуту


# Глобальный экземпляр сервиса
backup_service = BackupService()