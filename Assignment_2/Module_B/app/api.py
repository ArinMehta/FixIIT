"""
REST API endpoints for FixIIT Module B.
Includes authentication, ticket management, and admin operations.
"""
from datetime import date, datetime, time
import re

from flask import Blueprint, request, jsonify, g, render_template, redirect, url_for
from app.auth import login_and_issue_token
from app.rbac import login_required, admin_required
from app.audit_logger import log_api_event, log_security_event
from app import models
from app.database import (
    allocate_ticket_id,
    category_exists,
    DatabaseError,
    execute_write,
    fetch_all,
    fetch_one,
    is_member_admin,
    is_ticket_sharding_migration_complete,
    location_exists,
    member_exists,
    status_exists,
)
from app.sharding import (
    all_ticket_shards,
    get_ticket_shard_config,
    resolve_ticket_shard,
    shard_for_member,
)

api = Blueprint('api', __name__)


VALID_PRIORITIES = {'Low', 'Medium', 'High', 'Urgent', 'Emergency'}
TAMPER_EVENTS_PER_SOURCE = 200
TAMPER_EVENTS_RESPONSE_LIMIT = 200
DATE_ONLY_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
ISO_DATETIME_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?$')


class MigrationIncompleteError(RuntimeError):
    """Raised when ticket writes are attempted before migration completion."""


class TicketIntegrityError(RuntimeError):
    """Raised when cross-shard ticket corruption is detected."""


class TicketRepairUnavailableError(RuntimeError):
    """Raised when a cross-shard repair scan cannot complete safely."""


def _serialize_ticket(ticket):
    """Convert one ticket row into the existing API response shape."""
    return {
        'ticket_id': ticket.get('ticket_id'),
        'title': ticket.get('title'),
        'description': ticket.get('description'),
        'member_id': ticket.get('member_id'),
        'location_id': ticket.get('location_id'),
        'category_id': ticket.get('category_id'),
        'priority': ticket.get('priority'),
        'status_id': ticket.get('status_id'),
        'created_date': str(ticket.get('created_at')) if ticket.get('created_at') else None,
        'updated_date': str(ticket.get('updated_at')) if ticket.get('updated_at') else None,
    }


def _parse_positive_int(value, field_name):
    """Validate that an incoming value is a positive integer."""
    if isinstance(value, bool):
        raise ValueError(f'{field_name} must be a positive integer')

    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{field_name} must be a positive integer') from exc

    if parsed <= 0:
        raise ValueError(f'{field_name} must be a positive integer')
    return parsed


def _normalize_priority(value):
    """Validate one ticket priority against the existing allowed set."""
    if value is None:
        return None

    text = str(value).strip()
    if text not in VALID_PRIORITIES:
        raise ValueError('priority must be one of Low, Medium, High, Urgent, Emergency')
    return text


def _normalize_required_ticket_text(value, field_name):
    """Reject nulls and blank text for required ticket string inputs."""
    if value is None:
        raise ValueError(f'{field_name} cannot be null')

    text = str(value).strip()
    if not text:
        raise ValueError(f'{field_name} cannot be empty')
    return text


def _normalize_optional_ticket_title(value):
    """Normalize title while preserving the default for omitted titles."""
    if value is None:
        raise ValueError('title cannot be null')

    text = str(value).strip()
    return text or 'Maintenance Request'


def _parse_ticket_datetime(value, field_name, is_end=False):
    """Parse admin ticket filter datetimes from query params."""
    if value is None or str(value).strip() == '':
        return None

    text = str(value).strip()
    try:
        if DATE_ONLY_PATTERN.fullmatch(text):
            parsed_date = date.fromisoformat(text)
            boundary_time = time(23, 59, 59) if is_end else time(0, 0, 0)
            return datetime.combine(parsed_date, boundary_time)
        if ISO_DATETIME_PATTERN.fullmatch(text):
            return datetime.fromisoformat(text.replace(' ', 'T')).replace(microsecond=0)
    except ValueError as exc:
        raise ValueError(
            f'{field_name} must be ISO datetime or YYYY-MM-DD'
        ) from exc

    raise ValueError(f'{field_name} must be ISO datetime or YYYY-MM-DD')


