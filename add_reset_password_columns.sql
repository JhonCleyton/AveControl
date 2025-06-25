-- Primeiro, adiciona as colunas sem a restrição UNIQUE
ALTER TABLE usuarios ADD COLUMN reset_password_token VARCHAR(100);
ALTER TABLE usuarios ADD COLUMN reset_password_expires DATETIME;

-- Em seguida, adiciona um índice único para o token
CREATE UNIQUE INDEX IF NOT EXISTS ix_usuarios_reset_password_token ON usuarios(reset_password_token);
