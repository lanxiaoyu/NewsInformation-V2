from info import constants, db
from info.models import User, News,Comment,CommentLike
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import news_bp
from flask import render_template, session, current_app, jsonify, g, request



# 0.0.0:8000/news/comment_like
@news_bp.route('/comment_like', methods=['POST'])
@user_login_data
def comment_like():
    """点赞、取消点赞接口"""
    """
    1.获取参数
        1.1 comment_id:评论id，user:当前登录用户，action: 点赞/取消点赞的行为
    2.校验参数
        2.1 非空判断
        2.2 action in ['add', 'remove']
    3.逻辑处理
        3.0 根据comment_id查询当前评论对象
        3.1 action等于add表示点赞：先查询commentlike模型对象是否存在，不存在，再创建commentlike该对象并赋值
        3.2 action等于remove表示取消点赞：先查询commentlike模型对象是否存在，存在，才能去删除commentlike对象
        3.3 将commentlike对象的修改保存回数据库
    4.返回值
    """
    #1.1 用户对象 新闻id comment_id评论的id，action:(点赞、取消点赞)
    params_dict = request.json
    comment_id = params_dict.get("comment_id")
    action = params_dict.get("action")
    # 获取当前登录用户对象
    user = g.user

    #2.1 非空判断
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    #2.2 用户是否登录判断
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    #2.3 action in ["add", "remove"]
    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg="action参数错误")

    # 3.0 根据comment_id查询当前评论对象
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询评论对象异常")
    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论不存在")

    # 3.1 action等于add表示点赞：先查询commentlike模型对象是否存在，不存在，再创建commentlike该对象并赋值
    if action == "add":
        # 点赞
        try:
            commentlike = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                   CommentLike.user_id == user.id).first()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询评论点赞对象异常")
        # 当前用户并未对当前评论点过赞
        if not commentlike:
            # 创建评论点赞模型对象
            commentlike_obj = CommentLike()
            commentlike_obj.user_id = user.id
            commentlike_obj.comment_id = comment_id

            # 添加到数据库
            db.session.add(commentlike_obj)
            # 评论对象上的总评论条数累加
            comment.like_count += 1
    # 3.2 action等于remove表示取消点赞：先查询commentlike模型对象是否存在，存在，才能去删除commentlike对象
    else:
        try:
            commentlike = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                   CommentLike.user_id == user.id).first()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询评论点赞对象异常")

        # 当前用户已经对该评论点过赞，再次点击，表取消点赞
        if commentlike:
            # 将维护用户和评论之前的第三张表的对象删除，即表示取消点赞
            db.session.delete(commentlike)
            # 评论对象上的总评论条数减一
            comment.like_count -= 1

    # 3.3 将commentlike对象的修改保存回数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        # 回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="点赞/取消点赞失败")
    # 4.返回值
    return jsonify(errno=RET.OK, errmsg="OK")



#0.0.0:8000/news/news_comment
@news_bp.route('/news_comment',methods=['post'])
@user_login_data
def news_comment():
    """发布新闻评论接口(主,子评论)"""

    """
    1.获取参数
        1.1 news_id:新闻id,comment_str:评论的内容,parent_id:子评论的父评论(非必传0
    2.检验参数
        2.1非空判断
    3.逻辑处理
        3.0 根据news_id查询当前新闻
        3.1 parent_id没有值:创建主评论模型对象,并复制
        3.2 parent_id有值 :创建子评论模型对象,并赋值
        3.3 将评论模型对象保存到数据库
    4.返回值
    """
    #1.1 news_id:新闻id,comment_str:评论的内容,parent_id:子评论的父评论(非必传0
    params_dict=request.json
    news_id = params_dict.get("news_id")
    comment_str = params_dict.get("comment")
    parent_id = params_dict.get("parent_id")
    #获取用户登录信息
    user=g.user

    #2.1非空判断
    # 2 参数检验
    # 2.1 非空判断
    if not all([news_id,comment_str]):
        return jsonify(errno=RET.PARAMERR, errmsg= '参数不足')
    #2.2 用户是否登录判断

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    #3.0根据news_id查询当前新闻
    try:
        news=News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询新闻对象异常')

    if not news:
        return jsonify(errno=RET.NODATA, errmsg= '新闻不存在')

    #3.1 parent_id没有值: 创建主评论模型对象, 并复制
    comment_obj = Comment()
    comment_obj.user_id = user.id
    comment_obj.news_id = news_id
    comment_obj.content = comment_str

    #3.2 parent_id有值: 创建子评论模型对象, 并赋值
    if parent_id:
        comment_obj.parent_id = parent_id
    #3.3 将评论模型对象保存到数据库
    try:
        db.session.add(comment_obj)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存评论对象异常')
    #4,返回值
    return jsonify(errno=RET.OK, errmsg= '发布评论成功',data=comment_obj.to_dict())



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
            # -----------------查询新闻评论列表数据------------------
        try:
            comments = Comment.query.filter(Comment.news_id == news_id) \
                .order_by(Comment.create_time.desc()).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询评论列表数据异常")
        # 对象列表转字典列表
        comment_dict_list = []
        for comment in comments if comments else []:
            # 评论对象转字典
            comment_dict = comment.to_dict()
            comment_dict_list.append(comment_dict)
        # 4. 组织响应数据字典
    data = {
        "user_info": user.to_dict() if user else None,
        "news_rank_list": news_rank_dict_list,
        "news": new_dict,
        "is_collected": is_collected,
        "comments":comment_dict_list
    }

    return render_template("news/detail.html", data=data)
