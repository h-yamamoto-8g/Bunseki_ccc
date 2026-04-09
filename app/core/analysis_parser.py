"""分析結果パーサーのバリデーション・実行エンジン。

ユーザーが設定画面からアップロードした Python コードを AST で静的解析し、
安全性を確認したうえで exec() で実行する。
"""
from __future__ import annotations

import ast
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── 許可/禁止リスト ──────────────────────────────────────────────────────────

ALLOWED_MODULES: frozenset[str] = frozenset(
    {
        "csv",
        "json",
        "re",
        "io",
        "datetime",
        "math",
        "pathlib",
        "collections",
        "itertools",
        "functools",
        "string",
        "textwrap",
        "pandas",
        "chardet",
        "pdfplumber",
    }
)

FORBIDDEN_MODULES: frozenset[str] = frozenset(
    {
        "subprocess",
        "shutil",
        "socket",
        "urllib",
        "requests",
        "http",
        "ftplib",
        "smtplib",
        "ctypes",
        "multiprocessing",
        "threading",
        "signal",
        "sys",
        "importlib",
        "pickle",
        "shelve",
        "marshal",
        "code",
        "codeop",
        "compileall",
    }
)

FORBIDDEN_CALLS: frozenset[str] = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "globals",
        "locals",
        "getattr",
        "setattr",
        "delattr",
        "breakpoint",
    }
)

FORBIDDEN_OS_ATTRS: frozenset[str] = frozenset(
    {
        "system",
        "popen",
        "remove",
        "unlink",
        "rmdir",
        "rename",
        "makedirs",
        "mkdir",
        "execv",
        "execve",
        "fork",
        "kill",
        "environ",
    }
)


# ── バリデーション ────────────────────────────────────────────────────────────


def validate_parser_code(code: str) -> list[str]:
    """パーサーコードを静的解析し、問題点のリストを返す。

    Args:
        code: パーサーの Python ソースコード文字列。

    Returns:
        問題点のリスト。空リストなら問題なし。
    """
    errors: list[str] = []

    # 構文チェック
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"構文エラー (行 {e.lineno}): {e.msg}"]

    # parse 関数の存在チェック
    parse_found = False
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "parse":
            parse_found = True
            # 引数チェック
            args = node.args
            positional = [a.arg for a in args.args]
            if positional != ["file_path"]:
                errors.append(
                    "parse() の引数は file_path のみにしてください。"
                    f" 現在: ({', '.join(positional)})"
                )
            break

    if not parse_found:
        errors.append("parse(file_path) 関数が定義されていません。")

    # 禁止パターンの検出
    for node in ast.walk(tree):
        # import チェック
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in FORBIDDEN_MODULES:
                    errors.append(f"禁止モジュール: {alias.name} (行 {node.lineno})")
                elif top not in ALLOWED_MODULES and top != "os":
                    errors.append(
                        f"許可リスト外のモジュール: {alias.name} (行 {node.lineno})"
                    )

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                if top in FORBIDDEN_MODULES:
                    errors.append(f"禁止モジュール: {node.module} (行 {node.lineno})")
                elif top not in ALLOWED_MODULES and top != "os":
                    errors.append(
                        f"許可リスト外のモジュール: {node.module} (行 {node.lineno})"
                    )

        # 関数呼び出しチェック
        elif isinstance(node, ast.Call):
            func_name = _get_call_name(node)
            if func_name in FORBIDDEN_CALLS:
                errors.append(f"禁止関数: {func_name}() (行 {node.lineno})")
            # os.system, os.popen 等のチェック
            if isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "os"
                    and node.func.attr in FORBIDDEN_OS_ATTRS
                ):
                    errors.append(
                        f"禁止操作: os.{node.func.attr}() (行 {node.lineno})"
                    )

        # open(..., 'w'/'a') の書き込みモードチェック
        elif isinstance(node, ast.Call) and _get_call_name(node) == "open":
            _check_open_write(node, errors)

    return errors


def _get_call_name(node: ast.Call) -> str:
    """ast.Call ノードから関数名を抽出する。"""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def _check_open_write(node: ast.Call, errors: list[str]) -> None:
    """open() 呼び出しで書き込みモードが指定されていないかチェックする。"""
    write_modes = {"w", "a", "x", "wb", "ab", "xb", "w+", "a+", "r+"}
    # 位置引数の2番目 (mode)
    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
        if node.args[1].value in write_modes:
            errors.append(
                f"ファイル書き込みモードは禁止されています (行 {node.lineno})"
            )
    # キーワード引数 mode=
    for kw in node.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            if kw.value.value in write_modes:
                errors.append(
                    f"ファイル書き込みモードは禁止されています (行 {node.lineno})"
                )


# ── 実行エンジン ──────────────────────────────────────────────────────────────


PARSER_TIMEOUT_SECONDS: int = 30


def execute_parser(
    code: str,
    file_path: str,
    *,
    timeout: int | None = None,
) -> list[dict[str, str]]:
    """パーサーコードを実行し、結果を返す。

    実行前に validate_parser_code() でバリデーションを通過していることを前提とする。

    Args:
        code: パーサーの Python ソースコード文字列。
        file_path: 分析結果ファイルの絶対パス。
        timeout: タイムアウト秒数。None ならデフォルト (30秒)。

    Returns:
        各辞書はサンプル名キーと分析項目キーを含む。

    Raises:
        ValueError: parse() 関数が見つからない場合。
        TypeError: 戻り値の型が不正な場合。
        TimeoutError: 実行がタイムアウトした場合。
        Exception: パーサーコードの実行中に発生した例外。
    """
    import threading

    if timeout is None:
        timeout = PARSER_TIMEOUT_SECONDS

    namespace: dict[str, Any] = {}
    exec(code, namespace)  # noqa: S102 — バリデーション済みコードのみ実行

    parse_fn = namespace.get("parse")
    if not callable(parse_fn):
        raise ValueError("parse() 関数が見つかりません。")

    result_holder: list[Any] = []
    error_holder: list[Exception] = []

    def _run() -> None:
        try:
            result_holder.append(parse_fn(file_path))
        except Exception as e:
            error_holder.append(e)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        logger.error("パーサー実行がタイムアウトしました (%d秒)", timeout)
        raise TimeoutError(
            f"パーサーの実行が {timeout} 秒以内に完了しませんでした。"
            " コードに無限ループがないか確認してください。"
        )

    if error_holder:
        raise error_holder[0]

    if not result_holder:
        raise RuntimeError("パーサーが結果を返しませんでした。")

    result = result_holder[0]
    _validate_result(result)
    return result


def _validate_result(result: Any) -> None:
    """パーサーの戻り値が list[dict[str, str]] であることを検証する。

    Raises:
        TypeError: 型が不正な場合。
    """
    if not isinstance(result, list):
        raise TypeError(
            f"戻り値は list である必要があります。取得: {type(result).__name__}"
        )
    for i, item in enumerate(result):
        if not isinstance(item, dict):
            raise TypeError(
                f"result[{i}] は dict である必要があります。取得: {type(item).__name__}"
            )
        for k, v in item.items():
            if not isinstance(k, str):
                raise TypeError(
                    f"result[{i}] のキー {k!r} は str である必要があります。"
                )
            if not isinstance(v, str):
                raise TypeError(
                    f"result[{i}]['{k}'] は str である必要があります。"
                    f" 取得: {type(v).__name__} (値: {v!r})"
                )
