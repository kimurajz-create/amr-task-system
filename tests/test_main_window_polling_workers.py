import os
import types
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import functions
from main import MainWindow


class _SignalRecorder:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)


class _WorkerRecorder:
    def __init__(self, func, *args):
        self.func = func
        self.args = args
        self.finished = _SignalRecorder()
        self.error = _SignalRecorder()
        self.started = False

    def start(self):
        self.started = True


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = "ok"

    def json(self):
        return self._payload


class MainWindowPollingWorkerTests(unittest.TestCase):
    def test_start_guarded_worker_avoids_duplicate_background_jobs(self):
        fake = types.SimpleNamespace(
            worker_job_busy={},
            workers=[],
        )
        fake._cleanup_worker_job = lambda job_name, worker: MainWindow._cleanup_worker_job(
            fake,
            job_name,
            worker,
        )

        created_workers = []

        def build_worker(func, *args):
            worker = _WorkerRecorder(func, *args)
            created_workers.append(worker)
            return worker

        with patch("main.DBWorker", side_effect=build_worker):
            started = MainWindow._start_guarded_worker(
                fake,
                "mir_info",
                lambda: {"ok": True},
                lambda result: None,
                lambda error: None,
            )
            skipped = MainWindow._start_guarded_worker(
                fake,
                "mir_info",
                lambda: {"ok": True},
                lambda result: None,
                lambda error: None,
            )

        self.assertTrue(started)
        self.assertFalse(skipped)
        self.assertEqual(1, len(created_workers))
        self.assertTrue(created_workers[0].started)
        self.assertTrue(fake.worker_job_busy["mir_info"])
        self.assertEqual(1, len(fake.workers))

    def test_schedule_mir_info_refresh_uses_background_worker_job(self):
        recorded = []
        fake = types.SimpleNamespace()
        fake._load_mir_info_snapshot = lambda: {"state_id": 3}
        fake._apply_mir_info_snapshot = lambda snapshot: None
        fake._handle_mir_info_refresh_error = lambda message: None
        fake._start_guarded_worker = lambda job_name, func, success_cb, error_cb: recorded.append(
            (job_name, func, success_cb, error_cb)
        ) or True

        MainWindow.schedule_mir_info_refresh(fake)

        self.assertEqual(1, len(recorded))
        job_name, func, success_cb, error_cb = recorded[0]
        self.assertEqual("mir_info", job_name)
        self.assertIs(func, fake._load_mir_info_snapshot)
        self.assertIs(success_cb, fake._apply_mir_info_snapshot)
        self.assertIs(error_cb, fake._handle_mir_info_refresh_error)


class MirApiTimeoutTests(unittest.TestCase):
    def test_check_mir_status_uses_timeout(self):
        with patch("functions.requests.get", return_value=_FakeResponse({"state_id": 3})) as request_get, patch(
            "functions.get_auth_headers",
            return_value={"Authorization": "token"},
        ):
            result = functions.check_MiR_status()

        self.assertEqual({"state_id": 3}, result)
        _, kwargs = request_get.call_args
        self.assertEqual(functions.MIR_REQUEST_TIMEOUT_SECONDS, kwargs["timeout"])

    def test_get_pending_mission_names_uses_timeout_for_each_lookup(self):
        responses = [
            _FakeResponse([{"id": 7, "state": "Pending"}]),
            _FakeResponse({"mission": "/v2.0.0/missions/demo"}),
            _FakeResponse({"name": "Deliver meds"}),
        ]

        with patch("functions.requests.get", side_effect=responses) as request_get, patch(
            "functions.get_auth_headers",
            return_value={"Authorization": "token"},
        ):
            result = functions.get_pending_mission_names()

        self.assertEqual(["Deliver meds"], result)
        self.assertEqual(3, request_get.call_count)
        for _, kwargs in request_get.call_args_list:
            self.assertEqual(
                functions.MIR_REQUEST_TIMEOUT_SECONDS,
                kwargs["timeout"],
            )


if __name__ == "__main__":
    unittest.main()
