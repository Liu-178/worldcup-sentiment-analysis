-- ============================================
-- 清理重复URL数据 - SQL Server 版本
-- 说明：在添加唯一约束前，先清理已存在的重复数据
-- ============================================

-- 1. 查看重复URL（仅查看，不删除）
SELECT url, COUNT(*) as duplicate_count
FROM worldcup_news
GROUP BY url
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- 2. 删除重复URL，只保留最早的那条（id最小的）
-- 方法：使用CTE找出重复数据，删除id较大的
WITH duplicates AS (
    SELECT
        id,
        url,
        ROW_NUMBER() OVER (PARTITION BY url ORDER BY id ASC) as row_num
    FROM worldcup_news
)
DELETE FROM worldcup_news
WHERE id IN (
    SELECT id FROM duplicates WHERE row_num > 1
);

-- 3. 验证是否还有重复
SELECT url, COUNT(*) as count
FROM worldcup_news
GROUP BY url
HAVING COUNT(*) > 1;

-- 如果返回空结果，说明没有重复了
PRINT '✅ 重复数据清理完成！';

-- ============================================
-- 如果之前没建唯一索引，现在可以建
-- ============================================
-- 先检查索引是否存在
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'idx_url_unique' AND object_id = OBJECT_ID('worldcup_news')
)
BEGIN
    CREATE UNIQUE INDEX idx_url_unique ON worldcup_news(url);
    PRINT '✅ URL唯一索引创建成功！';
END
ELSE
BEGIN
    PRINT '⚠️ URL唯一索引已存在，跳过创建';
END
