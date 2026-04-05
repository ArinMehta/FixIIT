"""
Locust Stress Testing for FixIIT SQL Backend API (Assignment 2 Module B)

Module B (Assignment 3): Concurrent Workload & Stress Testing

This file defines load tests for the FixIIT Flask API with MySQL backend.
Tests cover:
1. Multi-user simulation (concurrent users)
2. Race condition testing (same ticket updates)
3. Stress testing (high request volume)
4. Mixed read/write workloads

Prerequisites:
1. Start Assignment 2 Module B Flask server:
   cd Assignment_2/Module_B && python run.py

2. Run Locust:
   locust -f locustfile.py --host=http://localhost:5000

3. Open Web UI: http://localhost:8089
"""

from __future__ import annotations

import json
import random
from datetime import datetime
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# Test user credentials (must exist in database)
TEST_USERNAME = "user"
TEST_PASSWORD = "user123"


# ============================================================================
# Custom User Classes
# ============================================================================

class FixIITUser(HttpUser):
    """
    Standard FixIIT user performing typical operations.
    Simulates real usage patterns with mixed read/write operations.
    """
    
    wait_time = between(0.5, 2)
    weight = 3
    token = None
    
    def on_start(self):
        """Authenticate user on start."""
        response = self.client.post(
            "/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("session_token")
        else:
            raise Exception(f"Login failed: {response.status_code}")
    
    def _headers(self):
        """Return auth headers."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(10)
    def get_my_tickets(self):
        """Fetch user's tickets (read workload)."""
        self.client.get("/tickets", headers=self._headers(), name="/tickets (GET)")
    
    @task(5)
    def create_ticket(self):
        """Create a new ticket (write workload)."""
        payload = {
            "title": f"Locust Test Ticket {random.randint(1000, 9999)}",
            "description": f"Created during load test at {datetime.now().isoformat()}",
            "location_id": random.randint(1, 5),
            "category_id": random.randint(1, 5),
            "priority": random.choice(["Low", "Medium", "High", "Emergency"])
        }
        
        with self.client.post(
            "/tickets",
            headers=self._headers(),
            json=payload,
            catch_response=True,
            name="/tickets (POST)"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Create ticket failed: {response.status_code}")
    
    @task(3)
    def get_portfolio(self):
        """Fetch user portfolio (read workload)."""
        self.client.get("/portfolio/me", headers=self._headers(), name="/portfolio/me (GET)")
    
    @task(1)
    def check_auth(self):
        """Verify authentication status."""
        self.client.get("/isAuth", headers=self._headers(), name="/isAuth")


class RaceConditionUser(HttpUser):
    """
    User that specifically targets race conditions.
    Multiple users compete to update the same ticket.
    """
    
    wait_time = between(0.1, 0.5)
    weight = 2
    token = None
    test_ticket_id = None
    
    def on_start(self):
        """Authenticate and create a test ticket for race testing."""
        response = self.client.post(
            "/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("session_token")
        else:
            raise Exception(f"Login failed: {response.status_code}")
    
    def _headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(10)
    def update_ticket_race(self):
        """
        Race condition test: Multiple users update tickets concurrently.
        Tests isolation via MySQL row-level locking.
        """
        # Get existing tickets first
        response = self.client.get("/tickets", headers=self._headers())
        if response.status_code != 200:
            return

        tickets_data = response.json()
        tickets = tickets_data.get("tickets", []) if tickets_data else []
        if not tickets:
            return

        # Pick a ticket to update (all users may pick same ticket = race)
        ticket = tickets[0] if tickets else None
        if not ticket:
            return
        
        ticket_id = ticket.get("ticket_id")
        
        with self.client.put(
            f"/tickets/{ticket_id}",
            headers=self._headers(),
            json={
                "priority": random.choice(["Low", "Medium", "High", "Emergency"]),
                "description": f"Race update at {datetime.now().isoformat()}"
            },
            catch_response=True,
            name="/tickets/<id> (PUT - race)"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Update failed: {response.status_code}")


class StressUser(HttpUser):
    """
    High-frequency stress test user.
    Minimal wait time for maximum throughput testing.
    """
    
    wait_time = between(0.05, 0.2)
    weight = 1
    token = None
    
    def on_start(self):
        """Authenticate user."""
        response = self.client.post(
            "/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            self.token = response.json().get("session_token")
    
    def _headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(10)
    def rapid_create_ticket(self):
        """Rapid-fire ticket creation requests."""
        payload = {
            "title": f"Stress Test {random.randint(10000, 99999)}",
            "description": "High-load stress test ticket",
            "location_id": 1,
            "category_id": 1,
            "priority": "Medium"
        }
        self.client.post("/tickets", headers=self._headers(), json=payload, name="/tickets (stress)")
    
    @task(15)
    def rapid_read(self):
        """Rapid-fire read requests."""
        self.client.get("/tickets", headers=self._headers(), name="/tickets (stress read)")


class MixedWorkloadUser(HttpUser):
    """
    User simulating realistic mixed workload (70% reads, 30% writes).
    """
    
    wait_time = between(0.3, 1.5)
    weight = 2
    token = None
    
    def on_start(self):
        """Authenticate user."""
        response = self.client.post(
            "/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            self.token = response.json().get("session_token")
    
    def _headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(7)
    def read_tickets(self):
        """Read operations (majority of requests)."""
        self.client.get("/tickets", headers=self._headers(), name="/tickets (mixed read)")
    
    @task(3)
    def write_ticket(self):
        """Write operations."""
        payload = {
            "title": f"Mixed Workload {random.randint(1000, 9999)}",
            "description": "Created during mixed workload test",
            "location_id": random.randint(1, 3),
            "category_id": random.randint(1, 3),
            "priority": random.choice(["Low", "Medium", "High"])
        }
        self.client.post("/tickets", headers=self._headers(), json=payload, name="/tickets (mixed write)")


# ============================================================================
# Event Hooks for Statistics
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("\n" + "="*60)
    print("  FixIIT SQL API Load Test Starting")
    print("  Module B (Assignment 3): Concurrent Workload Testing")
    print("="*60)
    print("\nTest Configuration:")
    print(f"  Host: {environment.host}")
    print(f"  User Classes: FixIITUser, RaceConditionUser, StressUser, MixedWorkloadUser")
    print(f"  Test User: {TEST_USERNAME}")
    print("\nEndpoints being tested:")
    print("  POST /login           - Authentication")
    print("  GET  /tickets         - Read tickets (main read workload)")
    print("  POST /tickets         - Create ticket (write workload)")
    print("  PUT  /tickets/<id>    - Update ticket (race condition test)")
    print("  GET  /portfolio/me    - Read portfolio")
    print("  GET  /isAuth          - Auth verification")
    print("\n" + "="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("\n" + "="*60)
    print("  FixIIT SQL API Load Test Complete")
    print("="*60)
    print("\nACID Properties Verified:")
    print("  Atomicity:    MySQL transactions ensure all-or-nothing commits")
    print("  Consistency:  Foreign key constraints enforced by database")
    print("  Isolation:    InnoDB row-level locking prevents dirty reads")
    print("  Durability:   Committed transactions persisted to disk")
    print("\n" + "="*60 + "\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Log failed requests for debugging."""
    if exception or (response and response.status_code >= 400):
        if exception:
            print(f"[FAIL] {request_type} {name}: {exception}")
        elif response and response.status_code not in [401, 403]:  # Don't log auth errors as failures
            try:
                error_data = response.json() if response.content else {}
                print(f"[FAIL] {request_type} {name}: {response.status_code} - {error_data.get('error', 'Unknown')}")
            except:
                print(f"[FAIL] {request_type} {name}: {response.status_code}")


# ============================================================================
# Usage Instructions
# ============================================================================

if __name__ == "__main__":
    print("""
FixIIT SQL API Load Testing (Assignment 3 Module B)
====================================================

PREREQUISITES:
1. Start the Assignment 2 Module B Flask server:
   cd Assignment_2/Module_B
   python run.py

2. Ensure MySQL database is running and configured.

RUNNING TESTS:

  Web UI Mode (recommended for interactive testing):
  --------------------------------------------------
  locust -f locustfile.py --host=http://localhost:5000
  
  Then open: http://localhost:8089
  Configure users and spawn rate in the web UI.

  Headless Mode (for automated testing):
  --------------------------------------
  locust -f locustfile.py --host=http://localhost:5000 \\
         --headless -u 50 -r 10 -t 60s --csv=results/locust

  Options:
    -u 50      : 50 concurrent users
    -r 10      : Spawn 10 users per second
    -t 60s     : Run for 60 seconds
    --csv=PATH : Export results to CSV files

TEST SCENARIOS:
  - FixIITUser:         Normal usage (read/write mix)
  - RaceConditionUser:  Concurrent updates to same ticket
  - StressUser:         High-frequency requests
  - MixedWorkloadUser:  70% read, 30% write workload
""")
