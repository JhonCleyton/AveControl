import sqlite3

def check_table_structure():
    conn = sqlite3.connect('instance/sistema.db')
    cursor = conn.cursor()
    
    # Verificar se a tabela existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
    if not cursor.fetchone():
        print("Tabela 'usuarios' não existe!")
        return
    
    # Obter estrutura da tabela
    cursor.execute("PRAGMA table_info(usuarios)")
    columns = cursor.fetchall()
    print("\nEstrutura da tabela 'usuarios':")
    for col in columns:
        print(f"Nome: {col[1]}, Tipo: {col[2]}, NotNull: {col[3]}, Default: {col[4]}")
    
    # Obter alguns dados da tabela
    cursor.execute("SELECT * FROM usuarios LIMIT 1")
    data = cursor.fetchone()
    if data:
        print("\nPrimeira linha de dados:")
        print(data)
    else:
        print("\nNenhum dado encontrado na tabela")
    
    conn.close()

if __name__ == '__main__':
    check_table_structure()
