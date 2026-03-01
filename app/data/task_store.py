import json
from datetime import datetime
from pathlib import Path
from app.config import DATA_PATH, STATE_ORDER, CURRENT_USER

TASKS_FILE = DATA_PATH / "bunseki" / "tasks" / "tasks.json"


def _ensure():
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_tasks() -> list[dict]:
    _ensure()
    if not TASKS_FILE.exists():
        return []
    with open(TASKS_FILE, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_tasks(tasks: list[dict]):
    _ensure()
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2, default=str)


def create_task(holder_group_code: str, holder_group_name: str, job_numbers: list) -> dict:
    now = datetime.now()
    task_id = f"{now.strftime('%Y%m%d%H%M%S')}_{holder_group_code}"
    task = {
        "task_id": task_id,
        "task_name": f"{now.strftime('%Y%m%d%H%M%S')}_{holder_group_name}",
        "holder_group_code": holder_group_code,
        "holder_group_name": holder_group_name,
        "job_numbers": job_numbers,
        "current_state": "analysis_targets",
        "status": "進行中",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "created_by": CURRENT_USER,
        "assigned_to": CURRENT_USER,
        "state_data": {
            "task_setup": {
                "holder_group_code": holder_group_code,
                "holder_group_name": holder_group_name,
                "job_numbers": job_numbers,
                "completed": True,
            }
        },
    }
    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)
    return task


def get_task(task_id: str) -> dict | None:
    for t in load_tasks():
        if t["task_id"] == task_id:
            return t
    return None


def update_task_state(task_id: str, state: str, state_data: dict | None = None):
    tasks = load_tasks()
    for i, t in enumerate(tasks):
        if t["task_id"] == task_id:
            t["current_state"] = state
            t["updated_at"] = datetime.now().isoformat()
            if state == "completed":
                t["status"] = "終了"
            elif state == "submission":
                t["status"] = "回覧中"
            else:
                t["status"] = "進行中"
            if state_data is not None:
                t.setdefault("state_data", {})[state] = state_data
            tasks[i] = t
            break
    save_tasks(tasks)


def invalidate_after(task_id: str, from_state: str):
    """Clear all state_data after from_state and reset current_state to from_state."""
    tasks = load_tasks()
    try:
        idx = STATE_ORDER.index(from_state)
    except ValueError:
        return
    for i, t in enumerate(tasks):
        if t["task_id"] == task_id:
            sd = t.get("state_data", {})
            for s in STATE_ORDER[idx + 1 :]:
                sd.pop(s, None)
            t["state_data"] = sd
            t["current_state"] = from_state
            t["status"] = "進行中"
            t["updated_at"] = datetime.now().isoformat()
            tasks[i] = t
            break
    save_tasks(tasks)


def update_task_field(task_id: str, **kwargs):
    tasks = load_tasks()
    for i, t in enumerate(tasks):
        if t["task_id"] == task_id:
            t.update(kwargs)
            t["updated_at"] = datetime.now().isoformat()
            tasks[i] = t
            break
    save_tasks(tasks)


def handover_task(task_id: str, new_assignee: str, operated_by: str) -> None:
    """タスクの担当者を変更し、引き継ぎ履歴を記録する。"""
    tasks = load_tasks()
    now = datetime.now().isoformat()
    for i, t in enumerate(tasks):
        if t["task_id"] == task_id:
            old_assignee = t.get("assigned_to", "")
            t["assigned_to"] = new_assignee
            t["updated_at"] = now
            history = t.setdefault("handover_history", [])
            history.append({
                "from": old_assignee,
                "to": new_assignee,
                "by": operated_by,
                "at": now,
            })
            tasks[i] = t
            break
    save_tasks(tasks)
