from info import redis_store, constants
from info.utils.response_code import RET
from . import index_bp
from info.models import User, News
from flask import render_template, current_app, session, jsonify


# 2.使用蓝图对象

@index_bp.route('/')
def index():
    # ------------------获取用户登录信息------------------
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

    # ------------------获取新闻点击排行数据------------------
    try:
        news_rank_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS).all()

    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno":RET.DBERR, "errmsg": '数据库获取新闻错误'})

    # 字典列表初始化
    """
        # news_rank_list 对象列表===》 [news1, news2, ...新闻对象 ]
        # news_rank_dict_list 字典列表===> [{新闻字典}, {}, {}]
    """
    news_rank_dict_list = []
    # 将新闻对象列表转换成字典列表
    for news_obj in news_rank_list if news_rank_list else []:
        # 将新闻转换成字典
        news_dict = news_obj.to_dict()
        # 构建字典列表
        news_rank_dict_list.append(news_dict)


    # 4. 组织响应数据字典
    data = {
        "user_info":user.to_dict() if user else None,
        "news_rank_list":news_rank_dict_list
    }

    return render_template("news/index.html",data = data)


@index_bp.route("/favicon.ico")
def favicon():
    """返回网页图标"""
    return current_app.send_static_file("news/favicon.ico")

