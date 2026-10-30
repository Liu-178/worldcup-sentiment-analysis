# -*- coding: utf-8 -*-
"""
============================================
世界杯舆情数据导入SQL Server脚本
============================================
功能：
1. 从CSV读取数据
2. 批量导入到SQL Server
3. 自动跳过重复URL（使用NOT EXISTS语法）
4. 输出实际新增条数
============================================
依赖安装：
pip install pandas pyodbc

运行方式：
python import_to_sqlserver.py

注意事项：
- 需要先安装SQL Server ODBC驱动
- 需要先在SQL Server中创建worldcup_db数据库和worldcup_news表
============================================
"""

import pandas as pd
import pyodbc
import os
import sys
from datetime import datetime

# ============================================
# 配置参数
# ============================================

# SQL Server连接配置（按需修改，或通过环境变量覆盖）
SERVER = os.environ.get('DB_SERVER', r'localhost\SQLEXPRESS')  # SQL Server地址
DATABASE = os.environ.get('DB_DATABASE', 'worldcup_db')         # 数据库名
USERNAME = os.environ.get('DB_USER', '')                        # 用户名（空则使用Windows身份验证）
PASSWORD = os.environ.get('DB_PASSWORD', '')                    # 密码
DRIVER = '{ODBC Driver 17 for SQL Server}'                      # ODBC驱动版本

# 数据文件配置
PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
CSV_FILE = 'merged_all.csv'    # CSV文件名

# 批量导入配置
BATCH_SIZE = 100               # 每批导入数量


# ============================================
# 连接数据库
# ============================================

def get_connection():
    """
    获取SQL Server连接

    返回:
        pyodbc连接对象
    """
    # 构建连接字符串
    if USERNAME and PASSWORD:
        # SQL Server身份验证
        conn_str = f'DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'
    else:
        # Windows身份验证（推荐）
        conn_str = f'DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes'

    try:
        conn = pyodbc.connect(conn_str)
        print(f"✅ 连接SQL Server成功: {SERVER}/{DATABASE}")
        return conn
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n可能的解决方案:")
        print("1. 检查SQL Server是否已启动")
        print("2. 检查ODBC驱动是否已安装")
        print("3. 检查数据库worldcup_db是否存在")
        return None


def check_table_exists(conn):
    """
    检查表是否存在

    参数:
        conn: 数据库连接

    返回:
        True/False
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'worldcup_news'
    """)
    count = cursor.fetchone()[0]
    return count > 0


def get_existing_count(conn):
    """
    获取表中已有数据数量

    参数:
        conn: 数据库连接

    返回:
        数据数量
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM worldcup_news")
    count = cursor.fetchone()[0]
    return count


# ============================================
# 数据导入
# ============================================

def import_data(conn, df):
    """
    批量导入数据到SQL Server（自动跳过重复URL）

    SQL Server语法：使用NOT EXISTS判断URL是否存在
    不使用INSERT IGNORE（那是MySQL语法）

    参数:
        conn: 数据库连接
        df: 数据DataFrame

    返回:
        实际新增条数
    """
    cursor = conn.cursor()
    inserted_count = 0
    skipped_count = 0
    error_count = 0

    print(f"\n📊 开始导入数据...")
    print(f"   CSV总数据: {len(df)} 条")
    print(f"   批量大小: {BATCH_SIZE} 条/批")

    total = len(df)

    for idx, row in df.iterrows():
        try:
            # 提取数据
            url = str(row.get('url', ''))[:500]
            title = str(row.get('title', ''))[:500]
            industry = str(row.get('industry', ''))[:50]
            publish_time = str(row.get('publish_time', ''))[:50]
            summary = str(row.get('summary', ''))
            source = str(row.get('source', ''))[:100]
            worldcup = str(row.get('worldcup', ''))[:50]
            keywords = str(row.get('keywords', ''))[:500]

            # 跳过空URL
            if not url or url == 'nan' or url == '':
                skipped_count += 1
                continue

            # SQL Server语法：INSERT + NOT EXISTS（自动跳过重复URL）
            # 这比INSERT IGNORE更安全，可以控制跳过逻辑
            sql = """
                INSERT INTO worldcup_news (url, title, industry, publish_time, summary, source, worldcup, keywords)
                SELECT ?, ?, ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM worldcup_news WHERE url = ?
                )
            """

            cursor.execute(sql, (
                url, title, industry, publish_time, summary, source, worldcup, keywords,
                url  # NOT EXISTS的参数
            ))

            # 检查是否实际插入（SQL Server的INSERT SELECT会返回影响行数）
            if cursor.rowcount > 0:
                inserted_count += 1
            else:
                skipped_count += 1  # URL已存在，跳过

            # 进度显示
            if (idx + 1) % BATCH_SIZE == 0 or (idx + 1) == total:
                progress = (idx + 1) / total * 100
                print(f"   进度: {idx + 1}/{total} ({progress:.1f}%) | 新增: {inserted_count} | 跳过: {skipped_count}")

        except Exception as e:
            error_count += 1
            if error_count <= 5:  # 只显示前5个错误
                print(f"   ⚠️ 错误 [{idx+1}]: {e}")

    # 提交事务
    conn.commit()

    print(f"\n{'='*60}")
    print(f"📊 导入完成统计")
    print(f"{'='*60}")
    print(f"   ✅ 实际新增: {inserted_count} 条")
    print(f"   ⏭️ 跳过重复: {skipped_count} 条")
    print(f"   ❌ 导入错误: {error_count} 条")
    print(f"{'='*60}")

    return inserted_count


def import_batch(conn, df):
    """
    批量导入（优化版，使用executemany）

    注意：SQL Server的executemany不支持NOT EXISTS条件，
    所以这里改用单条INSERT + 事务方式

    参数:
        conn: 数据库连接
        df: 数据DataFrame

    返回:
        实际新增条数
    """
    # 使用单条导入方式（更稳定）
    return import_data(conn, df)


# ============================================
# 主程序
# ============================================

def main():
    """主函数"""
    # 修复Windows控制台中文乱码
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("="*60)
    print("📊 世界杯舆情数据导入SQL Server")
    print("="*60)
    print(f"数据库: {SERVER}/{DATABASE}")
    print(f"表名: worldcup_news")
    print("="*60)

    # 1. 加载CSV数据
    csv_path = os.path.join(DATA_DIR, CSV_FILE)
    if not os.path.exists(csv_path):
        print(f"❌ CSV文件不存在: {csv_path}")
        return False

    print(f"\n📂 加载CSV数据: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    print(f"✅ 加载成功: {len(df)} 条")

    # 显示CSV列名
    print(f"   CSV列名: {list(df.columns)}")

    # 2. 连接SQL Server
    conn = get_connection()
    if not conn:
        return False

    # 3. 检查表是否存在
    if not check_table_exists(conn):
        print("\n❌ 表 worldcup_news 不存在！")
        print("请先执行建表SQL脚本: sql/create_table.sql")
        conn.close()
        return False

    print(f"\n✅ 表 worldcup_news 存在")

    # 4. 查看表中已有数据
    existing_count = get_existing_count(conn)
    print(f"   表中已有数据: {existing_count} 条")

    # 5. 导入数据
    inserted_count = import_data(conn, df)

    # 6. 查看导入后数据量
    final_count = get_existing_count(conn)
    print(f"\n📊 导入后总数据量: {final_count} 条")
    print(f"📊 本次实际新增: {inserted_count} 条")

    # 7. 关闭连接
    conn.close()
    print("\n✅ 导入任务完成！")

    return True


if __name__ == '__main__':
    main()