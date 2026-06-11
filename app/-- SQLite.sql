-- SQLite
-- 随便插入一条测试数据看看
INSERT INTO chat_messages (session_id, role, content) VALUES ('test_01', 'user', '你好！');

-- 然后查询
SELECT * FROM chat_messages;
