from info import constants
from info.models import User, News
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import news_bp
from flask import render_template, session, current_app, jsonify, g


@news_bp.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    """展示新闻详情页"""
    # ------------------获取用户登录信息------------------
    user = g.user

    # ------------------获取新闻点击排行数据------------------
    try:
        news_rank_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS).all()

    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno": RET.DBERR, "errmsg": '数据库获取新闻错误'})


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

    # ------------------获取新闻详细数据-----------------
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno": RET.DBERR, "errmsg": '查询新闻数据错误'})

    # 将新闻对象转成字典
    new_dict = news.to_dict() if news else None

    # 用户浏览量+1
    news.clicks += 1

        # 4. 组织响应数据字典
    data = {
            "user_info": user.to_dict() if user else None,
            "news_rank_list": news_rank_dict_list,
            "news":new_dict
        }

    return render_template("news/detail.html",data = data)
