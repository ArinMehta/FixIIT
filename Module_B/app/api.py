"""
REST API endpoints for FixIIT Module B.
Includes authentication, ticket management, and admin operations.
"""
from flask import Blueprint, request, jsonify, g, render_template, redirect, url_for
from app.auth import login_and_issue_token
from app.rbac import login_required, admin_required
from app.audit_logger import log_api_event, log_security_event
from app.database import (
    fetch_all, fetch_one, execute_write,
    is_member_admin
)

api = Blueprint('api', __name__)


@api.route('/', methods=['GET'])
def index():
    """
    Home page - redirects to login if not authenticated, dashboard if authenticated.
    """
    return redirect(url_for('api.login_page'))


@api.route('/login', methods=['GET'])
def login_page():
    """
    Login page - serves the login template.
    """
    return render_template('login.html')


@api.route('/dashboard', methods=['GET'])
def dashboard():
    """
    Dashboard page - serves the user dashboard template.
    """
    return render_template('dashboard.html')


@api.route('/portfolio', methods=['GET'])
def portfolio_page():
    """
    Portfolio page - serves the member portfolio template.
    """
    return render_template('portfolio.html')


@api.route('/admin', methods=['GET'])
def admin_panel():
    """
    Admin panel page - serves the admin template.
    """
    return render_template('admin.html')


