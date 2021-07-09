"""
config 파일을 이용하여 develop 모드와 production 모드 관리
"""

import os
from decouple import config


class Config(object):

    base_dir = os.path.abspath(os.path.dirname(__file__))

    # python-decouple 패키지를 이용하여 설정파일 .env에서 SECRET_KEY 값을 파싱
    SECRET_KEY = config("SECRET_KEY")

    # 기본설정으로 sqlite를 지정
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(base_dir, 'accounting_craft.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    # python-decouple 패키지를 이용하여 설정파일 .env에서 PostgreSQL의 설정값 파싱
    SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
        config('DB_ENGINE'),
        config('DB_USERNAME'),
        config('DB_PASS'),
        config('DB_HOST'),
        config('DB_PORT'),
        config('DB_NAME')
    )


class DebugConfig(Config):
    DEBUG = True

# Load all possible configurations
config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}
