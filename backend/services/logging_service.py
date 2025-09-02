import logging
import sys
from functools import lru_cache


@lru_cache
def setup_logging():
    """
    ロギングの基本設定を構成します。
    INFOレベル以上のログを標準出力に出力し、どのモジュールからのログか分かるようにフォーマットします。
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
        stream=sys.stdout,
    )


def get_logger(name: str) -> logging.Logger:
    """
    指定された名前でロガーを取得します。
    """
    return logging.getLogger(name)
