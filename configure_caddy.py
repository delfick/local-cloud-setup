#!/usr/bin/python -ci=__import__;o=i("os");s=i("sys");a=s.argv;p=o.path;y=p.join(p.dirname(a[1]),".python");o.execv(y,a)

import requests
import json
import sys


class BadConfig(Exception):
    pass


def configure():
    config = Config()
    body = {
        "apps": {"tls": config.tls(), "http": {"servers": {"cloud": config.apps()}}},
    }
    try:
        base_uri = "http://localhost:2019"
        res = requests.post(
            f"{base_uri}/load", json=body, headers={"Cache-Control": "must-revalidate"}
        )
        if res.status_code != 200:
            print("!" * 80)
            print(res.json())
            raise BadConfig(f"Failed to set configuration: got {res.status_code}")

        res = requests.get(f"{base_uri}/config/")
        print(json.dumps(res.json(), sort_keys=True, indent="  "))
    except BadConfig as error:
        sys.exit(str(error))
    except:
        print(json.dumps(body, sort_keys=True, indent="  ", default=lambda o: repr(o)))
        raise


class Config:
    def tls(self):
        return {
            "automation": {
                "policies": [
                    {
                        "subjects": [f"{name}.local.mycompany.co" for name, _ in self._apps],
                        "issuers": [
                            {
                                "module": "acme",
                                "ca": "https://step-ca.local.mycompany.co:666/acme/acme/directory",
                            }
                        ],
                    }
                ]
            },
        }

    @property
    def _apps(self):
        return [
            ("auth", 4598),
            ("somethingelse", 3003),
        ]

    @property
    def _pass_through(self):
        return ["homekit-token-bot"]

    def apps(self):
        apps = self._apps

        paths = [
            ("auth", "/some/url/*", "somethingelse"),
        ]

        by_app = dict(apps)

        path_routes = []

        for name, path, to in paths:
            port = by_app[to]
            path_routes.append(
                {
                    "match": [{"host": [f"{name}.local.mycompany.co"], "path": [path]}],
                    "handle": [
                        {
                            "handler": "reverse_proxy",
                            "transport": {"protocol": "http"},
                            "upstreams": [{"dial": f":{port}"}],
                        }
                    ],
                }
            )

        return {
            "listen": [":443", ":80"],
            "automatic_https": {"disable_redirects": True},
            "routes": [
                *path_routes,
                *[
                    {
                        "match": [{"host": [f"{name}.local.mycompany.co"]}],
                        "handle": [
                            {"handler": "acme_server"},
                            {
                                "handler": "reverse_proxy",
                                "transport": {
                                    "protocol": "http",
                                    "tls": {
                                        "client_certificate_automate": f"{name}.local.mycompany.co",
                                        "server_name": f"{name}.local.mycompany.co",
                                    },
                                },
                                "upstreams": [{"dial": f":{port}"}],
                            },
                        ],
                    }
                    for name, port in apps
                    if name in self._pass_through
                ],
                *[
                    {
                        "match": [{"host": [f"{name}.local.mycompany.co"]}],
                        "handle": [
                            {
                                "handler": "reverse_proxy",
                                "transport": {"protocol": "http"},
                                "upstreams": [{"dial": f":{port}"}],
                            }
                        ],
                    }
                    for name, port in apps
                    if name not in self._pass_through
                ],
            ],
        }


if __name__ == "__main__":
    configure()
