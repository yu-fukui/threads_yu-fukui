"""キューの項目を実際に Threads へ投稿する処理。"""

from __future__ import annotations

import logging
import os

from .client import PostResult, ThreadsAPIError, ThreadsClient
from .config import Config
from .queue import QueueItem

logger = logging.getLogger(__name__)


def トピック(item: QueueItem) -> str | None:
    """本体の投稿に付ける Threads のトピック（2026-11-23 統括決定：1投稿に1つ）。
    効き目を比べるため、出す日の通し番号が偶数の日だけ付ける（あり・なしを日ごとに交互。2週比べる）。
    語は環境変数 THREADS_TOPIC、始める日は THREADS_TOPIC_FROM（YYYY-MM-DD）。返信には付けない。"""
    語 = os.environ.get("THREADS_TOPIC", "").strip()
    if not 語 or getattr(item, "reply_to", None) or not item.scheduled_at:
        return None
    日 = item.scheduled_at.date()
    始め = os.environ.get("THREADS_TOPIC_FROM", "").strip()
    if 始め and 日.isoformat() < 始め:
        return None
    return 語 if 日.toordinal() % 2 == 0 else None


def publish_item(
    client: ThreadsClient,
    item: QueueItem,
    config: Config,
    *,
    dry_run: bool = False,
) -> PostResult | None:
    """1 件（連投がある場合はその一連）を投稿する。dry-run なら何も送らない。"""
    if dry_run:
        logger.info(
            "[dry-run] 投稿しません id=%s media_type=%s text=%r thread=%d件",
            item.id,
            item.media_type,
            item.text,
            len(item.thread),
        )
        return None

    中身 = dict(
        text=item.text,
        media_type=item.media_type,
        image_url=item.image_url,
        video_url=item.video_url,
        link_attachment=item.link_attachment,
        reply_control=item.reply_control,
        alt_text=item.alt_text,
    )
    語 = トピック(item)
    if 語:
        try:
            creation_id = client.create_container(**中身, topic_tag=語)
            logger.info("トピック「%s」を付けました id=%s", 語, item.id)
        except ThreadsAPIError as exc:
            # トピックが受け付けられなくても、投稿そのものは出す
            logger.warning("トピック「%s」を付けられませんでした（%s）。付けずに出します id=%s", 語, exc, item.id)
            creation_id = client.create_container(**中身)
    else:
        creation_id = client.create_container(**中身)
    _wait_for_container(client, creation_id, item.media_type, config)
    post_id = client.publish(creation_id)
    logger.info("投稿しました id=%s post_id=%s", item.id, post_id)

    # 連投は 1 件目への返信として順につなげる
    reply_to = post_id
    for index, text in enumerate(item.thread, start=2):
        reply_container = client.create_container(text=text, reply_to_id=reply_to)
        _wait_for_container(client, reply_container, "TEXT", config)
        reply_to = client.publish(reply_container)
        logger.info("連投 %d 件目を投稿しました post_id=%s", index, reply_to)

    return PostResult(
        creation_id=creation_id, post_id=post_id, permalink=client.permalink(post_id)
    )


def _wait_for_container(
    client: ThreadsClient, container_id: str, media_type: str, config: Config
) -> None:
    if media_type == "TEXT":
        # テキストは即時に公開できるが、直後の publish が稀に失敗するため少し待つ
        client.sleep(config.publish_delay)
        return
    client.wait_until_ready(container_id, interval=config.media_publish_delay / 6)
