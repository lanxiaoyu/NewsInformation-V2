from flask import g, render_template, request
from . import profile_bp
from info import user_login_data
from info.moduls.profile import profile_bp

#0.0.0:8000/user/info
@profile_bp.route('/base_info', methods=['GET', 'POST'])
@user_login_data
def user_base_info():
  """展示用户基本资料页面"""
  #获取用户对象
  user=g.user
  #get 请求查询用户基本资料并展示
  if request.method == "GET":
      data = {
          "user_info":user.to_dict() if user else  None
      }
      return render_template("profile/user_base_info.html",data = data)
  




#0.0.0:8000/user/info
@profile_bp.route('/info')
@user_login_data
def user_info():

    """
    展示用户个人中心页面"""
    #1.获取用户对象
    user = g.user

    #2. 组织数据
    data={
        "user_info":user.to_dict() if user else None
    }
    return render_template("profile/user.html",data = data)

    