@api.route('/login', methods=['POST'])
def login():
    """
    Login endpoint - accepts username and password, returns JWT token.
    Request body: {"username": "...", "password": "..."}
    Response: {"session_token": "jwt_token", "member_id": 123, "username": "..."}
    """
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            log_api_event('/login', 'FAILED', 'Missing username or password', None)
            return jsonify({'error': 'Missing username or password'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # Authenticate user and generate token
        success, auth_member, token, message = login_and_issue_token(username, password)

        if not success:
            log_security_event('/login', 'FAILED', f'Invalid credentials for user: {username}', None)
            return jsonify({'error': 'Invalid username or password'}), 401

        response = {
            'session_token': token,
            'member_id': auth_member.member_id,
            'username': auth_member.username,
            'name': auth_member.name,
            'is_admin': auth_member.is_admin,
            'role_codes': auth_member.role_codes,
            'message': message
        }

        log_api_event('/login', 'SUCCESS', f'User {username} logged in', auth_member.member_id)
        return jsonify(response), 200
    
    except Exception as e:
        log_api_event('/login', 'ERROR', str(e), None)
        return jsonify({'error': 'Login failed'}), 500


@api.route('/isAuth', methods=['GET'])
@login_required
def is_auth():
    """
    Check if current JWT token is valid.
    Returns current user information from token.
    Requires: Authorization header with Bearer token
    """
    try:
        member_id = g.member_id
        username = g.username
        
        # Fetch full member info from database
        member_record = fetch_one(
            "SELECT member_id, name, email, contact_number, address FROM members WHERE member_id = %s",
            (member_id,)
        )
        
        is_admin = is_member_admin(member_id)
        
        if member_record:
            name = member_record.get('name', '')
            first_name, last_name = (name.split(' ', 1) + [''])[:2] if name else ('', '')
            response = {
                'is_valid': True,
                'member_id': member_id,
                'username': username,
                'name': name,
                'first_name': first_name,
                'last_name': last_name,
                'email': member_record.get('email'),
                'is_admin': is_admin
            }
            log_api_event('/isAuth', 'SUCCESS', f'Auth check for user {username}', member_id)
            return jsonify(response), 200
        else:
            log_api_event('/isAuth', 'FAILED', f'Member record not found for id {member_id}', member_id)
            return jsonify({'is_valid': False, 'error': 'Member not found'}), 404
    
    except Exception as e:
        member_id = getattr(g, 'member_id', None)
        log_api_event('/isAuth', 'ERROR', str(e), member_id)
        return jsonify({'error': 'Authentication check failed'}), 500


@api.route('/portfolio/me', methods=['GET'])
@login_required
def get_my_portfolio():
    """
    Get member portfolio for the currently authenticated user.
    Requires: Authorization header with Bearer token
    """
    try:
        member_id = g.member_id

        query = """
            SELECT
                m.member_id,
                m.name,
                m.email,
                m.contact_number,
                m.address,
                mp.bio,
                mp.skills,
                mp.github_url,
                mp.linkedin_url,
                mp.updated_at
            FROM members m
            LEFT JOIN member_portfolio mp
              ON mp.member_id = m.member_id
            WHERE m.member_id = %s
        """
        record = fetch_one(query, (member_id,))

        if not record:
            log_api_event('/portfolio/me', 'FAILED', f'Portfolio not found for member {member_id}', member_id)
            return jsonify({'error': 'Member not found'}), 404

        response = {
            'member_id': record.get('member_id'),
            'name': record.get('name'),
            'email': record.get('email'),
            'contact_number': record.get('contact_number'),
            'address': record.get('address'),
            'bio': record.get('bio'),
            'skills': record.get('skills'),
            'github_url': record.get('github_url'),
            'linkedin_url': record.get('linkedin_url'),
            'updated_at': str(record.get('updated_at')) if record.get('updated_at') else None
        }
        log_api_event('/portfolio/me', 'SUCCESS', 'Fetched member portfolio', member_id)
        return jsonify(response), 200

    except Exception as e:
        member_id = getattr(g, 'member_id', None)
        log_api_event('/portfolio/me', 'ERROR', str(e), member_id)
        return jsonify({'error': 'Failed to fetch portfolio'}), 500


@api.route('/portfolio/me', methods=['PUT'])
@login_required
def update_my_portfolio():
    """
    Create or update member portfolio for the current user.
    Requires: Authorization header with Bearer token
    """
    try:
        member_id = g.member_id
        data = request.get_json()

        if not data:
            log_api_event('/portfolio/me (PUT)', 'FAILED', 'No update data provided', member_id)
            return jsonify({'error': 'No data to update'}), 400

        def clean_optional(value, max_len):
            if value is None:
                return None
            text = str(value).strip()
            if not text:
                return None
            if len(text) > max_len:
                raise ValueError(f'Field exceeds max length of {max_len}')
            return text

        try:
            bio = clean_optional(data.get('bio'), 2000)
            skills = clean_optional(data.get('skills'), 500)
            github_url = clean_optional(data.get('github_url'), 255)
            linkedin_url = clean_optional(data.get('linkedin_url'), 255)
        except ValueError as exc:
            log_api_event('/portfolio/me (PUT)', 'FAILED', str(exc), member_id)
            return jsonify({'error': str(exc)}), 400

        query = """
            INSERT INTO member_portfolio (
                member_id, bio, skills, github_url, linkedin_url, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                bio = VALUES(bio),
                skills = VALUES(skills),
                github_url = VALUES(github_url),
                linkedin_url = VALUES(linkedin_url),
                updated_at = NOW()
        """
        execute_write(query, (member_id, bio, skills, github_url, linkedin_url))

        log_api_event('/portfolio/me (PUT)', 'SUCCESS', 'Updated member portfolio', member_id)
        return jsonify({'message': 'Portfolio updated successfully'}), 200

    except Exception as e:
        member_id = getattr(g, 'member_id', None)
        log_api_event('/portfolio/me (PUT)', 'ERROR', str(e), member_id)
        return jsonify({'error': 'Failed to update portfolio'}), 500


@api.route('/tickets', methods=['GET'])
@login_required
def get_tickets():
    """
    Fetch all tickets for the current user.
    Requires: Authorization header with Bearer token
    Returns: List of ticket records belonging to the user.
    """
    try:
        member_id = g.member_id
        username = g.username
        
        query = """
            SELECT ticket_id, title, description, member_id, location_id, category_id,
                   priority, status_id, created_at, updated_at
            FROM tickets
            WHERE member_id = %s
            ORDER BY created_at DESC
        """
        tickets = fetch_all(query, (member_id,))

        ticket_list = []
        for ticket in tickets:
            ticket_list.append({
                'ticket_id': ticket.get('ticket_id'),
                'title': ticket.get('title'),
                'description': ticket.get('description'),
                'member_id': ticket.get('member_id'),
                'location_id': ticket.get('location_id'),
                'category_id': ticket.get('category_id'),
                'priority': ticket.get('priority'),
                'status_id': ticket.get('status_id'),
                'created_date': str(ticket.get('created_at')) if ticket.get('created_at') else None,
                'updated_date': str(ticket.get('updated_at')) if ticket.get('updated_at') else None
            })
        
        log_api_event('/tickets', 'SUCCESS', f'Retrieved {len(ticket_list)} tickets', member_id)
        return jsonify({'tickets': ticket_list, 'count': len(ticket_list)}), 200
    
    except Exception as e:
        member_id = getattr(g, 'member_id', None)
        log_api_event('/tickets', 'ERROR', str(e), member_id)
        return jsonify({'error': 'Failed to retrieve tickets'}), 500


@api.route('/admin/tickets', methods=['GET'])
@admin_required
def get_all_tickets_admin():
    """Fetch all tickets for admin management view."""
    try:
        member_id = g.member_id

        query = """
            SELECT ticket_id, title, description, member_id, location_id, category_id,
                   priority, status_id, created_at, updated_at
            FROM tickets
            ORDER BY created_at DESC
        """
        tickets = fetch_all(query)

        ticket_list = []
        for ticket in tickets:
            ticket_list.append({
                'ticket_id': ticket.get('ticket_id'),
                'title': ticket.get('title'),
                'description': ticket.get('description'),
                'member_id': ticket.get('member_id'),
                'location_id': ticket.get('location_id'),
                'category_id': ticket.get('category_id'),
                'priority': ticket.get('priority'),
                'status_id': ticket.get('status_id'),
                'created_date': str(ticket.get('created_at')) if ticket.get('created_at') else None,
                'updated_date': str(ticket.get('updated_at')) if ticket.get('updated_at') else None
            })

        log_api_event('/admin/tickets', 'SUCCESS', f'Retrieved {len(ticket_list)} tickets', member_id)
        return jsonify({'tickets': ticket_list, 'count': len(ticket_list)}), 200

    except Exception as e:
        member_id = getattr(g, 'member_id', None)
        log_api_event('/admin/tickets', 'ERROR', str(e), member_id)
        return jsonify({'error': 'Failed to retrieve admin tickets'}), 500


@api.route('/tickets', methods=['POST'])
@login_required
def create_ticket():
    """
    Create a new ticket for the current user.
    Requires: Authorization header with Bearer token
    Request body: {"location_id": 1, "category_id": 2, "description": "..."}
    """
    try:
        member_id = g.member_id
        username = g.username
        data = request.get_json()
        
        if not data or 'location_id' not in data or 'category_id' not in data or 'description' not in data:
            log_api_event('/tickets (POST)', 'FAILED', 'Missing required fields', member_id)
            return jsonify({'error': 'Missing required fields: location_id, category_id, description'}), 400
        
        location_id = data.get('location_id')
        category_id = data.get('category_id')
        description = data.get('description')
        title = data.get('title', 'Maintenance Request')
        priority = data.get('priority', 'Medium')

        # Insert ticket with status_id = 1 (Open)
        query = """
            INSERT INTO tickets (
                title, description, member_id, location_id, category_id,
                priority, status_id, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, 1, NOW(), NOW())
        """
        result = execute_write(
            query,
            (title, description, member_id, location_id, category_id, priority)
        )
        
        if result:
            log_api_event('/tickets (POST)', 'SUCCESS', f'Created ticket', member_id)
            return jsonify({'message': 'Ticket created successfully'}), 201
        else:
            log_api_event('/tickets (POST)', 'FAILED', 'Failed to create ticket', member_id)
            return jsonify({'error': 'Failed to create ticket'}), 500
    
    except Exception as e:
        member_id = getattr(g, 'member_id', None)
        log_api_event('/tickets (POST)', 'ERROR', str(e), member_id)
        return jsonify({'error': 'Failed to create ticket'}), 500


@api.route('/tickets/<int:ticket_id>', methods=['PUT'])
@admin_required
def update_ticket(ticket_id):
    """
    Update an existing ticket (admin only).
    Requires: Authorization header with Bearer token from admin user
    Request body: {"status_id": 2} (or other fields to update)
    """
    try:
        member_id = g.member_id
        username = g.username
        data = request.get_json()
        
        if not data:
            log_api_event(f'/tickets/{ticket_id} (PUT)', 'FAILED', 'No update data provided', member_id)
            return jsonify({'error': 'No data to update'}), 400
        
        # Build dynamic update query
        allowed_fields = ['status_id', 'description', 'priority', 'title']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                values.append(data[field])
        
        if not updates:
            log_api_event(f'/tickets/{ticket_id} (PUT)', 'FAILED', 'No valid fields to update', member_id)
            return jsonify({'error': 'No valid fields to update'}), 400
        
        values.append(ticket_id)
        query = f"UPDATE tickets SET {', '.join(updates)}, updated_at = NOW() WHERE ticket_id = %s"
        
        execute_write(query, tuple(values))
        log_api_event(f'/tickets/{ticket_id} (PUT)', 'SUCCESS', 'Ticket updated', member_id)
        return jsonify({'message': 'Ticket updated successfully'}), 200
    
    except Exception as e:
        member_id = getattr(g, 'member_id', None)
        log_api_event(f'/tickets/{ticket_id} (PUT)', 'ERROR', str(e), member_id)
        return jsonify({'error': 'Failed to update ticket'}), 500


@api.route('/tickets/<int:ticket_id>', methods=['DELETE'])
@admin_required
def delete_ticket(ticket_id):
    """
    Delete a ticket (admin only).
    Requires: Authorization header with Bearer token from admin user
    """
    try:
        member_id = g.member_id
        username = g.username
        
        query = "DELETE FROM tickets WHERE ticket_id = %s"
        execute_write(query, (ticket_id,))
        
        log_api_event(f'/tickets/{ticket_id} (DELETE)', 'SUCCESS', 'Ticket deleted', member_id)
        return jsonify({'message': 'Ticket deleted successfully'}), 200
    
    except Exception as e:
        member_id = getattr(g, 'member_id', None)
        log_api_event(f'/tickets/{ticket_id} (DELETE)', 'ERROR', str(e), member_id)
        return jsonify({'error': 'Failed to delete ticket'}), 500
