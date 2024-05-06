import os
import sys
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "source")))

from outer_resources.zabbix_connector import ZabbixConnector, ZabbixProblem


class TestZabbixConnector(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.zabbix_connector = ZabbixConnector(
            config=ZabbixConnector.Config(url="url", api_key="key"),
            context=ZabbixConnector.Context(session=MagicMock()),
        )
        self.zabbix_connector._http_connector = MagicMock()

    async def test_get_problems(self) -> None:
        with self.subTest("valid"):
            answer = {
                "jsonrpc": "2.0",
                "result": [
                    {
                        "eventid": "660673",
                        "source": "0",
                        "object": "0",
                        "objectid": "19946",
                        "clock": "1670397180",
                        "ns": "116396960",
                        "r_eventid": "0",
                        "r_clock": "0",
                        "r_ns": "0",
                        "correlationid": "0",
                        "userid": "0",
                        "name": "High CPU utilization (over 90% for 5m)",
                        "acknowledged": "0",
                        "severity": "2",
                        "opdata": "Current utilization: 90.2669 %",
                        "suppressed": "0",
                        "urls": []
                    },
                    {
                        "eventid": "2182049",
                        "source": "0",
                        "object": "0",
                        "objectid": "20124",
                        "clock": "1710550081",
                        "ns": "736348706",
                        "r_eventid": "0",
                        "r_clock": "0",
                        "r_ns": "0",
                        "correlationid": "0",
                        "userid": "0",
                        "name": "Количество новых записей в camera_status меньше 1000000",
                        "acknowledged": "0",
                        "severity": "5",
                        "opdata": "",
                        "suppressed": "0",
                        "urls": []
                    },
                ],
                "id": 1
            }
            self.zabbix_connector._http_connector.post_json = AsyncMock(return_value=answer)
            self.zabbix_connector._parse_answer = MagicMock(return_value=answer["result"])

            zabbix_problems = await self.zabbix_connector.get_problems()

            self.zabbix_connector._http_connector.post_json.assert_awaited_once()
            self.zabbix_connector._parse_answer.assert_called_once()
            self.assertEqual(
                zabbix_problems,
                {
                    ZabbixProblem(
                        external_id="660673",
                        trigger_external_id="19946",
                        trigger_title="High CPU utilization (over 90% for 5m)",
                        opdata="Current utilization: 90.2669 %",
                        occurred_at="1670397180",
                        trigger_severity="2"
                    ),
                    ZabbixProblem(
                        external_id="2182049",
                        trigger_external_id="20124",
                        trigger_title="Количество новых записей в camera_status меньше 1000000",
                        opdata="",
                        occurred_at="1710550081",
                        trigger_severity="5"
                    )
                }
            )
