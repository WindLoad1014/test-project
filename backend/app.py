"""
客服系统后端 - Flask API
支持SQLite和MySQL数据库
"""
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from datetime import datetime
import os
import sys
import hashlib
import jwt
from functools import wraps

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.db_manager import DatabaseManager
from backend.services.email_service import EmailService
from backend.services.ai_service import AIService
from backend.config import Config

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# JWT配置
app.config['SECRET_KEY'] = Config.SECRET_KEY if hasattr(Config, 'SECRET_KEY') else 'your-secret-key-here'
app.config['JWT_EXPIRATION_DELTA'] = 86400  # 24小时

# 初始化服务
db_manager = DatabaseManager()
email_service = EmailService(db_manager)
ai_service = AIService(db_manager)


def token_required(f):
    """JWT认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Token format invalid'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # 解码token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db_manager.fetch_one(
                "SELECT id, username, role FROM users WHERE id = ?",
                (data['user_id'],)
            )
            
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
            
            g.current_user = current_user
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(*args, **kwargs)
    
    return decorated


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/api/email/receive', methods=['POST'])
def receive_email():
    """
    接收邮件接口
    用于邮件系统自动转发玩家邮件到系统
    """
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['sender', 'subject', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # 保存邮件
        email_id = email_service.save_email({
            'sender': data['sender'],
            'subject': data['subject'],
            'content': data['content'],
            'received_at': data.get('received_at', datetime.now().isoformat()),
            'platform': data.get('platform'),
            'app_version': data.get('app_version'),
            'device': data.get('device'),
            'account_id': data.get('account_id'),
            'player_name': data.get('player_name')
        })
        
        return jsonify({
            'success': True,
            'email_id': email_id,
            'message': 'Email received successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/email/<int:email_id>/analyze', methods=['POST'])
def analyze_email(email_id):
    """
    分析邮件接口
    对指定邮件进行意图分类、紧急度判断、相似案例检索
    """
    try:
        # 获取邮件
        email = email_service.get_email(email_id)
        if not email:
            return jsonify({'error': 'Email not found'}), 404
        
        # AI分析
        analysis_result = ai_service.analyze_email(email)
        
        # 保存分析结果
        email_service.save_analysis(email_id, analysis_result)
        
        return jsonify({
            'success': True,
            'email_id': email_id,
            'analysis': analysis_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/email/<int:email_id>/generate-reply', methods=['POST'])
def generate_reply(email_id):
    """
    生成回复接口
    为指定邮件自动生成回复内容
    """
    try:
        data = request.get_json() or {}
        
        # 获取邮件和分析结果
        email = email_service.get_email(email_id)
        if not email:
            return jsonify({'error': 'Email not found'}), 404
        
        analysis = email_service.get_analysis(email_id)
        
        # 生成回复
        use_llm = data.get('use_llm', True)
        reply_result = ai_service.generate_reply(email, analysis, use_llm=use_llm)
        
        # 保存回复
        reply_id = email_service.save_reply({
            'email_id': email_id,
            'content': reply_result['content'],
            'generated_by': reply_result['model'],
            'confidence': reply_result.get('confidence'),
            'is_auto_generated': use_llm
        })
        
        return jsonify({
            'success': True,
            'email_id': email_id,
            'reply_id': reply_id,
            'reply': reply_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/email/<int:email_id>/send-reply', methods=['POST'])
def send_reply(email_id):
    """
    发送回复接口
    将生成的回复发送给玩家
    """
    try:
        data = request.get_json() or {}
        reply_content = data.get('content')
        
        if not reply_content:
            return jsonify({'error': 'Reply content is required'}), 400
        
        # 发送邮件
        send_result = email_service.send_reply(email_id, reply_content)
        
        # 更新邮件状态
        email_service.update_status(email_id, 'replied')
        
        return jsonify({
            'success': True,
            'email_id': email_id,
            'sent_at': send_result['sent_at'],
            'message': 'Reply sent successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/email/auto-process', methods=['POST'])
def auto_process_email():
    """
    自动处理邮件接口
    一键完成：接收 -> 分析 -> 生成回复 -> 发送
    用于完全自动化的邮件回复流程
    """
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['sender', 'subject', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # 1. 保存邮件
        email_id = email_service.save_email({
            'sender': data['sender'],
            'subject': data['subject'],
            'content': data['content'],
            'received_at': data.get('received_at', datetime.now().isoformat()),
            'platform': data.get('platform'),
            'app_version': data.get('app_version'),
            'device': data.get('device'),
            'account_id': data.get('account_id'),
            'player_name': data.get('player_name')
        })
        
        # 2. 分析邮件
        email = email_service.get_email(email_id)
        analysis_result = ai_service.analyze_email(email)
        email_service.save_analysis(email_id, analysis_result)
        
        # 3. 生成回复
        use_llm = data.get('use_llm', True)
        reply_result = ai_service.generate_reply(email, analysis_result, use_llm=use_llm)
        reply_id = email_service.save_reply({
            'email_id': email_id,
            'content': reply_result['content'],
            'generated_by': reply_result['model'],
            'confidence': reply_result.get('confidence'),
            'is_auto_generated': use_llm
        })
        
        # 4. 检查是否满足自动发送条件
        auto_send = data.get('auto_send', False)
        sent = False
        
        if auto_send and analysis_result['urgency'] == 'low' and reply_result.get('confidence', 0) > 0.8:
            # 低紧急度且高置信度时才自动发送
            send_result = email_service.send_reply(email_id, reply_result['content'])
            email_service.update_status(email_id, 'replied')
            sent = True
        else:
            email_service.update_status(email_id, 'pending_review')
        
        return jsonify({
            'success': True,
            'email_id': email_id,
            'reply_id': reply_id,
            'analysis': analysis_result,
            'reply': reply_result,
            'auto_sent': sent,
            'message': 'Email processed successfully' + (' and auto-sent' if sent else ' (pending review)')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/emails', methods=['GET'])
def get_emails():
    """获取邮件列表"""
    try:
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        emails = email_service.get_emails(
            status=status,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'success': True,
            'emails': emails,
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/email/<int:email_id>', methods=['GET'])
def get_email_detail(email_id):
    """获取邮件详情"""
    try:
        email = email_service.get_email_detail(email_id)
        if not email:
            return jsonify({'error': 'Email not found'}), 404
        
        return jsonify({
            'success': True,
            'email': email
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/email/<int:email_id>', methods=['DELETE'])
@token_required
def delete_email(email_id):
    """删除邮件"""
    try:
        # 检查邮件是否存在
        email = email_service.get_email(email_id)
        if not email:
            return jsonify({'error': 'Email not found'}), 404
        
        # 删除邮件
        success = email_service.delete_email(email_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Email deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete email'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取系统统计信息"""
    try:
        stats = email_service.get_statistics()
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge-base/search', methods=['POST'])
def search_knowledge_base():
    """知识库搜索接口（支持模糊搜索）"""
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        top_k = data.get('top_k', 5)
        question_type = data.get('question_type')
        fuzzy = data.get('fuzzy', True)  # 默认启用模糊搜索
        
        results = ai_service.search_similar_cases(query, top_k, question_type, fuzzy=fuzzy)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'fuzzy_enabled': fuzzy
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 认证相关接口 ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录接口"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # 验证用户
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = db_manager.fetch_one(
            "SELECT id, username, role, email, is_active FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        if not user.get('is_active'):
            return jsonify({'error': 'Account is disabled'}), 403
        
        # 更新最后登录时间
        db_manager.update(
            'users',
            {'last_login': datetime.now().isoformat()},
            'id = ?',
            (user['id'],)
        )
        
        # 生成JWT token
        token = jwt.encode(
            {
                'user_id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'exp': datetime.utcnow().timestamp() + app.config['JWT_EXPIRATION_DELTA']
            },
            app.config['SECRET_KEY'],
            algorithm="HS256"
        )
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'email': user['email']
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/register', methods=['POST'])
@token_required
def register():
    """用户注册接口（需要管理员权限）"""
    try:
        # 检查权限
        if g.current_user['role'] != 'admin':
            return jsonify({'error': 'Admin permission required'}), 403
        
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role', 'operator')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # 检查用户名是否已存在
        existing = db_manager.fetch_one(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )
        if existing:
            return jsonify({'error': 'Username already exists'}), 409
        
        # 创建用户
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user_id = db_manager.insert('users', {
            'username': username,
            'password_hash': password_hash,
            'email': email,
            'role': role
        })
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user_id': user_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """获取当前登录用户信息"""
    return jsonify({
        'success': True,
        'user': g.current_user
    })


@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout():
    """用户登出接口"""
    # 客户端需要删除token，这里可以添加token黑名单逻辑
    return jsonify({
        'success': True,
        'message': 'Logout successful'
    })


if __name__ == '__main__':
    # 初始化数据库
    db_manager.init_database()
    
    print("="*80)
    print("🚀 客服系统后端服务启动")
    print("="*80)
    print(f"📡 API地址: http://localhost:5000")
    print(f"📚 文档地址: http://localhost:5000/api/health")
    print("="*80)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
