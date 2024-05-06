import os
import sys
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "source")))

from entities.monitoring_system_structure.trigger import Trigger
from monitoring_systems.zabbix_controller import ZabbixController
from outer_resources.zabbix_connector import ZabbixTrigger


class TestZabbixController(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.zabbix_controller = ZabbixController(
            config=ZabbixController.Config(collection_interval_sec=42),
            context=ZabbixController.Context(controller=MagicMock(), zabbix_connector=MagicMock()),
        )

    async def test_get_triggers(self) -> None:
        with self.subTest("valid"):
            self.zabbix_controller.context.zabbix_connector.get_triggers = AsyncMock(
                return_value={
                    ZabbixTrigger(
                        triggerid='19207',
                        description='/boot: Disk space is low (used > {$VFS.FS.PUSED.MAX.WARN:"/boot"}%)',
                        priority='2',
                        host_id='10417',
                    )
                }
            )

            triggers = await self.zabbix_controller.get_triggers()

            self.zabbix_controller.context.zabbix_connector.get_triggers.assert_awaited_once()
            self.assertEqual(
                triggers,
                [
                    Trigger(
                        id=19207,
                        title='/boot: Disk space is low (used > {$VFS.FS.PUSED.MAX.WARN:"/boot"}%)',
                        severity=2,
                        host_id=10417,
                        disabled_at=None,
                        created_at=triggers[0].created_at,
                    )
                ]
            )
