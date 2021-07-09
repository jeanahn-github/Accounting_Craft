"""
실행모드별 실행정보 파싱
"""
from decouple import config
from flask_migrate import Migrate

from config import config_dict
from app import create_app, db


# .env 파일의 DEBUG 설정값에 따라 Debug 모드 또는 Production 모드로 실행여부 결정
DEBUG = config("DEBUG", cast=bool)
get_config_mode = "Debug" if DEBUG else "Production"

try:
    app_config = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

# 실행모드를 app 패키지의 __init.py__로 초기화 연결
app = create_app(app_config)
migrate = Migrate(app, db)

# Debug 모드 일때의 실행정보 전달
if DEBUG:
    app.logger.info('DEBUG = ' + str(DEBUG))
    app.logger.info('Environment = ' + get_config_mode)
    app.logger.info('DBMS = ' + app_config.SQLALCHEMY_DATABASE_URI)

if __name__ == "__main__":
    app.run()