from dataclasses import dataclass
import logging
from typing import Any

from aiohttp.web_exceptions import HTTPBadRequest
from http_tools.http_server_connector import HttpServerConnector

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ZabbixHostGroup:
    groupid: int
    name: str


@dataclass(frozen=True)
class ZabbixHost:
    hostid: int
    name: str
    group_ids: frozenset[int]


@dataclass(frozen=True)
class ZabbixTrigger:
    triggerid: str
    description: str
    priority: int
    host_id: int


@dataclass(frozen=True)
class ZabbixProblem:
    external_id: str
    trigger_external_id: str
    trigger_title: str
    opdata: str
    occurred_at: int
    trigger_severity: int


class ZabbixConnector:
    @dataclass(kw_only=True)
    class Config(HttpServerConnector.Config):
        api_key: str

    Context = HttpServerConnector.Context

    def __init__(self, config: Config, context: Context) -> None:
        self.config = config
        self.context = context
        self._http_connector = HttpServerConnector(config, context)
        self._PATH = "/zabbix/api_jsonrpc.php"
        logger.info(f"{type(self).__name__} inited")

    async def get_host_groups(self) -> list[ZabbixHostGroup]:
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "selectGroups": ["groupid", "name"],
                "output": ["hostid", "host", "name"],
            },
            "auth": self.config.api_key,
            "id": 1,
        }

        answer = await self._http_connector.post_json(path=self._PATH, payload=payload)

        host_group_external_id_to_host_group = {}
        for host_info in self._parse_answer(answer):
            for group in host_info["groups"]:
                host_group = ZabbixHostGroup(groupid=group["groupid"], name=group["name"])
                host_group_external_id_to_host_group[group["groupid"]] = host_group
        return list(host_group_external_id_to_host_group.values())

    async def get_hosts(self) -> set[ZabbixHost]:
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "selectGroups": ["groupid", "name"],
                "output": ["hostid", "host", "name"],
            },
            "auth": self.config.api_key,
            "id": 1,
        }

        answer = await self._http_connector.post_json(self._PATH, payload=payload)

        zabbix_hosts = set()
        for host_info in self._parse_answer(answer):
            zabbix_hosts.add(
                ZabbixHost(
                    hostid=host_info["hostid"],
                    name=host_info["name"],
                    group_ids=frozenset({group["groupid"] for group in host_info["groups"]})
                )
            )
        return zabbix_hosts

    async def get_triggers(self) -> set[ZabbixTrigger]:
        payload = {
            "jsonrpc": "2.0",
            "method": "trigger.get",
            "params": {
                "selectHosts": ["hostid", "name"],
                "expandComment": "true",
                "expandDescription": "true",
                "output": "extend",
            },
            "auth": self.config.api_key,
            "id": 1,
        }

        answer = await self._http_connector.post_json(self._PATH, payload=payload)

        zabbix_triggers = set()
        for host_info in self._parse_answer(answer):
            zabbix_triggers.add(
                ZabbixTrigger(
                    triggerid=host_info["triggerid"],
                    description=host_info["description"],
                    priority=host_info["priority"],
                    host_id=host_info["hosts"][0]["hostid"],
                )
            )
        return zabbix_triggers

    async def get_problems(self) -> set[ZabbixProblem]:
        payload = {
            "jsonrpc": "2.0",
            "method": "problem.get",
            "params": {
                "output": ["eventid", "objectid", "name", "opdata", "clock", "severity"],
            },
            "auth": self.config.api_key,
            "id": 1,
        }

        answer = await self._http_connector.post_json(path=self._PATH, payload=payload)

        problems = set()
        for problem_info in self._parse_answer(answer):
            problem = ZabbixProblem(
                external_id=problem_info["eventid"],
                trigger_external_id=problem_info["objectid"],
                trigger_title=problem_info["name"],
                opdata=problem_info["opdata"],
                occurred_at=problem_info["clock"],
                trigger_severity=problem_info["severity"],
            )
            problems.add(problem)

        return problems

    @staticmethod
    def _parse_answer(answer: dict[str, Any]) -> list[dict[str, Any]]:
        if not isinstance(answer, dict):
            raise HTTPBadRequest(reason=f"Zabbix answer is not a dict: {answer}")
        try:
            return answer["result"]
        except KeyError as e:
            raise HTTPBadRequest(reason=f"No 'result' field in Zabbix answer: {answer}") from e
