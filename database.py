# -*- coding: utf-8 -*-
"""SQLite 食物数据库。

数据库文件 foods.db 与本文件放在同一目录，首次运行时自动建表并写入默认食物。
用户手动添加的食物也会保存在这里，供以后重复使用。
"""

import datetime
import json
import os
import sqlite3
import sys

from foods import DEFAULT_FOODS, FOODS_VERSION

# 打包成 exe 后（PyInstaller 等），数据文件应放在 exe 所在目录而非临时解压目录，
# 这样用户的数据才能持久保存。
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "foods.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    return conn


def init_db():
    """建表并写入默认食物；食物库版本变化时自动清空旧数据、写入新数据。"""
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            carbs REAL NOT NULL,
            protein REAL NOT NULL,
            fat REAL NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            meal_period TEXT NOT NULL,
            kcal REAL NOT NULL,
            carbs REAL NOT NULL,
            protein REAL NOT NULL,
            fat REAL NOT NULL,
            items TEXT NOT NULL
        )
        """
    )
    cur.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    cur.execute("SELECT value FROM meta WHERE key = 'foods_version'")
    row = cur.fetchone()
    current = int(row[0]) if row else 0
    if current != FOODS_VERSION:
        cur.execute("DELETE FROM foods")
        cur.executemany(
            "INSERT INTO foods (name, carbs, protein, fat) VALUES (?, ?, ?, ?)",
            DEFAULT_FOODS,
        )
        cur.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('foods_version', ?)",
            (str(FOODS_VERSION),),
        )
    conn.commit()
    conn.close()


def add_food(name, carbs, protein, fat):
    """新增食物；若同名食物已存在则更新其营养含量。返回是否为新食物。"""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT id FROM foods WHERE name = ?", (name,))
    exists = cur.fetchone() is not None
    cur.execute(
        """
        INSERT INTO foods (name, carbs, protein, fat) VALUES (?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET carbs = excluded.carbs,
                                         protein = excluded.protein,
                                         fat = excluded.fat
        """,
        (name, carbs, protein, fat),
    )
    conn.commit()
    conn.close()
    return not exists


def all_foods():
    """返回所有食物，每项为 (名称, 碳水, 蛋白质, 脂肪)。按录入顺序返回。"""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT name, carbs, protein, fat FROM foods ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_food(name):
    """按名称查找食物，返回 (碳水, 蛋白质, 脂肪) 或 None。"""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT carbs, protein, fat FROM foods WHERE name = ?", (name,))
    row = cur.fetchone()
    conn.close()
    return row


def delete_food(name):
    """按名称删除食物。"""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM foods WHERE name = ?", (name,))
    conn.commit()
    conn.close()


def add_record(meal_period, kcal, carbs, protein, fat, items):
    """保存一条饮食记录。items 为食物明细列表（list of dict）。返回记录时间字符串。"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO records (datetime, meal_period, kcal, carbs, protein, fat, items) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (now, meal_period, kcal, carbs, protein, fat, json.dumps(items, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()
    return now


def get_records(date_str=None):
    """返回饮食记录列表，每项 (id, 时间, 餐次, 热量, 碳水, 蛋白质, 脂肪, 明细list)。

    date_str 形如 '2026-10-20'，为空则返回全部。
    """
    conn = _connect()
    cur = conn.cursor()
    if date_str:
        cur.execute(
            "SELECT id, datetime, meal_period, kcal, carbs, protein, fat, items "
            "FROM records WHERE datetime LIKE ? ORDER BY datetime DESC",
            (date_str + "%",),
        )
    else:
        cur.execute(
            "SELECT id, datetime, meal_period, kcal, carbs, protein, fat, items "
            "FROM records ORDER BY datetime DESC"
        )
    rows = cur.fetchall()
    conn.close()

    result = []
    for rid, dt, period, kcal, carbs, protein, fat, items_json in rows:
        result.append((rid, dt, period, kcal, carbs, protein, fat, json.loads(items_json)))
    return result


def delete_record(record_id):
    """按 id 删除一条饮食记录。"""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


def get_record_dates():
    """返回所有记录过的日期（去重、倒序），形如 '2026-10-20'。"""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT substr(datetime, 1, 10) AS d FROM records ORDER BY d DESC")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]