def _validate_ticket_create_references(member_id, location_id, category_id):
    """Validate sharded ticket references against coordinator tables."""
    if not member_exists(member_id):
        raise ValueError('Authenticated member does not exist')
    if not location_exists(location_id):
        raise ValueError('location_id does not exist')
    if not category_exists(category_id):
        raise ValueError('category_id does not exist')
    if not status_exists(1):
        raise ValueError('Default ticket status_id=1 is missing')


def _ensure_ticket_writes_enabled():
    """Block ticket writes until the explicit sharding migration has completed."""
    if not is_ticket_sharding_migration_complete():
        raise MigrationIncompleteError(
            'Ticket writes are disabled until Assignment 4 ticket sharding migration completes'
        )


def _build_admin_ticket_filters():
    """Build shard-safe SQL filters for the cross-shard admin ticket view."""
    created_from = _parse_ticket_datetime(
        request.args.get('created_from'),
        'created_from',
    )
    created_to = _parse_ticket_datetime(
        request.args.get('created_to'),
        'created_to',
        is_end=True,
    )
    ticket_id_min = request.args.get('ticket_id_min')
    ticket_id_max = request.args.get('ticket_id_max')
    parsed_ticket_id_min = None
    parsed_ticket_id_max = None

    if ticket_id_min not in (None, ''):
        parsed_ticket_id_min = _parse_positive_int(ticket_id_min, 'ticket_id_min')
    if ticket_id_max not in (None, ''):
        parsed_ticket_id_max = _parse_positive_int(ticket_id_max, 'ticket_id_max')
    if created_from and created_to and created_from > created_to:
        raise ValueError('created_from must be less than or equal to created_to')
    if (
        parsed_ticket_id_min is not None
        and parsed_ticket_id_max is not None
        and parsed_ticket_id_min > parsed_ticket_id_max
    ):
        raise ValueError('ticket_id_min must be less than or equal to ticket_id_max')

    clauses = []
    params = []

    if created_from:
        clauses.append('created_at >= %s')
        params.append(created_from.strftime('%Y-%m-%d %H:%M:%S'))
    if created_to:
        clauses.append('created_at <= %s')
        params.append(created_to.strftime('%Y-%m-%d %H:%M:%S'))
    if parsed_ticket_id_min is not None:
        clauses.append('ticket_id >= %s')
        params.append(parsed_ticket_id_min)
    if parsed_ticket_id_max is not None:
        clauses.append('ticket_id <= %s')
        params.append(parsed_ticket_id_max)

    query = """
        SELECT ticket_id, title, description, member_id, location_id, category_id,
               priority, status_id, created_at, updated_at
        FROM tickets
    """
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at DESC, ticket_id DESC"
    return query, tuple(params)


def _fetch_tamper_events_for_source(source_name, source_type, db_config, shard_idx=None):
    """Fetch only the newest bounded tamper rows from one audit source."""
    rows = fetch_all(
        """
        SELECT
            id, table_name, operation, pk_value, actor_member_id,
            endpoint, source, before_json, after_json, changed_at
        FROM db_change_audit
        WHERE source = 'DIRECT_DB'
        ORDER BY changed_at DESC
        LIMIT %s
        """,
        (TAMPER_EVENTS_PER_SOURCE,),
        db_config=db_config,
    )

    for row in rows:
        row['source_name'] = source_name
        row['source_type'] = source_type
        row['shard_idx'] = shard_idx
        row['source_event_id'] = row.get('id')
        row['event_id'] = f"{source_name}:{row.get('id')}"
    return rows


def _upsert_ticket_locator(ticket_id, member_id, shard_idx, actor_member_id, endpoint):
    """Create or repair the authoritative ticket locator row."""
    execute_write(
        """
        INSERT INTO ticket_locator (ticket_id, member_id, shard_idx, created_at, updated_at)
        VALUES (%s, %s, %s, NOW(), NOW())
        ON DUPLICATE KEY UPDATE
            member_id = VALUES(member_id),
            shard_idx = VALUES(shard_idx),
            updated_at = NOW()
        """,
        (ticket_id, member_id, shard_idx),
        audit_context={
            'actor_member_id': actor_member_id,
            'endpoint': endpoint,
        },
    )


