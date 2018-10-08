from info import redis_store, constants
from info.utils.response_code import RET
from . import index_bp
from info.models import User, News, Category
from flask import render_template, current_app, session, jsonify, request


@index_bp.route('/news_list')
def get_news_list():
    """获取新闻列表数据"""
    """
    1.获取参数
        1.1 cid :分类id    page:当前页码(默认第一页)   per_page:每页的多少条数据(默认10)
    2.检验参数
        2.1 非空判断
        2.2 整型强制转换
    3.逻辑处理
        3.1 分页查询
        3.2 对象列表转成字典列表
    4.返回值
    """
    # 1.1
    param_dict = request.args

    cid = param_dict.get("cid")
    page = param_dict.get("page", '1')
    per_page = param_dict.get("per_page", "10")

    # 2.1 非空判断
    if not cid:
        return jsonify({"errno": RET.PARAMERR, "errmsg": '参数不足'})

    # 2.2
    cid = int(cid)
    page = int(page)
    per_page = int(per_page)

    # 3.1
    try:
        paginate = News.query.filter(News.category_id ==cid).order_by(News.create_time.desc()).paginate(page,per_page,False)
        # 获取当前页面的所有数据
        news_list = paginate.items
        # 获取当前页码
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages

    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno":RET.DBERR, "errmsg": '查询新闻列表数据异常'})

    # 3.2
    news_dict_list = []
    for news in news_list if news_list else []:
        news_dict_list.append(news.to_dict())

    data = {
        "news_list":news_dict_list,
        "current_page":current_page,
        "total_page":total_page
    }

    # 4
    return jsonify({"errno":RET.OK, "errmsg": 'ok'},data = data)


@index_bp.route('/')
def index():
    # ------------------获取用户登录信息------------------
    # 1. 获取当前登录用户的id
    user_id = session.get("user_id")

    user = None  # type:User

    # 2.查询用户对象
    if user_id:
        try:
            # 获取用户对象
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({"errno": RET.DBERR, "errmsg": '数据库查询用户错误'})

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

    # ----------获取新闻分类数据-----------
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno": RET.DBERR, "errmsg": '数据库查询类别错误'})

    # 对象列表转换成字典列表
    category_dict_list = []
    for category in categories if categories else []:
        category_dict_list.append(category.to_dict())

    # 4. 组织响应数据字典
    data = {
        "user_info": user.to_dict() if user else None,
        "news_rank_list": news_rank_dict_list,
        "categories": category_dict_list
    }

    return render_template("news/index.html", data=data)


@index_bp.route("/favicon.ico")
def favicon():
    """返回网页图标"""
    return current_app.send_static_file("news/favicon.ico")
