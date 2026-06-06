"""Lỗi crawl — dùng để dừng pipeline ngay khi bị Lazada chặn."""


class CrawlFailureError(RuntimeError):
    """Crawl danh mục thất bại (cookie/JSON/chặn bot)."""

    def __init__(
        self,
        category: str,
        *,
        blocked: bool = False,
        count: int = 0,
        detail: str = "",
    ) -> None:
        self.category = category
        self.blocked = blocked
        self.count = count
        self.detail = detail or "Lazada không trả JSON (cookie hết hạn hoặc bị chặn)"
        msg = (
            f"Crawl thất bại: '{category}' — {self.detail}. "
            f"Sản phẩm thu được: {count}."
        )
        super().__init__(msg)
