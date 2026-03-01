"""
SecOps Task Manager — CLI Poller
Uses only stdlib (urllib, json, time) — no extra dependencies.

Usage:
    py poll.py            # Continuous polling loop
    py poll.py --once     # Single check
    py poll.py --status   # Queue summary
"""

import sys
import json
import time
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8099"
POLL_INTERVAL = 15  # seconds


def api(method, path, body=None):
    url = BASE_URL + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        print(f"  [ERROR] {e.code}: {detail}")
        return None
    except urllib.error.URLError as e:
        print(f"  [ERROR] Cannot reach server: {e.reason}")
        return None


def show_status():
    stats = api("GET", "/api/tasks/stats")
    if not stats:
        return
    print("\n=== Queue Status ===")
    for key in ("pending", "in_progress", "approved", "completed", "failed", "cancelled"):
        label = key.replace("_", " ").title()
        print(f"  {label:15s}: {stats.get(key, 0)}")
    print()


def print_task(task):
    print(f"\n{'='*60}")
    print(f"  Task #{task['id']}: {task['title']}")
    print(f"  Client:   {task['client_name']}")
    if task.get("client_description"):
        print(f"            {task['client_description']}")
    print(f"  Project:  {task['project_name']}")
    if task.get("project_description"):
        print(f"            {task['project_description']}")
    print(f"  Category: {task['category']}")
    print(f"  Priority: {task['priority']}")
    print(f"  Mode:     {task['approval_mode']}")
    print(f"  Folder:   {task['output_folder']}")
    print(f"{'='*60}")
    if task["description"]:
        print(f"\n  Description:\n  {task['description']}")
    if task["required_actions"]:
        print(f"\n  Required Actions:\n  {task['required_actions']}")
    print()


def wait_for_approval(task_id):
    print("  Waiting for approval in the web UI...")
    while True:
        time.sleep(5)
        task = api("GET", f"/api/tasks/{task_id}")
        if not task:
            return None
        if task["status"] == "approved":
            print("  Plan APPROVED — proceeding with execution.")
            return task
        if task["status"] == "pending":
            print("  Plan REJECTED — task returned to queue.")
            return None
        if task["status"] in ("cancelled", "failed"):
            print(f"  Task {task['status']} — aborting.")
            return None


def process_task(task):
    print_task(task)

    if task["approval_mode"] == "ask":
        print("  [ASK MODE] Enter execution plan (end with blank line):")
        lines = []
        while True:
            line = input("  > ")
            if line == "":
                break
            lines.append(line)
        plan = "\n".join(lines)
        if not plan.strip():
            print("  No plan entered — skipping.")
            api("POST", f"/api/execution/{task['id']}/fail", {"error": "No plan provided", "execution_log": ""})
            return

        result = api("POST", f"/api/execution/{task['id']}/plan", {"plan": plan})
        if not result:
            return

        approved = wait_for_approval(task["id"])
        if not approved:
            return
    else:
        print("  [AUTO MODE] Proceeding immediately.")

    # --- Execution phase ---
    print("\n  Execute the task now. When finished, enter results below.")
    print("  Summary (one line):")
    summary = input("  > ")
    print("  Execution log (end with blank line):")
    log_lines = []
    while True:
        line = input("  > ")
        if line == "":
            break
        log_lines.append(line)
    execution_log = "\n".join(log_lines)

    print("  Mark as (c)ompleted or (f)ailed? [c/f]: ", end="")
    choice = input().strip().lower()
    if choice == "f":
        api("POST", f"/api/execution/{task['id']}/fail", {"error": summary, "execution_log": execution_log})
        print("  Task marked as FAILED.")
    else:
        api("POST", f"/api/execution/{task['id']}/complete", {"summary": summary, "execution_log": execution_log})
        print("  Task marked as COMPLETED.")


def poll_once():
    result = api("POST", "/api/execution/poll")
    if not result or not result.get("task"):
        print("  No pending tasks.")
        return False
    process_task(result["task"])
    return True


def poll_loop():
    print(f"SecOps Task Poller — polling {BASE_URL} every {POLL_INTERVAL}s")
    print("Press Ctrl+C to stop.\n")
    while True:
        try:
            result = api("POST", "/api/execution/poll")
            if result and result.get("task"):
                process_task(result["task"])
            else:
                print(f"  [{time.strftime('%H:%M:%S')}] No pending tasks. Waiting...")
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("\nPoller stopped.")
            break


def main():
    args = sys.argv[1:]
    if "--status" in args:
        show_status()
    elif "--once" in args:
        poll_once()
    else:
        poll_loop()


if __name__ == "__main__":
    main()
