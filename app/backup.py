import shutil
from datetime import datetime
import os

def gerar_backup_sqlite():
    origem = os.path.join('instance', 'database.db')
    pasta_backups = 'backups'
    os.makedirs(pasta_backups, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    destino = os.path.join(pasta_backups, f'backup_finance_{timestamp}.db')
    
    if os.path.exists(origem):
        shutil.copy2(origem, destino)
        print(f"Backup realizado com sucesso: {destino}")

if __name__ == '__main__':
    gerar_backup_sqlite()