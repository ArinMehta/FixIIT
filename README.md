# FixIIT – Campus Maintenance Management System

### CS 432: Databases (Course Project - Track 1)
**Semester II (2025–2026) | Instructor: Dr. Yogesh K. Meena**

---

## Team Members

| Name | Roll Number |
| :--- | :--- |
| **Abhitej Singh Bhullar** | 23110009 |
| **Shiv Patel** | 23110302 |
| **Shivansh Shukla** | 23110303 |
| **Soham Shrivastava** | 23110315 |
| **Arin Mehta** | 23110038 |

---

## Project Overview

**FixIIT** is a robust, database-driven software system designed to streamline maintenance requests across the IIT Gandhinagar campus. It serves as a centralized portal for reporting issues, assigning technicians, and tracking resolution progress.

### Key Features:
* **Ticket Management:** Members can raise tickets for various categories (Electrical, Plumbing, IT, etc.).
* **Role-Based Access:** Distinct roles for Students, Faculty, Technicians, and Admins.
* **Workflow Automation:** Supervisors can assign tickets to specific technicians with instructions.
* **Feedback Loop:** Users can rate completed services and provide feedback.
* **Communication:** Integrated commenting system for updates on specific tickets.

---

## Codebase Structure

* **`Track1_Assignment1_ModuleA.sql`**: The complete SQL dump containing:
    * Table definitions (DDL) for all 10 entities.
    * Enforced constraints (Foreign Keys, Checks, Unique).
    * Sample data population (30+ rows per table).
* **`Project_Report.pdf`**: The combined Module A & B report containing Schema details, ER Diagrams, and Normalization analysis.

---

## Technical Details

* **Database System:** MySQL
* **SQL Mode:** Strict Mode enabled (`STRICT_TRANS_TABLES`, `ONLY_FULL_GROUP_BY`, etc.) to ensure data integrity.
* **Normalization:** Schema designed to adhere to **3NF** (Third Normal Form).
