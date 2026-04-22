from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Poll, Option, VoteRecord
from datetime import datetime
from sqlalchemy.exc import IntegrityError

vote_bp = Blueprint('vote', __name__)


@vote_bp.route('/')
def index():
    """首页：展示进行中的投票列表"""
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('q', '')

    query = Poll.query.filter_by(is_active=True, is_public=True)
    if keyword:
        query = query.filter(Poll.title.contains(keyword))

    polls = query.order_by(Poll.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('index.html', polls=polls, keyword=keyword)


@vote_bp.route('/poll/<int:poll_id>')
def poll_detail(poll_id):
    """投票详情页"""
    poll = Poll.query.get_or_404(poll_id)

    # 检查权限
    if not poll.is_public and not current_user.is_authenticated:
        flash('请先登录才能查看此投票', 'warning')
        return redirect(url_for('auth.login', next=request.url))

    # 查询当前用户是否已投票
    user_vote = None
    if current_user.is_authenticated:
        user_vote = VoteRecord.query.filter_by(
            user_id=current_user.id, poll_id=poll_id
        ).first()

    return render_template('poll_detail.html', poll=poll, user_vote=user_vote)


@vote_bp.route('/poll/<int:poll_id>/vote', methods=['POST'])
@login_required
def cast_vote(poll_id):
    """提交投票"""
    poll = Poll.query.get_or_404(poll_id)

    if not poll.is_active:
        flash('该投票已关闭', 'danger')
        return redirect(url_for('vote.poll_detail', poll_id=poll_id))

    if poll.is_expired:
        flash('投票已截止', 'danger')
        return redirect(url_for('vote.poll_detail', poll_id=poll_id))

    option_id = request.form.get('option_id', type=int)
    if not option_id:
        flash('请选择一个选项', 'warning')
        return redirect(url_for('vote.poll_detail', poll_id=poll_id))

    option = Option.query.filter_by(id=option_id, poll_id=poll_id).first()
    if not option:
        flash('无效的选项', 'danger')
        return redirect(url_for('vote.poll_detail', poll_id=poll_id))

    try:
        record = VoteRecord(user_id=current_user.id, poll_id=poll_id, option_id=option_id)
        db.session.add(record)
        # 原子更新票数，防并发竞态
        Option.query.filter_by(id=option_id).update(
            {'vote_count': Option.vote_count + 1}
        )
        db.session.commit()
        flash('投票成功！', 'success')
        return redirect(url_for('vote.poll_result', poll_id=poll_id))

    except IntegrityError:
        db.session.rollback()
        flash('您已经参与过该投票', 'warning')
        return redirect(url_for('vote.poll_detail', poll_id=poll_id))


@vote_bp.route('/poll/<int:poll_id>/result')
def poll_result(poll_id):
    """投票结果页"""
    poll = Poll.query.get_or_404(poll_id)
    total = poll.total_votes

    results = []
    for opt in poll.options:
        results.append({
            'id': opt.id,
            'content': opt.content,
            'votes': opt.vote_count,
            'percent': round(opt.vote_count / total * 100, 1) if total > 0 else 0
        })

    return render_template('result.html', poll=poll, results=results, total=total)


@vote_bp.route('/api/poll/<int:poll_id>/result')
def api_poll_result(poll_id):
    """实时获取投票结果（AJAX）"""
    poll = Poll.query.get_or_404(poll_id)
    total = poll.total_votes
    return jsonify({
        'total': total,
        'options': [{
            'id': o.id,
            'content': o.content,
            'votes': o.vote_count,
            'percent': round(o.vote_count / total * 100, 1) if total > 0 else 0
        } for o in poll.options]
    })
