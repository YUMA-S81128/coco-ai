import logging
import sys
from functools import lru_cache


@lru_cache
def setup_logging():
    """
    アプリケーションの基本的なロギング設定を構成する。

    この関数は、ロギングレベルをINFOに設定し、ログメッセージにタイムスタンプ、
    ログレベル、ロガー名、メッセージが含まれるようにフォーマットする。
    アプリケーションの起動時に一度だけ呼び出す必要がある。
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
        stream=sys.stdout,  # ログを標準出力にストリーミング
    )


def get_logger(name: str) -> logging.Logger:
    """指定された名前のロガーインスタンスを取得する。"""
    return logging.getLogger(name)
