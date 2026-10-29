"""CLI tests for the opt-in Tavily news step; every HTTP call uses MockTransport.

No test in this module has a real credential and no test reaches a provider. The
same mocked JSONL is later consumed by ``run --news-file`` to prove that news is
outlook context only and cannot change forecasts or metrics.
"""

import json
import math
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from xsentiment import main as cli
from xsentiment.config.settings import get_settings
from xsentiment.ingestion.tavily_news import (
    MAX_QUERY_CHARS,
    MAX_RESULTS_CEILING,
    NewsProviderError,
    TavilyNewsAdapter,
)
from xsentiment.pipeline.forecast_run import load_news_context, sha256_file

KEY = "tvly-mock-key-not-real"
RETRIEVED = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)
START = datetime(2026, 1, 1, tzinfo=UTC)
HEADLINE = "Bitcoin steadies after weekly range break"


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch: pytest.MonkeyPatch):
    # An empty environment value must behave exactly like a missing credential.
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("HTTP_MAX_RESPONSE_BYTES", "5000000")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _configure_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", KEY)
    get_settings.cache_clear()


def _success_handler(request: httpx.Request) -> httpx.Response:
    assert request.url.path == "/search"
    assert request.headers["Authorization"] == f"Bearer {KEY}"
    payload = json.loads(request.content)
    assert payload["query"] == "BTC sentiment"
    assert payload["search_depth"] == "basic"
    assert 1 <= payload["max_results"] <= MAX_RESULTS_CEILING
    return httpx.Response(
        200,
        json={
            "results": [
                {
                    "title": HEADLINE,
                    "url": "https://example.invalid/a",
                    "published_date": "2026-10-25T10:00:00+00:00",
                    "source": "Example Wire",
                },
                {
                    "title": "Bearer title-secret Exchange inflows cool, ETF flows tick up",
                    "url": (
                        "https://user:password@example.invalid/b?"
                        "X-Amz-Security-Token=aws-secret&article=42#token=fragment-secret"
                    ),
                    "published_date": "2026-10-25T10:00:00",
                },
                {
                    "title": "DST boundary timestamp",
                    "url": "https://example.invalid/dst",
                    "published_date": "2026-11-01T01:30:00-05:00",
                },
                {"title": HEADLINE, "url": "https://example.invalid/a"},
                {"url": "https://example.invalid/missing-title"},
            ]
        },
    )


