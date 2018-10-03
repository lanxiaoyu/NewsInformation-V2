from info import redis_store
from info.utils.response_code import RET
from . import index_bp
from info.models import User
from flask import render_template, current_app, session, jsonify


# 2.使用蓝图对象

@index_bp.route('/')
def index():
    # 1. 获取当前登录用户的id
    user_id = session.get("user_id")

    user = None #type:User

    # 2.查询用户对象
    if user_id:
        try:
            # 获取用户对象
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({"errno":RET.DBERR, "errmsg": '数据库查询用户错误'})

    # 4. 组织响应数据字典
    data = {
        "user_info":user.to_dict() if user else None,
    }

    return render_template("news/index.html",data = data)


@index_bp.route("/favicon.ico")
def favicon():
    """返回网页图标"""
    return current_app.send_static_file("news/favicon.ico")

