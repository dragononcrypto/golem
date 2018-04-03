import calendar
import datetime
import time
import unittest

from golem_messages.message import concents as concent_msg

from golem.network.concent import client

from tests.factories import messages as msg_factories

from ..base import ConcentBaseTest


class ForceGetTaskResultTest(ConcentBaseTest, unittest.TestCase):

    def test_send(self):
        fgtr = msg_factories.ForceGetTaskResult()
        response = self._send_to_concent(fgtr)
        msg = self._load_response(response)
        self.assertIsInstance(msg, concent_msg.AckForceGetTaskResult)
        self.assertEqual(msg.force_get_task_result.get_short_hash(),
                         fgtr.get_short_hash())

    def test_send_fail_timeout(self):
        past_deadline = calendar.timegm(time.gmtime()) -\
                        int(datetime.timedelta(days=1).total_seconds())
        ttc = msg_factories.TaskToCompute(
            compute_task_def__deadline=past_deadline
        )
        fgtr = msg_factories.ForceGetTaskResult(
            report_computed_task__task_to_compute=ttc
        )

        response = self._send_to_concent(fgtr)
        msg = self._load_response(response)
        self.assertIsInstance(msg, concent_msg.ForceGetTaskResultRejected)
        self.assertEqual(msg.reason,
                         msg.REASON.AcceptanceTimeLimitExceeded)

    def test_send_duplicate(self):
        rct = msg_factories.ReportComputedTask()
        fgtr1 = msg_factories.ForceGetTaskResult(report_computed_task=rct)

        response = self._send_to_concent(fgtr1)
        msg = self._load_response(response)
        self.assertIsInstance(msg, concent_msg.AckForceGetTaskResult)

        fgtr2 = msg_factories.ForceGetTaskResult(report_computed_task=rct)

        response = self._send_to_concent(fgtr2)
        msg = self._load_response(response)
        self.assertIsInstance(msg, concent_msg.ServiceRefused)
        self.assertEqual(msg.reason, msg.REASON.DuplicateRequest)

    def test_send_receive(self):
        fgtr = msg_factories.ForceGetTaskResult()
        ack = self._load_response(self._send_to_concent(fgtr))
        self.assertIsInstance(ack, concent_msg.AckForceGetTaskResult)
        content = client.receive_from_concent(
            fgtr.report_computed_task.task_to_compute.provider_public_key)
        self.assertIsNotNone(content)

        # @todo verify the response