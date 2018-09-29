from redis import StrictRedis
import logging


class Config(object):
    """父类配置"""
    DEBUG = True

    # mysql数据库的配置信息
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/NewsInformation_v2"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis数据库的配置信息
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    REDIS_NUM = 1

    SECRET_KEY = "DSFYGHEGEHJOUHGJIBRREJBJ"

    # 通过flask-session扩展.,将flask中的session(内存)调整到redis的配置信息
    # <1>储存数据库类型:redis
    SESSION_TYPE = "redis"
    # <2>将redis实例对象进行传入
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_NUM)
    # <3>对session数据进行加密,需要配置SECRET_KEY
    SESSION_USE_SIGNER = True
    # <4>关闭永久储存
    SESSION_PERMANENT = False
    # <5>过期时长(24小时)
    PERMANENT_SESSION_LIFETIME = 86400


class DevelopmentConfig(Config):
    """开发环境的项目配置信息"""
    DEBUG = True

    # 开发者环境:日志级别-->debug
    LOG_LEVEL = logging.DEBUG


class ProductionConfig(Config):
    """线上模式的配置信息"""
    DEBUG = False

    # 线上环境:日志级别-->WARING
    LOG_LEVEL = logging.WARNING


# 给外界暴露一个使用配置类的接口
config_dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig
}
