SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,ONLY_FULL_GROUP_BY';

CREATE DATABASE IF NOT EXISTS fixiit_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;
USE fixiit_db;

DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS ticket_comments;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS member_roles;
DROP TABLE IF EXISTS members;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS statuses;
DROP TABLE IF EXISTS roles;

CREATE TABLE roles (
  role_id INT AUTO_INCREMENT PRIMARY KEY,
  role_name VARCHAR(50) NOT NULL,
  role_code VARCHAR(30) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (role_name),
  UNIQUE (role_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE statuses (
  status_id INT AUTO_INCREMENT PRIMARY KEY,
  status_name VARCHAR(30) NOT NULL,
  is_closed TINYINT(1) NOT NULL,
  sort_order INT NOT NULL,
  UNIQUE (status_name),
  CHECK (is_closed IN (0,1)),
  CHECK (sort_order > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE categories (
  category_id INT AUTO_INCREMENT PRIMARY KEY,
  category_name VARCHAR(50) NOT NULL,
  sla_hours INT NOT NULL,
  is_active TINYINT(1) NOT NULL,
  UNIQUE (category_name),
  CHECK (sla_hours > 0),
  CHECK (is_active IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE locations (
  location_id INT AUTO_INCREMENT PRIMARY KEY,
  building_name VARCHAR(80) NOT NULL,
  floor_number INT NOT NULL,
  room_number VARCHAR(20) NOT NULL,
  type VARCHAR(30) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (building_name, floor_number, room_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE members (
  member_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL,
  image VARCHAR(255) NOT NULL,
  age INT NOT NULL,
  email VARCHAR(120) NOT NULL,
  contact_number VARCHAR(20) NOT NULL,
  address VARCHAR(200) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (email),
  CHECK (age > 16)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE member_roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  member_id INT NOT NULL,
  role_id INT NOT NULL,
  assigned_date DATE NOT NULL,
  assigned_by_member_id INT NOT NULL,
  UNIQUE (member_id, role_id),
  CONSTRAINT fk_member_roles_member
    FOREIGN KEY (member_id) REFERENCES members(member_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_member_roles_role
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_member_roles_assigned_by
    FOREIGN KEY (assigned_by_member_id) REFERENCES members(member_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE tickets (
  ticket_id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(120) NOT NULL,
  description TEXT NOT NULL,
  member_id INT NOT NULL,
  location_id INT NOT NULL,
  category_id INT NOT NULL,
  priority VARCHAR(20) NOT NULL,
  status_id INT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT chk_ticket_priority
    CHECK (priority IN ('Low','Medium','High','Urgent','Emergency')),

  CHECK (created_at <= updated_at),

  CONSTRAINT fk_tickets_member
    FOREIGN KEY (member_id) REFERENCES members(member_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_tickets_location
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_tickets_category
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_tickets_status
    FOREIGN KEY (status_id) REFERENCES statuses(status_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE assignments (
  assignment_id INT AUTO_INCREMENT PRIMARY KEY,
  ticket_id INT NOT NULL,
  technician_member_id INT NOT NULL,
  assigned_by INT NOT NULL,
  assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  instructions VARCHAR(255) NOT NULL,
  UNIQUE (ticket_id),
  CONSTRAINT fk_assignments_ticket
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_assignments_technician
    FOREIGN KEY (technician_member_id) REFERENCES members(member_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_assignments_assigned_by
    FOREIGN KEY (assigned_by) REFERENCES members(member_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE ticket_comments (
  ticket_id INT NOT NULL,                
  comment_seq INT NOT NULL,              
  member_id INT NOT NULL,
  comment_text VARCHAR(255) NOT NULL,
  commented_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  PRIMARY KEY (ticket_id, comment_seq),

  CONSTRAINT fk_ticket_comments_ticket
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
    
  CONSTRAINT fk_ticket_comments_member
    FOREIGN KEY (member_id) REFERENCES members(member_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE feedback (
  feedback_id INT AUTO_INCREMENT PRIMARY KEY,
  ticket_id INT NOT NULL,
  rating INT NOT NULL,
  comment VARCHAR(255) NOT NULL,
  submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  submitted_by_member_id INT NOT NULL,
  UNIQUE (ticket_id),
  CHECK (rating BETWEEN 1 AND 5),
  CONSTRAINT fk_feedback_ticket
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_feedback_submitted_by
    FOREIGN KEY (submitted_by_member_id) REFERENCES members(member_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO roles (role_name, role_code) VALUES
('Admin', 'ADMIN'),
('Supervisor', 'SUPERVISOR'),
('Fire & Safety Officer', 'FIRE_SAFETY'),
('AC Technician', 'AC_TECH'),
('Electrician', 'ELECTRIC'),
('Plumber', 'PLUMB'),
('IT Support', 'IT_SUPPORT'),
('Carpenter', 'CARP'),
('Civil Maintenance', 'CIVIL'),
('Housekeeping', 'HOUSE'),
('Pest Control', 'PEST');

INSERT INTO statuses (status_name, is_closed, sort_order) VALUES
('Open', 0, 1),
('Assigned', 0, 2),
('In_Progress', 0, 3),
('On_Hold', 0, 4),
('Closed', 1, 5),
('Resolved', 1, 6),
('Cancelled', 1, 7),
('Reopened', 0, 8),
('Waiting_Parts', 0, 9),
('Scheduled', 0, 10);

INSERT INTO categories (category_name, sla_hours, is_active) VALUES
('Electrical', 24, 1),
('Plumbing', 24, 1),
('Air Conditioning', 48, 1),
('Carpentry', 72, 1),
('IT Support', 24, 1),
('Housekeeping', 12, 1),
('General Maintenance', 48, 1),
('Pest Control', 72, 1),
('Fire & Safety', 24, 1),
('Civil Maintenance', 96, 1);

INSERT INTO locations (building_name, floor_number, room_number, type) VALUES
('Academic Block 7', 1, 'AB7/201', 'Classroom'), 
('Academic Block 4', 2, 'AB4/305', 'Laboratory'),
('Academic Block 6', 1, 'AB6/106', 'Workshop'),
('Academic Block 10', 0, 'AB10/104', 'Lab'),
('Library', 1, 'L205', 'Conference Room 1'),
('Library', 1, 'L201', 'Reading Area'),
('Academic Block 3', 0, 'AB3/102', 'Student Affairs Office'),
('Hostel Jurqia', 1, 'J231W', 'Washroom'),
('Hostel Kyzeel', 2, 'K335', 'Common Room'),
('2D Cafe', 1, 'AB1', 'Outlet'),
('Sports Complex', 1, 'S05', 'Gym'),
('Central Arcade', 1, 'CA201W', 'Washroom'),
('Hostel Jurqia', 2, 'J337', 'Room');

INSERT INTO members (name, image, age, email, contact_number, address) VALUES
('Prof. XYZ', 'prof_xyz.jpg', 37, 'prof.xyz@iitgn.ac.in', '+91 9123456789', 'AB 3/302A'),
('Shiv Patel', 'shiv.jpg', 20, 'shiv.patel@iitgn.ac.in', '+91 8123406789', 'J307'),
('Prof. ABC', 'prof_abc.jpg', 42, 'prof.abc@iitgn.ac.in', '+91 7123456190', 'AB 5/301A'),
('Shivansh', 'shivansh.jpg', 21, 'shivansh@iitgn.ac.in', '+91 6123456729', 'J235'),
('Abhishek', 'abhishek.jpg', 20, 'abhishek@iitgn.ac.in', '+91 9123456739', 'L105'),
('Farhan Obaid', 'farhan.jpg', 22, 'farhan.obaid@iitgn.ac.in', '+91 9123456749', 'J236'),
('Student A', 'student_a.jpg', 24, 'student.a@iitgn.ac.in', '+91 9123456759', 'A123'),
('Arin Mehta', 'arin.jpg', 20, 'arin.mehta@iitgn.ac.in', '+91 9123456788', 'J235'),
('Soham', 'soham.jpg', 20, 'soham@iitgn.ac.in', '+91 9123456769', 'Library Conference Room 1'),
('Abhinav', 'abhinav.jpg', 21, 'abhinav@iitgn.ac.in', '+91 9123056739', 'L115'),
('Student B', 'student_b.jpg', 23, 'student.b@iitgn.ac.in', '+91 9123456791', 'K431'),
('Attendant A', 'attendant_a.jpg', 33, 'library.attendant.a@iitgn.ac.in', '+91 9123456792', 'Library, Office 2'),
('Jiya', 'jiya.jpg', 26, 'jiya@iitgn.ac.in', '+91 9123456793', 'I344'),
('Dilip Singh', 'dilip.jpg', 24, 'dilip.singh@iitgn.ac.in', '+91 9123456794', 'Sports Complex, Gym'),
('Attendant B', 'attendant_b.jpg', 27, 'library.attendant.b@iitgn.ac.in', '+91 9123456795', 'Library, Office 3'),
('Dean, SA', 'dean_sa.jpg', 28, 'dean.sa@iitgn.ac.in', '+91 9123456796', 'AB 3/102'),
('Electrician A', 'electrician_a.jpg', 32, 'electrician.a@fixiit.iitgn.ac.in', '+91 9000000001', 'IITGN Maintenance Office'),
('Electrician B', 'electrician_b.jpg', 29, 'electrician.b@fixiit.iitgn.ac.in', '+91 9000000002', 'IITGN Maintenance Office'),
('Plumber A', 'plumber_a.jpg', 35, 'plumber.a@fixiit.iitgn.ac.in', '+91 9000000003', 'IITGN Maintenance Office'),
('Plumber B', 'plumber_b.jpg', 31, 'plumber.b@fixiit.iitgn.ac.in', '+91 9000000004', 'IITGN Maintenance Office'),
('AC Technician A', 'ac_tech_a.jpg', 30, 'ac.tech.a@fixiit.iitgn.ac.in', '+91 9000000005', 'IITGN Maintenance Office'),
('IT Support A', 'it_support_a.jpg', 27, 'it.support.a@fixiit.iitgn.ac.in', '+91 9000000006', 'IITGN IT Helpdesk'),
('Carpenter A', 'carpenter_a.jpg', 38, 'carpenter.a@fixiit.iitgn.ac.in', '+91 9000000007', 'IITGN Maintenance Office'),
('Housekeeping A', 'housekeeping_a.jpg', 33, 'housekeeping.a@fixiit.iitgn.ac.in', '+91 9000000008', 'IITGN Housekeeping Office'),
('Civil Technician A', 'civil_tech_a.jpg', 36, 'civil.tech.a@fixiit.iitgn.ac.in', '+91 9000000009', 'IITGN Maintenance Office'),
('Fire & Safety Officer A', 'fire_safety_a.jpg', 34, 'fire.safety.a@fixiit.iitgn.ac.in', '+91 9000000010', 'IITGN Safety Office'),
('Pest Control A', 'pest_control_a.jpg', 31, 'pest.control.a@fixiit.iitgn.ac.in', '+91 9000000011', 'IITGN Maintenance Office'),
('Hostel Office', 'hostel_office.jpg', 40, 'hostel.office@fixiit.iitgn.ac.in', '+91 9000000012', 'Hostel Administration Office'),
('Hostel Caretaker', 'hostel_caretaker.jpg', 45, 'hostel.caretaker@fixiit.iitgn.ac.in', '+91 9000000013', 'Hostel Administration Office');

INSERT INTO member_roles (member_id, role_id, assigned_date, assigned_by_member_id) VALUES
(28, 1, '2025-08-01', 28),
(29, 2, '2025-08-01', 28),  
(26, 3, '2025-08-02', 29),  
(21, 4, '2025-08-02', 29),  
(17, 5, '2025-08-02', 29),  
(18, 5, '2025-08-02', 29),  
(19, 6, '2025-08-02', 29),  
(20, 6, '2025-08-02', 29),  
(22, 7, '2025-08-02', 29),  
(23, 8, '2025-08-02', 29),  
(25, 9, '2025-08-02', 29),  
(24, 10, '2025-08-02', 29), 
(27, 11, '2025-08-02', 29); 

INSERT INTO tickets
(title, description, member_id, location_id, category_id, priority, status_id, created_at, updated_at) VALUES
('Projector not working', 'Projector in classroom flickers and shuts down.', 3, 1, 1, 'Medium', 5, '2026-01-10 09:00:00', '2026-01-10 09:00:00'),
('Leaky faucet in Hostel Jurqia', 'Faucet in bathroom needs repair.', 8, 8, 2, 'High', 5, '2026-01-11 08:30:00', '2026-01-11 08:45:00'),
('Broken window latch', 'Window latch is broken and will not lock.', 15, 9, 10, 'Medium', 5, '2026-01-12 10:15:00', '2026-01-12 10:15:00'),
('WiFi not working in library', 'No connectivity in conference room 1.', 9, 5, 5, 'Urgent', 5, '2026-01-13 14:20:00', '2026-01-13 14:20:00'),
('Gym locker jammed', 'Locker door stuck and cannot open.', 14, 11, 4, 'Urgent', 5, '2026-01-14 16:05:00', '2026-01-14 16:05:00'),
('AC not working in Lab', 'Lab AC unit not cooling effectively.', 4, 2, 3, 'High', 5, '2026-01-15 09:10:00', '2026-01-15 11:00:00'),
('Power outlet sparks', 'Outlet near workshop sparks when used.', 5, 3, 1, 'Emergency', 2, '2026-01-15 12:30:00', '2026-01-15 13:00:00'),
('Clogged drain in cafeteria', 'Kitchen drain is clogged and backing up.', 10, 10, 2, 'High', 2, '2026-01-16 07:45:00', '2026-01-16 09:00:00'),
('Network switch reboot loop', 'Switch in lab keeps rebooting.', 9, 4, 5, 'Urgent', 2, '2026-01-16 10:20:00', '2026-01-16 11:10:00'),
('Broken chair in classroom', 'Classroom chair leg snapped.', 7, 1, 4, 'Medium', 2, '2026-01-17 08:05:00', '2026-01-17 08:30:00'),
('Ceiling fan noise', 'Fan makes loud noise at high speed.', 6, 7, 1, 'Medium', 3, '2026-01-18 09:40:00', '2026-01-19 10:00:00'),
('Water geyser issue', 'Hot water not available in Jurqia.', 8, 8, 2, 'Emergency', 3, '2026-01-19 07:15:00', '2026-01-20 12:00:00'),
('Desk repair in library', 'Study desk has broken edge.', 12, 6, 4, 'Low', 3, '2026-01-20 13:00:00', '2026-01-21 09:30:00'),
('Floor cleaning spill', 'Spill needs deep cleaning and polish.', 11, 10, 6, 'Urgent', 3, '2026-01-21 18:10:00', '2026-01-22 08:00:00'),
('Replace lab UPS battery', 'UPS battery for lab equipment is failing.', 13, 2, 1, 'High', 4, '2026-01-22 10:50:00', '2026-01-23 11:00:00'),
('Security camera offline', 'Camera near AB3 entrance is offline.', 16, 7, 5, 'Urgent', 4, '2026-01-23 15:05:00', '2026-01-24 10:30:00'),
('AC water leakage', 'Water leaking from AC unit in Jurqia.', 4, 13, 3, 'High', 5, '2026-01-05 09:00:00', '2026-01-06 16:00:00'),
('Broken door handle', 'Door handle on common room is loose.', 11, 9, 10, 'Low', 5, '2026-01-06 11:00:00', '2026-01-07 14:30:00'),
('WiFi not discoverable', 'WiFi network not visible in Library.', 12, 6, 5, 'Medium', 5, '2026-01-07 08:00:00', '2026-01-07 17:00:00'),
('Washroom odor issue', 'Persistent odor in washroom area.', 10, 12, 6, 'Medium', 5, '2026-01-08 07:45:00', '2026-01-08 12:00:00');

INSERT INTO assignments
(ticket_id, technician_member_id, assigned_by, assigned_at, instructions) VALUES
(7, 17, 28, '2026-01-15 13:05:00', 'Inspect wiring and replace damaged outlet.'),          -- Electrical -> Electrician A
(8, 19, 29, '2026-01-16 09:10:00', 'Clear blockage and test drainage flow.'),              -- Plumbing -> Plumber A
(9, 22, 29, '2026-01-16 11:15:00', 'Diagnose switch loop and apply firmware update.'),     -- IT -> IT Support A
(10, 23, 29, '2026-01-17 08:35:00', 'Repair chair frame and reinforce joints.'),           -- Carpentry -> Carpenter A
(11, 17, 29, '2026-01-18 10:00:00', 'Inspect fan mounts and balance blades.'),             -- Electrical -> Electrician A
(12, 19, 28, '2026-01-19 08:00:00', 'Check heater coils and replace thermostat.'),         -- Plumbing -> Plumber A (geyser)
(13, 23, 29, '2026-01-20 13:30:00', 'Sand and refinish desk edge.'),                       -- Carpentry -> Carpenter A
(14, 24, 29, '2026-01-21 18:20:00', 'Deep clean and apply floor polish.'),                 -- Housekeeping -> Housekeeping A
(15, 17, 29, '2026-01-22 11:10:00', 'Source compatible battery and schedule swap.'),       -- Electrical -> Electrician A (UPS)
(16, 22, 29, '2026-01-23 15:15:00', 'Verify power, reset camera, and check network.');     -- IT -> IT Support A


INSERT INTO ticket_comments (ticket_id, comment_seq, member_id, comment_text, commented_at) VALUES
-- Ticket 1 (Projector)
(1, 1, 3,  'Ticket raised: Projector flickers and shuts down.', '2026-01-10 09:00:00'),
(1, 2, 29, 'Acknowledged. Logged and routed to the relevant team.', '2026-01-10 09:10:00'),
(1, 3, 29, 'Update: Issue verified during inspection; resolved.', '2026-01-10 12:30:00'),

-- Ticket 2 (Leaky Faucet)
(2, 1, 8,  'Ticket raised: Leaky faucet needs repair.', '2026-01-11 10:30:00'),
(2, 2, 29, 'Acknowledged. Scheduled for maintenance round.', '2026-01-11 10:40:00'),
(2, 3, 29, 'Update: Repair completed and leakage stopped.', '2026-01-11 13:20:00'),

-- Ticket 3 (Window Latch)
(3, 1, 15, 'Ticket raised: Window latch broken and won’t lock.', '2026-01-12 08:15:00'),
(3, 2, 29, 'Acknowledged. Added to carpentry queue.', '2026-01-12 08:25:00'),
(3, 3, 29, 'Update: Latch replaced/adjusted. Ticket closed.', '2026-01-12 15:10:00'),

-- Ticket 4 (WiFi)
(4, 1, 9,  'Ticket raised: No WiFi connectivity in conference room.', '2026-01-13 14:20:00'),
(4, 2, 29, 'Acknowledged. Network team informed.', '2026-01-13 14:30:00'),
(4, 3, 29, 'Update: Access point rebooted and connectivity restored.', '2026-01-13 18:00:00'),

-- Ticket 5 (Gym Locker)
(5, 1, 14, 'Ticket raised: Gym locker door stuck and cannot open.', '2026-01-14 16:00:00'),
(5, 2, 29, 'Acknowledged. Scheduled for inspection.', '2026-01-14 16:10:00'),
(5, 3, 29, 'Update: Lock mechanism adjusted and locker operational.', '2026-01-14 17:20:00'),

-- Ticket 6 (Lab AC)
(6, 1, 4,  'Ticket raised: Lab AC not cooling effectively.', '2026-01-15 11:05:00'),
(6, 2, 29, 'Acknowledged. Logged for AC technician visit.', '2026-01-15 11:15:00'),
(6, 3, 29, 'Update: Cooling restored after checks.', '2026-01-15 16:00:00'),

-- Ticket 7 (Sparks)
(7, 1, 5,  'Ticket raised: Power outlet sparks when used.', '2026-01-16 09:40:00'),
(7, 2, 29, 'Acknowledged. Assigned to Electrician.', '2026-01-16 09:45:00'),
(7, 3, 17, 'Update: Inspected outlet; isolating circuit and replacing.', '2026-01-16 10:30:00'),

-- Ticket 8 (Clogged Drain)
(8, 1, 10, 'Ticket raised: Kitchen drain clogged and backing up.', '2026-01-17 13:10:00'),
(8, 2, 29, 'Acknowledged. Assigned to Plumber.', '2026-01-17 13:15:00'),
(8, 3, 19, 'Update: Clearing blockage and testing flow.', '2026-01-17 14:20:00'),

-- Ticket 9 (Switch Reboot)
(9, 1, 9,  'Ticket raised: Network switch keeps rebooting.', '2026-01-18 18:30:00'),
(9, 2, 29, 'Acknowledged. Assigned to IT Support.', '2026-01-18 18:35:00'),
(9, 3, 22, 'Update: Checking logs and applying stable configuration.', '2026-01-18 19:10:00'),

-- Ticket 10 (Broken Chair)
(10, 1, 7,  'Ticket raised: Classroom chair leg snapped.', '2026-01-19 07:50:00'),
(10, 2, 29, 'Acknowledged. Assigned to Carpenter.', '2026-01-19 08:00:00'),
(10, 3, 23, 'Update: Repairing chair frame and reinforcing joints.', '2026-01-19 09:00:00');

INSERT INTO feedback
(ticket_id, rating, comment, submitted_by_member_id, submitted_at) VALUES
(17, 5, 'Cooling restored quickly.', 4, '2026-01-06 17:00:00'),
(18, 4, 'Handle replaced and door works.', 11, '2026-01-07 15:00:00'),
(19, 5, 'Network stable after update.', 12, '2026-01-07 18:00:00'),
(20, 3, 'Odor reduced, need follow-up.', 10, '2026-01-08 12:30:00'),
(1, 4, 'Projector repaired successfully.', 3, '2026-01-11 10:00:00'),
(2, 5, 'Faucet fixed quickly.', 8, '2026-01-11 09:30:00'),
(3, 4, 'Window latch replaced.', 15, '2026-01-12 15:00:00'),
(4, 5, 'WiFi restored in reading room.', 9, '2026-01-13 18:00:00'),
(5, 3, 'Locker repaired but slightly tight.', 14, '2026-01-14 17:00:00'),
(6, 5, 'AC cooling properly now.', 4, '2026-01-15 16:00:00');

SELECT 'roles' AS table_name, COUNT(*) AS row_count FROM roles;
SELECT 'ticket_comments' AS table_name, COUNT(*) AS row_count FROM ticket_comments;
SELECT 'statuses' AS table_name, COUNT(*) AS row_count FROM statuses;
SELECT 'categories' AS table_name, COUNT(*) AS row_count FROM categories;
SELECT 'locations' AS table_name, COUNT(*) AS row_count FROM locations;
SELECT 'members' AS table_name, COUNT(*) AS row_count FROM members;
SELECT 'member_roles' AS table_name, COUNT(*) AS row_count FROM member_roles;
SELECT 'tickets' AS table_name, COUNT(*) AS row_count FROM tickets;
SELECT 'assignments' AS table_name, COUNT(*) AS row_count FROM assignments;
SELECT 'feedback' AS table_name, COUNT(*) AS row_count FROM feedback;

SELECT
  t.ticket_id,
  t.title,
  m.name AS member_name,
  l.building_name,
  l.room_number,
  c.category_name,
  t.priority,
  s.status_name
FROM tickets t
JOIN members m ON t.member_id = m.member_id
JOIN locations l ON t.location_id = l.location_id
JOIN categories c ON t.category_id = c.category_id
JOIN statuses s ON t.status_id = s.status_id
ORDER BY t.ticket_id;

SELECT
  a.assignment_id,
  t.ticket_id,
  t.title,
  s.status_name,
  tech.name AS technician_name,
  mgr.name AS assigned_by_name
FROM assignments a
JOIN tickets t ON a.ticket_id = t.ticket_id
JOIN statuses s ON t.status_id = s.status_id
JOIN members tech ON a.technician_member_id = tech.member_id
JOIN members mgr ON a.assigned_by = mgr.member_id
ORDER BY a.assignment_id;

SELECT
  f.feedback_id,
  t.ticket_id,
  t.title,
  s.status_name,
  f.rating,
  f.comment,
  m.name AS submitted_by
FROM feedback f
JOIN tickets t ON f.ticket_id = t.ticket_id
JOIN statuses s ON t.status_id = s.status_id
JOIN members m ON f.submitted_by_member_id = m.member_id
ORDER BY f.feedback_id;


