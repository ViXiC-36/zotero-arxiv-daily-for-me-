import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "prepare_legacy_config.py"
SPEC = importlib.util.spec_from_file_location("prepare_legacy_config", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_build_config_migrates_legacy_values_without_credentials():
    config = MODULE.build_config(
        {
            "ARXIV_QUERY": "cs.CL+cs.SD",
            "SMTP_SERVER": "smtp.example.com",
            "SMTP_PORT": "587",
            "SEND_EMPTY": "true",
            "MAX_PAPER_NUM": "25",
            "MODEL_NAME": "example-model",
            "LANGUAGE": "Chinese",
            "ZOTERO_KEY": "must-not-be-copied",
            "SENDER_PASSWORD": "must-not-be-copied",
            "OPENAI_API_KEY": "must-not-be-copied",
        }
    )

    assert config["source"]["arxiv"]["category"] == ["cs.CL", "cs.SD"]
    assert config["email"]["smtp_server"] == "smtp.example.com"
    assert config["email"]["smtp_port"] == 587
    assert config["executor"]["send_empty"] is True
    assert config["executor"]["max_paper_num"] == 25
    assert config["llm"]["generation_kwargs"]["model"] == "example-model"
    assert config["llm"]["language"] == "Chinese"
    assert "must-not-be-copied" not in repr(config)


def test_build_config_uses_safe_defaults_for_empty_values():
    config = MODULE.build_config({"ARXIV_QUERY": "", "SMTP_PORT": ""})

    assert config["source"]["arxiv"]["category"] == MODULE.DEFAULT_ARXIV_CATEGORIES
    assert config["email"]["smtp_server"] == "smtp.qq.com"
    assert config["email"]["smtp_port"] == 465
    assert config["executor"]["send_empty"] is False
    assert config["executor"]["max_paper_num"] == 100