def _find_ticket_across_shards(ticket_id):
    """Find a ticket across all shards for stale-locator recovery."""
    hits = []
    for shard_idx, shard_config in all_ticket_shards():
        row = fetch_one(
            """
            SELECT ticket_id, member_id
            FROM tickets
            WHERE ticket_id = %s
            """,
            (ticket_id,),
            db_config=shard_config,
        )
        if row:
            hits.append({
                'ticket_id': row['ticket_id'],
                'member_id': row['member_id'],
                'shard_idx': shard_idx,
            })
    return hits


def _validate_ticket_shard_hit(ticket_id, member_id, shard_idx):
    """Reject ticket rows that violate the approved member_id shard formula."""
    expected_shard_idx = shard_for_member(member_id)
    if expected_shard_idx != int(shard_idx):
        raise TicketIntegrityError(
            f'ticket_id {ticket_id} is stored on shard {shard_idx}, expected {expected_shard_idx}'
        )


def _resolve_ticket_for_admin_action(ticket_id, actor_member_id, endpoint):
    """Resolve a ticket shard and repair or remove stale locator rows when needed."""
    locator = resolve_ticket_shard(ticket_id)
    if locator:
        shard_config = get_ticket_shard_config(locator['shard_idx'])
        shard_row = fetch_one(
            "SELECT ticket_id, member_id FROM tickets WHERE ticket_id = %s",
            (ticket_id,),
            db_config=shard_config,
        )
        if shard_row:
            _validate_ticket_shard_hit(
                ticket_id,
                shard_row['member_id'],
                locator['shard_idx'],
            )
            if int(shard_row['member_id']) != int(locator['member_id']):
                _upsert_ticket_locator(
                    ticket_id,
                    shard_row['member_id'],
                    locator['shard_idx'],
                    actor_member_id,
                    f'{endpoint} - locator member repair',
                )
            return {
                'ticket_id': ticket_id,
                'member_id': int(shard_row['member_id']),
                'shard_idx': int(locator['shard_idx']),
            }

    try:
        shard_hits = _find_ticket_across_shards(ticket_id)
    except DatabaseError as exc:
        raise TicketRepairUnavailableError(
            f'ticket_id {ticket_id} could not be repair-resolved because shard scan failed: {exc}'
        ) from exc

    if len(shard_hits) > 1:
        raise TicketIntegrityError(f'ticket_id {ticket_id} exists on multiple shards')
    if not shard_hits:
        if locator:
            execute_write(
                "DELETE FROM ticket_locator WHERE ticket_id = %s",
                (ticket_id,),
                audit_context={
                    'actor_member_id': actor_member_id,
                    'endpoint': f'{endpoint} - stale locator cleanup',
                },
            )
        return None

    repaired = shard_hits[0]
    _validate_ticket_shard_hit(
        repaired['ticket_id'],
        repaired['member_id'],
        repaired['shard_idx'],
    )
    _upsert_ticket_locator(
        ticket_id,
        repaired['member_id'],
        repaired['shard_idx'],
        actor_member_id,
        f'{endpoint} - {"locator" if locator else "missing locator"} repair',
    )
    return repaired


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
    Dashboard page shell.

    Note: Browser navigation requests cannot include custom Authorization
    headers. The template's JS performs token validation using /isAuth.
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
    Admin page shell.

    Note: Browser navigation requests cannot include custom Authorization
    headers. The template's JS performs admin validation using /isAuth and
    protected admin APIs.
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
            name = clean_optional(data.get('name'), 80)
            email = clean_optional(data.get('email'), 120)
            contact_number = clean_optional(data.get('contact_number'), 20)
            address = clean_optional(data.get('address'), 200)
            bio = clean_optional(data.get('bio'), 2000)
            skills = clean_optional(data.get('skills'), 500)
            github_url = clean_optional(data.get('github_url'), 255)
            linkedin_url = clean_optional(data.get('linkedin_url'), 255)
            current_password = data.get('current_password')
            new_password = data.get('new_password')

            if new_password:
                if not current_password:
                    raise ValueError('Current password is required to change password')
                if len(str(new_password)) < 6:
                    raise ValueError('New password must be at least 6 characters')
        except ValueError as exc:
            log_api_event('/portfolio/me (PUT)', 'FAILED', str(exc), member_id)
            return jsonify({'error': str(exc)}), 400

        # Update member profile fields if provided.
        if any(value is not None for value in [name, email, contact_number, address]):
            member_record = fetch_one(
                "SELECT name, email, contact_number, address FROM members WHERE member_id = %s",
                (member_id,),
            )
            if not member_record:
                log_api_event('/portfolio/me (PUT)', 'FAILED', 'Member not found', member_id)
                return jsonify({'error': 'Member not found'}), 404

            resolved_name = name if name is not None else member_record.get('name')
            resolved_email = email if email is not None else member_record.get('email')
            resolved_contact = contact_number if contact_number is not None else member_record.get('contact_number')
            resolved_address = address if address is not None else member_record.get('address')

            if not resolved_name or not resolved_email or not resolved_contact or not resolved_address:
                log_api_event('/portfolio/me (PUT)', 'FAILED', 'Name/email/contact/address cannot be empty', member_id)
                return jsonify({'error': 'Name, email, contact number, and address cannot be empty'}), 400

            execute_write(
                """
                UPDATE members
                SET name = %s, email = %s, contact_number = %s, address = %s
                WHERE member_id = %s
                """,
                (resolved_name, resolved_email, resolved_contact, resolved_address, member_id),
                audit_context={
                    'actor_member_id': member_id,
                    'endpoint': '/portfolio/me (PUT) - members'
                }
            )

        # Change password only when explicitly requested.
        if new_password:
            credential_record = fetch_one(
                "SELECT password_hash FROM Credentials WHERE member_id = %s",
                (member_id,),
            )
            if not credential_record:
                log_api_event('/portfolio/me (PUT)', 'FAILED', 'Credentials not found', member_id)
                return jsonify({'error': 'Credentials not found'}), 404

            if not models.verify_password(str(current_password), credential_record.get('password_hash', '')):
                log_api_event('/portfolio/me (PUT)', 'FAILED', 'Current password is incorrect', member_id)
                return jsonify({'error': 'Current password is incorrect'}), 400

            execute_write(
                "UPDATE Credentials SET password_hash = %s WHERE member_id = %s",
                (models.hash_password(str(new_password)), member_id),
                audit_context={
                    'actor_member_id': member_id,
                    'endpoint': '/portfolio/me (PUT) - password'
                }
            )

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
        execute_write(
            query,
            (member_id, bio, skills, github_url, linkedin_url),
            audit_context={
                'actor_member_id': member_id,
                'endpoint': '/portfolio/me (PUT)'
            }
        )

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
        query = """
            SELECT ticket_id, title, description, member_id, location_id, category_id,
                   priority, status_id, created_at, updated_at
            FROM tickets
            WHERE member_id = %s
            ORDER BY created_at DESC, ticket_id DESC
        """
        if is_ticket_sharding_migration_complete():
            shard_idx = shard_for_member(member_id)
            shard_config = get_ticket_shard_config(shard_idx)
            tickets = fetch_all(query, (member_id,), db_config=shard_config)
        else:
            tickets = fetch_all(query, (member_id,))
        ticket_list = [_serialize_ticket(ticket) for ticket in tickets]

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
        query, params = _build_admin_ticket_filters()

        if is_ticket_sharding_migration_complete():
            tickets = []
            for _shard_idx, shard_config in all_ticket_shards():
                tickets.extend(fetch_all(query, params, db_config=shard_config))
        else:
            tickets = fetch_all(query, params)

        tickets.sort(
            key=lambda ticket: (
                ticket.get('created_at') or datetime.min,
                ticket.get('ticket_id') or 0,
            ),
            reverse=True,
        )
        ticket_list = [_serialize_ticket(ticket) for ticket in tickets]

        log_api_event('/admin/tickets', 'SUCCESS', f'Retrieved {len(ticket_list)} tickets', member_id)
        return jsonify({'tickets': ticket_list, 'count': len(ticket_list)}), 200

    except ValueError as exc:
        member_id = getattr(g, 'member_id', None)
        log_api_event('/admin/tickets', 'FAILED', str(exc), member_id)
        return jsonify({'error': str(exc)}), 400
    except Exception as e:
        member_id = getattr(g, 'member_id', None)
        log_api_event('/admin/tickets', 'ERROR', str(e), member_id)
        return jsonify({'error': 'Failed to retrieve admin tickets'}), 500


