-- ============================================
-- 世界杯舆情新闻表 - SQL Server 版本
-- 数据库: worldcup_db
-- 表名: worldcup_news
-- ============================================

-- 如果表已存在，先删除
-- DROP TABLE IF EXISTS worldcup_news;

-- 创建表
CREATE TABLE worldcup_news (
    id INT IDENTITY(1,1) PRIMARY KEY,           -- 自增主键
    url NVARCHAR(500) NOT NULL,                 -- 原文链接（唯一键）
    title NVARCHAR(500) NOT NULL,               -- 新闻标题
    industry NVARCHAR(50),                      -- 所属行业（分类）
    publish_time NVARCHAR(50),                  -- 发布时间
    summary NVARCHAR(MAX),                      -- 正文摘要（新闻内容）
    source NVARCHAR(100),                       -- 媒体来源
    worldcup NVARCHAR(50),                      -- 届次（2022卡塔尔/2026美加墨）
    keywords NVARCHAR(500),                     -- 关键词
    created_at DATETIME DEFAULT GETDATE(),      -- 入库时间
    updated_at DATETIME DEFAULT GETDATE()       -- 更新时间
);

-- 创建URL唯一索引（防止重复导入）
CREATE UNIQUE INDEX idx_url_unique ON worldcup_news(url);

-- 创建其他索引（提升查询性能）
CREATE INDEX idx_industry ON worldcup_news(industry);
CREATE INDEX idx_worldcup ON worldcup_news(worldcup);
CREATE INDEX idx_publish_time ON worldcup_news(publish_time);

PRINT '✅ 表 worldcup_news 创建成功！';
