from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
import bcrypt

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('vote.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        # 校验
        if not username or not email or not password:
            flash('请填写所有必填项', 'danger')
            return render_template('register.html')

        if len(username) < 3 or len(username) > 50:
            flash('用户名长度应为3-50个字符', 'danger')
            return render_template('register.html')

        if password != confirm:
            flash('两次密码输入不一致', 'danger')
            return render_template('register.html')

        if len(password) < 8:
            flash('密码长度至少8位', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return render_template('register.html')

        # 加密密码并创建用户
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(username=username, email=email, password=hashed.decode('utf-8'))
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('注册成功，欢迎加入！', 'success')
        return redirect(url_for('vote.index'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('vote.index'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        # 支持用户名或邮箱登录
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            flash('用户名或密码错误', 'danger')
            return render_template('login.html')

        if not user.is_active:
            flash('账号已被禁用，请联系管理员', 'danger')
            return render_template('login.html')

        login_user(user, remember=remember)
        next_page = request.args.get('next')
        flash(f'欢迎回来，{user.username}！', 'success')
        return redirect(next_page or url_for('vote.index'))

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功退出登录', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_info':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()

            if username != current_user.username:
                if User.query.filter_by(username=username).first():
                    flash('用户名已存在', 'danger')
                    return render_template('profile.html')
                current_user.username = username

            if email != current_user.email:
                if User.query.filter_by(email=email).first():
                    flash('邮箱已被使用', 'danger')
                    return render_template('profile.html')
                current_user.email = email

            db.session.commit()
            flash('个人信息更新成功', 'success')

        elif action == 'change_password':
            old_pw = request.form.get('old_password', '')
            new_pw = request.form.get('new_password', '')
            confirm = request.form.get('confirm_password', '')

            if not bcrypt.checkpw(old_pw.encode('utf-8'), current_user.password.encode('utf-8')):
                flash('原密码错误', 'danger')
                return render_template('profile.html')

            if len(new_pw) < 8:
                flash('新密码至少8位', 'danger')
                return render_template('profile.html')

            if new_pw != confirm:
                flash('两次密码不一致', 'danger')
                return render_template('profile.html')

            current_user.password = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            db.session.commit()
            flash('密码修改成功', 'success')

    return render_template('profile.html')