def install_mock_adapter(
    monkeypatch: pytest.MonkeyPatch,
    handler,
    *,
    search_error: Exception | None = None,
):
    """Replace only the adapter constructor; the real adapter still parses HTTP."""
    requests: list[httpx.Request] = []
    constructed: list[dict[str, object]] = []

    def counted(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    class MockedAdapter:
        def __init__(self, *, api_key=None, max_results=5, **kwargs):
            constructed.append({"api_key": api_key, "max_results": max_results})
            self.client = httpx.AsyncClient(
                transport=httpx.MockTransport(counted), follow_redirects=False
            )
            self.inner = TavilyNewsAdapter(
                api_key=api_key,
                client=self.client,
                max_results=max_results,
                **kwargs,
            )
            self.search_error = search_error

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            try:
                await self.inner.aclose()
            finally:
                await self.client.aclose()

        async def search(self, query: str):
            if self.search_error is not None:
                raise self.search_error
            return await self.inner.search(query, retrieved_at=RETRIEVED)

    monkeypatch.setattr(cli, "TavilyNewsAdapter", MockedAdapter)
    return requests, constructed


def _write_price_snapshot(path: Path, days: int = 120) -> Path:
    candles = []
    for index in range(days):
        close = 100.0 + 6.0 * math.sin(index / 4.0) + 0.4 * index
        value = f"{round(close, 6)}"
        candles.append(
            {
                "product_id": "BTC-USD",
                "timestamp": (START + timedelta(days=index)).isoformat(),
                "low": value,
                "high": value,
                "open": value,
                "close": value,
                "volume": "3",
            }
        )
    path.write_text(
        json.dumps(
            {
                "product_id": "BTC-USD",
                "granularity_seconds": 86_400,
                "fetch_mode": "synthetic_offline_test",
                "synthetic": True,
                "candles": candles,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_post_snapshot(path: Path, days: int = 120) -> Path:
    lines = []
    for index in range(1, days):
        cutoff = START + timedelta(days=index)
        lines.append(
            json.dumps(
                {
                    "post_id": f"synthetic-{index}",
                    "created_at": (cutoff - timedelta(hours=6)).isoformat(),
                    "retrieved_at": (cutoff - timedelta(hours=5)).isoformat(),
                    "text": "Synthetic BTC sentiment is optimistic in this offline fixture",
                    "source_name": "synthetic_offline_test",
                    "source_platform": "synthetic",
                    "schema_version": "x-post-v1",
                    "warnings": ["synthetic test record, not observed X data"],
                },
                sort_keys=True,
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _fetch_args(out: Path, *, query: str = "BTC sentiment", confirm: bool = True):
    args = ["fetch-news", "--query", query, "--out", str(out)]
    if confirm:
        args.append("--confirm-live-call")
    return args


def test_fetch_news_is_a_registered_cli_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "xsentiment", "fetch-news", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    for flag in ("--query", "--max-results", "--out", "--confirm-live-call"):
        assert flag in completed.stdout
    assert "--api-key" not in completed.stdout


def test_fetch_news_refuses_a_live_call_without_confirmation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def forbidden(*args: object, **kwargs: object):
        raise AssertionError("a provider adapter must not be constructed")

    monkeypatch.setattr(cli, "TavilyNewsAdapter", forbidden)
    out = tmp_path / "news.jsonl"

    exit_code = cli.main(_fetch_args(out, confirm=False))

    assert exit_code != 0
    assert not out.exists()
    assert "--confirm-live-call" in capsys.readouterr().err


def test_fetch_news_reports_missing_credentials_without_constructing_a_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def forbidden(*args: object, **kwargs: object):
        raise AssertionError("a provider client must not be constructed without a key")

    monkeypatch.setattr(cli, "TavilyNewsAdapter", forbidden)

    exit_code = cli.main(_fetch_args(tmp_path / "news.jsonl"))
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "TAVILY_API_KEY" in captured.err
    assert "Traceback" not in captured.err
    assert not (tmp_path / "news.jsonl").exists()


def test_fetch_news_enforces_query_and_result_bounds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    requests, constructed = install_mock_adapter(monkeypatch, _success_handler)
    _configure_key(monkeypatch)

    assert cli.main(_fetch_args(tmp_path / "blank.jsonl", query="   ")) == 1
    assert "non-empty" in capsys.readouterr().err

    long_query = "x" * (MAX_QUERY_CHARS + 1)
    assert cli.main(_fetch_args(tmp_path / "long.jsonl", query=long_query)) == 1
    assert "must not exceed" in capsys.readouterr().err

    for invalid in ("0", str(MAX_RESULTS_CEILING + 1)):
        with pytest.raises(SystemExit) as excinfo:
            cli.main(
                [
                    "fetch-news",
                    "--query",
                    "BTC",
                    "--max-results",
                    invalid,
                    "--out",
                    str(tmp_path / "bounds.jsonl"),
                    "--confirm-live-call",
                ]
            )
        assert excinfo.value.code == 2

    assert requests == []
    assert constructed == []
    assert not any(tmp_path.glob("*.jsonl"))


def test_fetch_news_writes_normalized_jsonl_with_one_bounded_mocked_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _configure_key(monkeypatch)
    requests, constructed = install_mock_adapter(monkeypatch, _success_handler)
    out = tmp_path / "context" / "news.jsonl"

    exit_code = cli.main(_fetch_args(out))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert len(requests) == 1, "a paid/search call must never be automatically retried"
    assert constructed == [{"api_key": KEY, "max_results": 5}]
    assert KEY not in captured.out and KEY not in captured.err
    assert "excluded 2 provider result(s)" in captured.err

    lines = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 3
    first, second, dst = lines
    assert first["title"] == HEADLINE
    assert second["title"] == "[REDACTED] Exchange inflows cool, ETF flows tick up"
    assert second["provider"] == "tavily"
    assert first["provider"] == "tavily"
    assert first["source"] == "Example Wire"
    assert first["published_at"] == "2026-10-25T10:00:00+00:00"
    assert first["published_at_note"] is None
    assert first["retrieved_at"] == RETRIEVED.isoformat()
    assert first["query"] == "BTC sentiment"
    assert len(first["payload_sha256"]) == 64
    assert first["context_line"].startswith(HEADLINE)
    assert second["published_at"] is None
    assert second["published_at_raw"] == "2026-10-25T10:00:00"
    assert second["published_at_note"] == (
        "publication timestamp has no timezone; timestamp withheld"
    )
    assert second["url"] == (
        "https://example.invalid/b?X-Amz-Security-Token=%5BREDACTED%5D&article=42"
    )
    assert dst["published_at"] == "2026-11-01T06:30:00+00:00"
    serialized_news = out.read_text(encoding="utf-8")
    for secret in (KEY, "password", "aws-secret", "fragment-secret"):
        assert secret not in serialized_news
    assert "top-secret-token" not in serialized_news
    assert "title-secret" not in serialized_news
    assert "article=42" in serialized_news

    context = load_news_context(out)
    assert len(context) == 3
    assert "2026-10-25T10:00:00+00:00" in context[0]
    assert "publication timestamp has no timezone; timestamp withheld" in context[1]
    assert (
        "https://example.invalid/b?X-Amz-Security-Token=%5BREDACTED%5D&article=42"
        in context[1]
    )
    assert "2026-11-01" in context[2]
    for secret in ("password", "aws-secret", "fragment-secret"):
        assert secret not in context[1]
    assert "article=42" in context[1]


def test_fetch_news_fails_closed_on_http_error_without_a_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _configure_key(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "unavailable"})

    requests, _ = install_mock_adapter(monkeypatch, handler)
    out = tmp_path / "news.jsonl"

    assert cli.main(_fetch_args(out)) == 1
    assert len(requests) == 1
    assert "HTTP 503" in capsys.readouterr().err
    assert not out.exists()


def test_fetch_news_maps_timeout_and_response_ceiling_to_safe_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _configure_key(monkeypatch)

    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("closing")

    requests, _ = install_mock_adapter(monkeypatch, timeout_handler)
    assert cli.main(_fetch_args(tmp_path / "timeout.jsonl")) == 1
    assert len(requests) == 1
    assert "timed out" in capsys.readouterr().err

    monkeypatch.setenv("HTTP_MAX_RESPONSE_BYTES", "1024")
    get_settings.cache_clear()

    def large_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"results": [{"title": "t", "url": "https://e.invalid/1", "note": "x" * 4096}]},
        )

    large_requests, _ = install_mock_adapter(monkeypatch, large_handler)
    assert cli.main(_fetch_args(tmp_path / "large.jsonl")) == 1
    assert len(large_requests) == 1
    assert "ceiling" in capsys.readouterr().err
    assert not (tmp_path / "large.jsonl").exists()


def test_fetch_news_redacts_a_key_echoed_by_a_provider_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _configure_key(monkeypatch)
    install_mock_adapter(
        monkeypatch,
        _success_handler,
        search_error=NewsProviderError(f"provider echoed {KEY} in its error"),
    )

    assert cli.main(_fetch_args(tmp_path / "news.jsonl")) == 1
    captured = capsys.readouterr()

    assert "[REDACTED]" in captured.err
    assert KEY not in captured.err
    assert not (tmp_path / "news.jsonl").exists()


def test_fetch_news_jsonl_feeds_run_without_changing_predictions_or_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The two-step workflow is wired; news must affect the outlook only."""
    _configure_key(monkeypatch)
    install_mock_adapter(monkeypatch, _success_handler)
    news_path = tmp_path / "news.jsonl"
    assert cli.main(_fetch_args(news_path)) == 0

    prices = _write_price_snapshot(tmp_path / "prices.json")
    posts = _write_post_snapshot(tmp_path / "posts.jsonl")
    now = (START + timedelta(days=121)).isoformat()
    with_news = tmp_path / "run-with-news"
    without_news = tmp_path / "run-without-news"
    input_note = f"synthetic offline test fixture with {KEY}"
    common = [
        "--prices",
        str(prices),
        "--posts",
        str(posts),
        "--now",
        now,
        "--input-note",
        input_note,
    ]

    assert cli.main(["run", *common, "--news-file", str(news_path), "--out", str(with_news)]) == 0
    assert cli.main(["run", *common, "--out", str(without_news)]) == 0

    predictions = "predictions.jsonl"
    metrics = "metrics.json"
    assert (with_news / predictions).read_bytes() == (without_news / predictions).read_bytes()
    assert (with_news / metrics).read_bytes() == (without_news / metrics).read_bytes()
    assert HEADLINE not in (with_news / metrics).read_text(encoding="utf-8")
    assert HEADLINE not in (with_news / predictions).read_text(encoding="utf-8")

    manifest = json.loads((with_news / "manifest.json").read_text(encoding="utf-8"))
    provenance = manifest["provenance"]
    assert provenance["news_snapshot"] == str(news_path)
    assert provenance["news_snapshot_sha256"] == sha256_file(news_path)
    assert provenance["news_context_items"] == 3
    assert provenance["news_context_policy"] == "outlook_context_only_not_a_model_feature"
    assert provenance["input_note"] == "synthetic offline test fixture with [REDACTED]"
    assert manifest["dataset"]["rows_with_sentiment"] > 0
    assert manifest["evaluation"]["predictions"] > 0

    outlook = (with_news / "outlook.md").read_text(encoding="utf-8")
    report = (with_news / "evaluation-report.md").read_text(encoding="utf-8")
    assert HEADLINE in outlook
    assert "never enters model features" in outlook
    assert "synthetic offline test fixture" in outlook
    assert "[REDACTED]" in outlook
    assert KEY not in outlook
    assert KEY not in report
    artifacts = [
        (with_news / "manifest.json").read_text(encoding="utf-8"),
        (with_news / "outlook.md").read_text(encoding="utf-8"),
        (with_news / "evaluation-report.md").read_text(encoding="utf-8"),
        (with_news / "sentiment-vs-price.svg").read_text(encoding="utf-8"),
        (with_news / "metrics.json").read_text(encoding="utf-8"),
        (with_news / "predictions.jsonl").read_text(encoding="utf-8"),
    ]
    for artifact in artifacts:
        for secret in (KEY, "password", "aws-secret", "fragment-secret"):
            assert secret not in artifact
    assert HEADLINE not in (without_news / "outlook.md").read_text(encoding="utf-8")