@api.route('/admin/tamper-events', methods=['GET'])
@admin_required
def get_tamper_events():
    """Get suspicious direct database writes that bypassed app/API context."""
    try:
        member_id = g.member_id

        rows = _fetch_tamper_events_for_source(
            source_name='coordinator',
            source_type='coordinator',
            db_config=None,
        )
        for _shard_idx, shard_config in all_ticket_shards():
            rows.extend(
                _fetch_tamper_events_for_source(
                    source_name=f'shard_{_shard_idx}',
                    source_type='ticket_shard',
                    db_config=shard_config,
                    shard_idx=_shard_idx,
                )
            )

        rows.sort(
            key=lambda row: (
                row.get('changed_at') or datetime.min,
                row.get('source_name') or '',
                row.get('id') or 0,
            ),
            reverse=True,
        )
        rows = rows[:TAMPER_EVENTS_RESPONSE_LIMIT]

        events = []
        for row in rows:
            events.append({
                'id': row.get('id'),
                'event_id': row.get('event_id'),
                'source_event_id': row.get('source_event_id'),
                'table_name': row.get('table_name'),
                'operation': row.get('operation'),
                'pk_value': row.get('pk_value'),
                'actor_member_id': row.get('actor_member_id'),
                'endpoint': row.get('endpoint'),
                'source': row.get('source'),
                'source_name': row.get('source_name'),
                'source_type': row.get('source_type'),
                'shard_idx': row.get('shard_idx'),
                'before_json': row.get('before_json'),
                'after_json': row.get('after_json'),
                'changed_at': str(row.get('changed_at')) if row.get('changed_at') else None
            })

        log_api_event('/admin/tamper-events', 'SUCCESS', f'Retrieved {len(events)} events', member_id)
        return jsonify({'events': events, 'count': len(events)}), 200

    except Exception as e:
        member_id = getattr(g, 'member_id', None)
        log_api_event('/admin/tamper-events', 'ERROR', str(e), member_id)
        return jsonify({'error': 'Failed to retrieve tamper events'}), 500


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
        _ensure_ticket_writes_enabled()
        data = request.get_json()
        
        if not data or 'location_id' not in data or 'category_id' not in data or 'description' not in data:
            log_api_event('/tickets (POST)', 'FAILED', 'Missing required fields', member_id)
            return jsonify({'error': 'Missing required fields: location_id, category_id, description'}), 400

        location_id = _parse_positive_int(data.get('location_id'), 'location_id')
        category_id = _parse_positive_int(data.get('category_id'), 'category_id')
        description = _normalize_required_ticket_text(data.get('description'), 'description')
        title = (
            'Maintenance Request'
            if 'title' not in data
            else _normalize_optional_ticket_title(data.get('title'))
        )
        priority = _normalize_priority(data.get('priority', 'Medium'))
        shard_idx = shard_for_member(member_id)
        shard_config = get_ticket_shard_config(shard_idx)

        _validate_ticket_create_references(member_id, location_id, category_id)

        ticket_id = allocate_ticket_id()
        insert_query = """
            INSERT INTO tickets (
                ticket_id, title, description, member_id, location_id, category_id,
                priority, status_id, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 1, NOW(), NOW())
        """
        result = execute_write(
            insert_query,
            (ticket_id, title, description, member_id, location_id, category_id, priority),
            audit_context={
                'actor_member_id': member_id,
                'endpoint': '/tickets (POST)'
            },
            db_config=shard_config,
        )

        try:
            _upsert_ticket_locator(
                ticket_id,
                member_id,
                shard_idx,
                member_id,
                '/tickets (POST) - locator',
            )
        except Exception as locator_exc:
            execute_write(
                "DELETE FROM tickets WHERE ticket_id = %s",
                (ticket_id,),
                audit_context={
                    'actor_member_id': member_id,
                    'endpoint': '/tickets (POST) - locator rollback'
                },
                db_config=shard_config,
            )
            raise RuntimeError(
                f'locator insert failed after ticket insert: {locator_exc}'
            ) from locator_exc

        if result:
            log_api_event('/tickets (POST)', 'SUCCESS', f'Created ticket', member_id)
            return jsonify({'message': 'Ticket created successfully'}), 201

        log_api_event('/tickets (POST)', 'FAILED', 'Failed to create ticket', member_id)
        return jsonify({'error': 'Failed to create ticket'}), 500

    except ValueError as exc:
        member_id = getattr(g, 'member_id', None)
        log_api_event('/tickets (POST)', 'FAILED', str(exc), member_id)
        return jsonify({'error': str(exc)}), 400
    except MigrationIncompleteError as exc:
        member_id = getattr(g, 'member_id', None)
        log_api_event('/tickets (POST)', 'FAILED', str(exc), member_id)
        return jsonify({'error': str(exc)}), 503
    except Exception as e:
        member_id = getattr(g, 'member_id', None)
        log_api_event('/tickets (POST)', 'ERROR', str(e), member_id)
        if 'locator insert failed after ticket insert' in str(e):
            return jsonify({'error': 'Failed to create ticket because ticket locator write failed'}), 500
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
        _ensure_ticket_writes_enabled()
        data = request.get_json()
        
        if not data:
            log_api_event(f'/tickets/{ticket_id} (PUT)', 'FAILED', 'No update data provided', member_id)
            return jsonify({'error': 'No data to update'}), 400

        resolved_ticket = _resolve_ticket_for_admin_action(
            ticket_id,
            member_id,
            f'/tickets/{ticket_id} (PUT)',
        )
        if not resolved_ticket:
            log_api_event(f'/tickets/{ticket_id} (PUT)', 'FAILED', 'Ticket not found in locator', member_id)
            return jsonify({'error': 'Ticket not found'}), 404

        shard_config = get_ticket_shard_config(resolved_ticket['shard_idx'])
        
        # Build dynamic update query
        allowed_fields = ['status_id', 'description', 'priority', 'title']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                if field == 'status_id':
                    status_id = _parse_positive_int(data[field], 'status_id')
                    if not status_exists(status_id):
                        log_api_event(f'/tickets/{ticket_id} (PUT)', 'FAILED', 'status_id does not exist', member_id)
                        return jsonify({'error': 'status_id does not exist'}), 400
                    values.append(status_id)
                elif field == 'priority':
                    values.append(_normalize_priority(data[field]))
                else:
                    values.append(_normalize_required_ticket_text(data[field], field))
                updates.append(f"{field} = %s")
        
        if not updates:
            log_api_event(f'/tickets/{ticket_id} (PUT)', 'FAILED', 'No valid fields to update', member_id)
            return jsonify({'error': 'No valid fields to update'}), 400
        
        values.append(ticket_id)
        query = f"UPDATE tickets SET {', '.join(updates)}, updated_at = NOW() WHERE ticket_id = %s"
        
        updated_rows = execute_write(
            query,
            tuple(values),
            audit_context={
                'actor_member_id': member_id,
                'endpoint': f'/tickets/{ticket_id} (PUT)'
            },
            db_config=shard_config,
        )
        if not updated_rows:
            existing_ticket = fetch_one(
                "SELECT ticket_id FROM tickets WHERE ticket_id = %s",
                (ticket_id,),
                db_config=shard_config,
            )
            if not existing_ticket:
                execute_write(
                    "DELETE FROM ticket_locator WHERE ticket_id = %s",
                    (ticket_id,),
                    audit_context={
                        'actor_member_id': member_id,
                        'endpoint': f'/tickets/{ticket_id} (PUT) - stale locator cleanup',
                    },
                )
                log_api_event(
                    f'/tickets/{ticket_id} (PUT)',
                    'FAILED',
                    'Ticket disappeared before update completed',
                    member_id,
                )
                return jsonify({'error': 'Ticket not found'}), 404
        log_api_event(f'/tickets/{ticket_id} (PUT)', 'SUCCESS', 'Ticket updated', member_id)
        return jsonify({'message': 'Ticket updated successfully'}), 200

    except ValueError as exc:
        member_id = getattr(g, 'member_id', None)
        log_api_event(f'/tickets/{ticket_id} (PUT)', 'FAILED', str(exc), member_id)
        return jsonify({'error': str(exc)}), 400
    except TicketIntegrityError as exc:
        member_id = getattr(g, 'member_id', None)
        log_api_event(f'/tickets/{ticket_id} (PUT)', 'FAILED', str(exc), member_id)
        return jsonify({'error': str(exc)}), 409
    except TicketRepairUnavailableError as exc:
        member_id = getattr(g, 'member_id', None)
        log_api_event(f'/tickets/{ticket_id} (PUT)', 'FAILED', str(exc), member_id)
        return jsonify({'error': str(exc)}), 503
    except MigrationIncompleteError as exc:
        member_id = getattr(g, 'member_id', None)
        log_api_event(f'/tickets/{ticket_id} (PUT)', 'FAILED', str(exc), member_id)
        return jsonify({'error': str(exc)}), 503
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
        _ensure_ticket_writes_enabled()
        resolved_ticket = _resolve_ticket_for_admin_action(
            ticket_id,
            member_id,
            f'/tickets/{ticket_id} (DELETE)',
        )
        if not resolved_ticket:
            log_api_event(f'/tickets/{ticket_id} (DELETE)', 'FAILED', 'Ticket not found in locator', member_id)
            return jsonify({'error': 'Ticket not found'}), 404

        shard_config = get_ticket_shard_config(resolved_ticket['shard_idx'])
        execute_write(
            "DELETE FROM ticket_locator WHERE ticket_id = %s",
            (ticket_id,),
            audit_context={
                'actor_member_id': member_id,
                'endpoint': f'/tickets/{ticket_id} (DELETE) - locator'
            },
        )
        try:
            deleted_rows = execute_write(
                "DELETE FROM tickets WHERE ticket_id = %s",
                (ticket_id,),
                audit_context={
                    'actor_member_id': member_id,
                    'endpoint': f'/tickets/{ticket_id} (DELETE)'
                },
                db_config=shard_config,
            )
            if not deleted_rows:
                log_api_event(
                    f'/tickets/{ticket_id} (DELETE)',
                    'FAILED',
                    'Ticket disappeared before delete completed',
                    member_id,
                )
                return jsonify({'error': 'Ticket not found'}), 404
        except Exception as shard_exc:
            _upsert_ticket_locator(
                ticket_id,
                resolved_ticket['member_id'],
                resolved_ticket['shard_idx'],
                member_id,
                f'/tickets/{ticket_id} (DELETE) - locator restore',
            )
            raise RuntimeError(
                f'shard delete failed after locator delete; locator restored: {shard_exc}'
            ) from shard_exc
        
        log_api_event(f'/tickets/{ticket_id} (DELETE)', 'SUCCESS', 'Ticket deleted', member_id)
        return jsonify({'message': 'Ticket deleted successfully'}), 200
    
    except TicketIntegrityError as exc:
        member_id = getattr(g, 'member_id', None)
        log_api_event(f'/tickets/{ticket_id} (DELETE)', 'FAILED', str(exc), member_id)
        return jsonify({'error': str(exc)}), 409
    except TicketRepairUnavailableError as exc:
        member_id = getattr(g, 'member_id', None)
        log_api_event(f'/tickets/{ticket_id} (DELETE)', 'FAILED', str(exc), member_id)
        return jsonify({'error': str(exc)}), 503
    except MigrationIncompleteError as exc:
        member_id = getattr(g, 'member_id', None)
        log_api_event(f'/tickets/{ticket_id} (DELETE)', 'FAILED', str(exc), member_id)
        return jsonify({'error': str(exc)}), 503
    except Exception as e:
        member_id = getattr(g, 'member_id', None)
        log_api_event(f'/tickets/{ticket_id} (DELETE)', 'ERROR', str(e), member_id)
        return jsonify({'error': 'Failed to delete ticket'}), 500
