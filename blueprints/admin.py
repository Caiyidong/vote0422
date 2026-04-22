from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import db, Poll, Option, User, VoteRecord, AdminLog
from datetime import datetime

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理员权限', 'danger')
            return redirect(url_for('vote.index'))
        return f(*args, **kwargs)
    return decorated


def log_action(action, detail=''):
    log = AdminLog(admin_id=current_user.id, action=action, detail=detail)
    db.session.add(log)


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """后台首页数据看板"""
    total_polls = Poll.query.count()
    active_polls = Poll.query.filter_by(is_active=True).count()
    total_users = User.query.count()
    total_votes = VoteRecord.query.count()
    recent_polls = Poll.query.order_by(Poll.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
                           total_polls=total_polls,
                           active_polls=active_polls,
                           total_users=total_users,
                           total_votes=total_votes,
                           recent_polls=recent_polls)


@admin_bp.route('/polls')
@login_required
@admin_required
def polls():
    """投票管理列表"""
    page = request.args.get('page', 1, type=int)
    all_polls = Poll.query.order_by(Poll.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('admin/polls.html', polls=all_polls)


@admin_bp.route('/polls/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_poll():
    """创建投票"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        end_time_str = request.form.get('end_time', '').strip()
        is_public = request.form.get('is_public') == 'on'
        options_raw = request.form.getlist('options')

        if not title:
            flash('请输入投票标题', 'danger')
            return render_template('admin/create_poll.html')

        options = [o.strip() for o in options_raw if o.strip()]
        if len(options) < 2:
            flash('至少需要2个选项', 'danger')
            return render_template('admin/create_poll.html')

        end_time = None
        if end_time_str:
            try:
                end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('截止时间格式错误', 'danger')
                return render_template('admin/create_poll.html')

        poll = Poll(
            title=title,
            description=description,
            creator_id=current_user.id,
            end_time=end_time,
            is_public=is_public
        )
        db.session.add(poll)
        db.session.flush()  # 获取 poll.id

        for content in options:
            db.session.add(Option(poll_id=poll.id, content=content))

        log_action('创建投票', f'标题：{title}')
        db.session.commit()
        flash('投票创建成功', 'success')
        return redirect(url_for('admin.polls'))

    return render_template('admin/create_poll.html')


@admin_bp.route('/polls/<int:poll_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_poll(poll_id):
    """编辑投票"""
    poll = Poll.query.get_or_404(poll_id)

    if request.method == 'POST':
        poll.title = request.form.get('title', '').strip()
        poll.description = request.form.get('description', '').strip()
        poll.is_public = request.form.get('is_public') == 'on'
        poll.is_active = request.form.get('is_active') == 'on'

        end_time_str = request.form.get('end_time', '').strip()
        if end_time_str:
            try:
                poll.end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('截止时间格式错误', 'danger')
                return render_template('admin/edit_poll.html', poll=poll)
        else:
            poll.end_time = None

        log_action('编辑投票', f'ID：{poll_id}，标题：{poll.title}')
        db.session.commit()
        flash('投票更新成功', 'success')
        return redirect(url_for('admin.polls'))

    return render_template('admin/edit_poll.html', poll=poll)


@admin_bp.route('/polls/<int:poll_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_poll(poll_id):
    """删除投票"""
    poll = Poll.query.get_or_404(poll_id)
    log_action('删除投票', f'ID：{poll_id}，标题：{poll.title}')
    db.session.delete(poll)
    db.session.commit()
    flash('投票已删除', 'success')
    return redirect(url_for('admin.polls'))


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """用户管理"""
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('q', '')
    query = User.query
    if keyword:
        query = query.filter(
            (User.username.contains(keyword)) | (User.email.contains(keyword))
        )
    all_users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('admin/users.html', users=all_users, keyword=keyword)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    """启用/禁用用户"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('不能操作自己的账号', 'warning')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    action = '启用' if user.is_active else '禁用'
    log_action(f'{action}用户', f'用户名：{user.username}')
    db.session.commit()
    flash(f'已{action}用户 {user.username}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/set_admin', methods=['POST'])
@login_required
@admin_required
def set_admin(user_id):
    """设置/取消管理员"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('不能修改自己的权限', 'warning')
        return redirect(url_for('admin.users'))
    user.is_admin = not user.is_admin
    action = '设为管理员' if user.is_admin else '取消管理员'
    log_action(action, f'用户名：{user.username}')
    db.session.commit()
    flash(f'已{action}：{user.username}', 'success')
    return redirect(url_for('admin.users'))
