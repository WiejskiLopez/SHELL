from __future__ import annotations

import yaml


def _write_message_file(writer: object) -> None:
    data = writer.message_.message_envelope_.to_dict()
    writer.path_.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False), encoding="utf-8")
