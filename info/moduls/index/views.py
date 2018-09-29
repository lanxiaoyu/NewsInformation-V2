from info import redis_store
from . import index_bp
import logging
from flask import current_app


# 2.使用蓝图对象
@index_bp.route('/index')
def index():
    # 使用redis对象存储kv数据
    redis_store.set("name", "ywk")

    logging.debug("我是debug级别日志")
    logging.info("我是infog级别日志")
    logging.warning("我是warning级别日志")
    logging.error("我是error级别日志")
    logging.critical("我是critical级别日志")

    # flask中对logging模块进行了封装,直接用current_app调用,常用的方法
    current_app.logger.debug("falsk中记录的debug日志")
    return "index page"
