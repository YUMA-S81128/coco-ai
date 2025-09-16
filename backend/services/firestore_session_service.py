import asyncio
import hashlib
import json
import re
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

from google.adk.events import Event
from google.adk.sessions import BaseSessionService, Session
from google.api_core import exceptions as google_exceptions
from google.cloud import firestore
from pydantic import BaseModel
from services.logging_service import get_logger

logger = get_logger(__name__)

# タイムスタンプはFirestoreのサーバータイムスタンプを使用するため、
# Pydanticモデル用のプレースホルダーとしてUTCを使用
UTC = timezone.utc

# Firestoreのフィールドパスで無効な文字を検出するための正規表現
INVALID_KEY_CHARS = re.compile(r"[.$/\[\]]")


def _to_epoch(dt: datetime) -> float:
    """
    datetimeオブジェクトをタイムゾーンを考慮してepoch秒(float)に変換する。
    タイムゾーン情報がない場合はUTCとみなす。
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _normalize_timestamps(obj: Any) -> Any:
    """
    Firestoreから取得したオブジェクト内のdatetimeを再帰的にepoch秒(float)に変換する。（非破壊的）
    """
    if isinstance(obj, dict):
        # 新しい辞書を生成して副作用を避ける
        return {k: _normalize_timestamps(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_timestamps(x) for x in obj]
    if isinstance(obj, datetime):
        # datetime -> unix epoch (float seconds)
        return _to_epoch(obj)
    return obj


async def _run_with_retries(
    fn, *args, max_attempts=5, base_delay=0.2, log_context: dict | None = None, **kwargs
):
    """
    Firestoreのトランザクション競合など、一時的なエラーが発生した場合に
    指数バックオフ付きでリトライを実行するラッパー関数。
    """
    last_exc: Exception = RuntimeError(
        "Retry mechanism failed without a specific exception."
    )
    for attempt in range(1, max_attempts + 1):
        try:
            return await fn(*args, **kwargs)
        except (
            google_exceptions.Aborted,
            google_exceptions.DeadlineExceeded,
            google_exceptions.InternalServerError,
            google_exceptions.ServiceUnavailable,
        ) as e:
            last_exc = e
            context_str = f" (context: {log_context})" if log_context else ""
            backoff = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "Transaction attempt %d failed%s: %s; retrying in %.2fs",
                attempt,
                context_str,
                e,
                backoff,
            )
            await asyncio.sleep(backoff)

    # リトライがすべて失敗した場合、最終的な例外のトレースバックを詳細にログ記録する
    tb = "".join(
        traceback.format_exception(type(last_exc), last_exc, last_exc.__traceback__)
    )
    logger.error(
        "Transaction permanently failed after %d attempts. Context: %s\n%s",
        max_attempts,
        log_context,
        tb,
    )
    raise last_exc


class FirestoreSessionService(BaseSessionService):
    """
    Firestoreをバックエンドとして使用するADKセッションサービス（非同期）。
    - セッションをコレクションに保存します（デフォルト: 'adk_sessions'）。
    - model_dump(by_alias=True) を使用して書き込むことで、フィールドがADKスキーマ（appName, userIdなど）と一致するようにします。
    """

    def __init__(
        self, db_client: firestore.AsyncClient, collection_name: str = "adk_sessions"
    ):
        # 外部から渡された共有クライアントを使用
        self._db = db_client
        self._collection = self._db.collection(collection_name)
        logger.info(
            "FirestoreSessionService initialized (collection=%s)", collection_name
        )

    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> Session:
        session_id = session_id or uuid.uuid4().hex
        session = Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=state or {},
            events=[],
            # Pydanticモデルの検証をパスするためのプレースホルダータイムスタンプ
            last_update_time=datetime.now(UTC).timestamp(),
        )
        # Firestoreに保存するデータからevents配列を削除し、メタデータを追加
        session_data = session.model_dump(by_alias=True, exclude_none=True)
        session_data.pop(
            "events", None
        )  # キーが存在しない場合もエラーにならないようにpopを使用
        session_data["eventsCount"] = 0
        session_data["lastUpdateTime"] = firestore.SERVER_TIMESTAMP

        # ADKのエイリアス（appName/userId）を使用して保存し、他のサービスとの一貫性を保つ
        doc_ref = self._collection.document(session_id)
        await doc_ref.set(session_data)

        logger.debug(
            "created session %s for app=%s user=%s", session_id, app_name, user_id
        )

        # 返り値の整合性を保つため、書き込み後のデータを再度読み込んで返す。
        # これにより、last_update_timeがサーバーで採番された正確なタイムスタンプになる。
        created_snap = await doc_ref.get()
        created_data = created_snap.to_dict()
        if created_data:
            created_data = _normalize_timestamps(created_data)
            # ADKのSessionモデルにないカスタムフィールドを検証前に削除
            created_data.pop("eventsCount", None)
            session = Session.model_validate(created_data)
        else:
            logger.error(
                "Failed to retrieve session %s immediately after creation.", session_id
            )
        return session

    async def update_session(
        self,
        *,
        session_id: str,
        state_delta: dict[str, Any],
        app_name: str | None = None,
        user_id: str | None = None,
        raise_on_missing: bool = False,
        max_state_keys: int = 200,
    ) -> Session | None:
        """
        セッションの状態(state)をアトミックに更新し、更新後のセッションオブジェクトを返す。

        このメソッドは、ADKのLlmAgentが`output_key`を持つ場合に内部的に呼び出され、
        LLMの出力などをセッション状態に永続化する役割を担う。

        Args:
            session_id: 更新対象のセッションID。
            state_delta: セッションのstateにマージするデータの辞書。
            app_name: (任意) 所有者検証用のアプリケーション名。
            user_id: (任意) 所有者検証用のユーザーID。
            raise_on_missing: (任意) セッションが存在しない場合に例外を投げるかどうかのフラグ。
            max_state_keys: (任意) 一度に更新できるキーの最大数（過大な更新を防ぐ保護機能）。

        Returns:
            更新が成功した場合は、最新の `Session` オブジェクト。セッションが存在しない場合は `None`。
        """
        if not state_delta:
            logger.debug(
                "update_session called with empty state_delta for %s", session_id
            )
            # 更新がない場合でも、現在のセッション状態を返す
            return await self.get_session(
                app_name=app_name or "",
                user_id=user_id or "",
                session_id=session_id,
                ignore_owner_check=not (app_name and user_id),
            )

        if len(state_delta) > max_state_keys:
            raise ValueError(
                f"state_delta too large ({len(state_delta)} > {max_state_keys})"
            )

        session_ref = self._collection.document(session_id)
        update_data: dict[str, Any] = {"lastUpdateTime": firestore.SERVER_TIMESTAMP}
        for key, value in state_delta.items():
            if INVALID_KEY_CHARS.search(key):
                raise ValueError(f"Invalid character in state_delta key: '{key}'")
            update_data[f"state.{key}"] = value

        transaction = self._db.transaction()

        @firestore.async_transactional
        async def update_in_transaction(transaction: firestore.AsyncTransaction):
            snap = await session_ref.get(transaction=transaction)
            if not snap.exists:
                if raise_on_missing:
                    raise FileNotFoundError(f"Session {session_id} not found.")
                return False

            if app_name is not None or user_id is not None:
                doc = snap.to_dict() or {}
                if app_name is not None and doc.get("appName") != app_name:
                    raise PermissionError("app_name mismatch for session update")
                if user_id is not None and doc.get("userId") != user_id:
                    raise PermissionError("user_id mismatch for session update")

            transaction.update(session_ref, update_data)
            return True

        ok = await _run_with_retries(
            update_in_transaction, transaction, log_context={"session_id": session_id}
        )
        if not ok:
            return None

        return await self.get_session(
            app_name=app_name or "",
            user_id=user_id or "",
            session_id=session_id,
            ignore_owner_check=True,
        )

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Any | None = None,
        ignore_owner_check: bool = False,
        include_events: bool = False,
    ) -> Session | None:
        doc_ref = self._collection.document(session_id)
        snap = await doc_ref.get()
        if not snap.exists:
            return None

        data = snap.to_dict()
        if data is None:
            return None

        events: list[Event] = []
        if include_events:
            # サブコレクションから最新100件のイベントを取得
            events_query = (
                doc_ref.collection("events")
                .order_by("createdAt", direction=firestore.Query.DESCENDING)
                .limit(100)
            )
            event_docs = await events_query.get()
            # 時刻順（昇順）に戻してからモデルに読み込ませる
            for doc in reversed(event_docs):
                event_data = doc.to_dict()
                if event_data:
                    normalized_event_data = _normalize_timestamps(event_data)
                    events.append(Event.model_validate(normalized_event_data))

        # FirestoreのデータとサブコレクションのイベントをマージしてSessionオブジェクトを構築
        data["events"] = events

        # 親ドキュメントのタイムスタンプも正規化
        data = _normalize_timestamps(data)
        # ADKのSessionモデルにないカスタムフィールドを検証前に削除
        data.pop("eventsCount", None)
        session = Session.model_validate(data)

        if not ignore_owner_check and (
            session.app_name != app_name or session.user_id != user_id
        ):
            logger.warning(
                "session found but app_name/user_id mismatch (doc=%s, expected app=%s user=%s)",
                session_id,
                app_name,
                user_id,
            )
            return None
        return session

    async def append_event(self, session: Session, event: Event) -> Event:
        """
        セッション履歴にイベントをアトミックに追加し、イベントのアクションにあるstate_deltaを適用します。
        Firestoreトランザクションを使用して、同時更新による競合を防ぎます。
        """
        session_ref = self._collection.document(session.id)

        # イベントデータにサーバータイムスタンプを追加
        event_data = event.model_dump(by_alias=True, exclude_none=True)
        event_data["createdAt"] = firestore.SERVER_TIMESTAMP

        # イベントの冪等性（何度実行しても結果が同じになる性質）を保証するため、決定論的なIDを生成する
        # タイムスタンプなど毎回変わる値はハッシュ計算から除外する
        payload_for_hash = {
            k: v for k, v in event_data.items() if k not in ["id", "createdAt"]
        }
        # より安定したJSON文字列を生成
        payload_json = json.dumps(
            payload_for_hash, sort_keys=True, separators=(",", ":"), default=str
        )
        event_id = event.id or hashlib.sha256(payload_json.encode()).hexdigest()
        event_ref = session_ref.collection("events").document(event_id)
        # ドキュメントの中にもIDを保存してデバッグを容易にする
        event_data["id"] = event_id

        transaction = self._db.transaction()

        @firestore.async_transactional
        async def update_in_transaction(transaction: firestore.AsyncTransaction):
            # 1. 親セッションの存在を確認
            snap = await session_ref.get(transaction=transaction)
            if not snap.exists:
                raise FileNotFoundError(
                    f"Session {session.id} not found in transaction."
                )

            # 2. 【重要】イベントが既に存在するか確認し、冪等性を保証する
            existing_event_snap = await event_ref.get(transaction=transaction)
            if existing_event_snap.exists:
                # イベントが既に存在する場合（再試行など）、何もせず正常終了
                logger.info("Event %s already exists, skipping creation.", event_id)
                return

            # 3. イベントが存在しない場合のみ、ドキュメントを作成し、親を更新する
            transaction.set(event_ref, event_data)

            update_data = {
                "lastUpdateTime": firestore.SERVER_TIMESTAMP,
                "eventsCount": firestore.Increment(
                    1
                ),  # イベント数をアトミックにインクリメント
            }

            # イベントのアクションにstate_deltaが含まれている場合、それを親セッションのstateにマージする
            if event.actions and event.actions.state_delta:
                for key, value in event.actions.state_delta.items():
                    if INVALID_KEY_CHARS.search(key):
                        raise ValueError(
                            f"Invalid character in state_delta key: '{key}'"
                        )
                    # Pydanticモデルを辞書に変換してから保存
                    if isinstance(value, BaseModel):
                        update_data[f"state.{key}"] = value.model_dump(
                            by_alias=True, exclude_none=True
                        )
                    else:
                        update_data[f"state.{key}"] = value

            transaction.update(session_ref, update_data)

        # レビュー指摘対応: 堅牢化のため、リトライラッパー経由でトランザクションを実行
        await _run_with_retries(
            update_in_transaction, transaction, log_context={"session_id": session.id}
        )

        # 呼び出し元がIDを使えるように、返すイベントオブジェクトにも安全にIDをセットする
        try:
            event.id = event_id
        except Exception:
            # Eventオブジェクトがイミュータブルな場合に備え、新しいインスタンスを作成
            logger.debug("Event object is immutable, creating a new instance with id.")
            ev_data = event.model_dump(by_alias=True, exclude_none=True)
            ev_data["id"] = event_id
            event = Event.model_validate(ev_data)

        logger.debug("Appended event to subcollection for session %s", session.id)
        return event

    async def delete_session(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        """Firestoreからセッションを削除します。"""

        # Firestoreのバッチ書き込み上限（500件）を考慮し、サブコレクションをチャンクに分けて削除する
        async def _batch_delete_subcollection(ref):
            BATCH_SIZE = 499  # 500件の上限より少し余裕を持たせる
            while True:
                docs = await ref.limit(BATCH_SIZE).get()
                if not docs:
                    break  # No more documents to delete.
                batch = self._db.batch()
                for doc in docs:
                    batch.delete(doc.reference)
                await batch.commit()
                logger.info(
                    "Deleted a batch of %d events for session %s", len(docs), session_id
                )

        doc_ref = self._collection.document(session_id)
        events_ref = doc_ref.collection("events")

        # サブコレクション内の全ドキュメントをバッチ削除
        await _batch_delete_subcollection(events_ref)
        # 親ドキュメントを削除
        await doc_ref.delete()
        logger.info("Deleted session %s", session_id)

    async def list_sessions(self, *, app_name: str, user_id: str) -> list[Session]:
        """指定されたユーザーのセッション一覧をFirestoreから取得します。"""
        # by_alias=Trueで保存したため、クエリには'appName'と'userId'を使用
        query = self._collection.where("appName", "==", app_name).where(
            "userId", "==", user_id
        )
        docs = await query.get()
        sessions: list[Session] = []
        for doc in docs:
            data = doc.to_dict()
            if data is None:
                logger.warning(
                    "Document %s has no data, skipping in list_sessions.", doc.id
                )
                continue
            # このメソッドではイベントリストは読み込まない
            data["events"] = []
            # lastUpdateTimeなどのタイムスタンプフィールドを正規化
            data = _normalize_timestamps(data)
            # ADKのSessionモデルにないカスタムフィールドを検証前に削除
            data.pop("eventsCount", None)
            sessions.append(Session.model_validate(data))
        return sessions
