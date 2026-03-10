from flask import Flask, jsonify
from TaskDBManager import TaskDBManager

app = Flask(__name__)

DB_CONFIG = {
    'user': 'postgres',
    'host': 'localhost',
    'database': 'military_mir250_project',
    'password': '123456',
    'port': 5432
}

db_manager = TaskDBManager(DB_CONFIG)
db_manager.connect()


@app.route("/room/<room_id>/task")
def get_room_task(room_id):

    task = db_manager.get_latest_task_for_room(room_id)

    if task:
        return jsonify(task)
    else:
        return jsonify({"task": None})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)