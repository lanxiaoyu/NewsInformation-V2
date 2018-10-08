from . import news_bp
from flask import render_template


@news_bp.route('/<int:news_id>')
def news_detail(news_id):
    """展示新闻详情页"""
    return render_template("news/detail.html")
