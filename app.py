from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config
from models import db, User
from datetime import datetime

migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'warning'


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 向所有模板注入 now 变量（用于截止时间比较）
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    # 注册蓝图
    from blueprints.auth import auth_bp
    from blueprints.vote import vote_bp
    from blueprints.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(vote_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        # 自动创建默认管理员账号（首次运行）
        from models import User
        import bcrypt
        if not User.query.filter_by(username='admin').first():
            pw = bcrypt.hashpw(b'admin123456', bcrypt.gensalt()).decode('utf-8')
            admin = User(username='admin', email='admin@vote.com', password=pw, is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print('✅ 默认管理员已创建：admin / admin123456')
    app.run(debug=True, host='0.0.0.0', port=5000)
