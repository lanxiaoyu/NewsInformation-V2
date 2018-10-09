from info import constants
from info.models import User, News
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import news_bp
from flask import render_template, session, current_app, jsonify, g, request


@news_bp.route('/news_collect', methods=["post"])
@user_login_data
def news_collected():
    """点击收藏/取消收藏后端接口实现"""
    """
    1.获取参数
        1.1 news_id   action:动作指令  
        1.2 获取当前用户对象
    2.检验1参数
        2.1 非空判断
    3.逻辑处理
        3.1 根据新闻id查询新闻对象
        3.2 收藏:将当前新闻添加到user.collection_news列表中
        3.3 取消收藏:将当前新闻从user.collection_news列表中删除
    4.返回值
    """
    # 1.1
    param_dict = request.json

    news_id = param_dict.get("news_id")
    action = param_dict.get("action")

    # 1.2
    user = g.user

    # 2.1 非空判断
    if not all([news_id, action]):
        return jsonify({"errno": RET.PARAMERR, "errmsg": '参数不足'})

    # 3.1
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno": RET.DBERR, "errmsg": '数据库查询新闻出现错误'})

    # 3.2
    if action == "collect":
        # 收藏
        user.collection_news.append(news)
    else:
        # 取消收藏
        user.collection_news.remove(news)

    # 4.
    return jsonify({"errno": RET.OK, "errmsg": '收藏成功'})


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

    # --------------------------查看用户是否收藏过该条新闻------
    is_collected = False
    # 当前用户已登录
    if user:
        if news in user.collection_news:
            is_collected = True

        # 4. 组织响应数据字典
    data = {
        "user_info": user.to_dict() if user else None,
        "news_rank_list": news_rank_dict_list,
        "news": new_dict,
        "is_collected": is_collected
    }

    return render_template("news/detail.html", data=data)
