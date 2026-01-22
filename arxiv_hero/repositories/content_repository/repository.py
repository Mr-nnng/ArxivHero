from arxiv_hero.models import DBSession
from arxiv_hero.models.content import Content as ContentModel
from arxiv_hero.repositories.content_repository.protocol import LatexPagagraph


class ContentRepository:
    zh_fields = [
        "zh_text",
    ]

    @staticmethod
    def _convert_orm_to_pydantic(
        content_mdls: list[ContentModel],
    ) -> list[LatexPagagraph]:
        pagagraphs = []
        for content_mdl in content_mdls:
            pagagraphs.append(
                LatexPagagraph(
                    type=content_mdl.type,
                    order_idx=content_mdl.order_idx,
                    text=content_mdl.text,
                    zh_text=content_mdl.zh_text,
                    text_level=content_mdl.text_level,
                )
            )
        return pagagraphs

    @staticmethod
    def _convert_pydantic_to_orm(
        entry_id: str, is_translated: bool, pagagraphs: list[LatexPagagraph]
    ) -> list[ContentModel]:
        contents = []
        for pagagraph in pagagraphs:
            contents.append(
                ContentModel(
                    entry_id=entry_id,
                    type=pagagraph.type,
                    order_idx=pagagraph.order_idx,
                    text=pagagraph.text,
                    zh_text=pagagraph.zh_text,
                    text_level=pagagraph.text_level,
                    is_translated=is_translated,
                )
            )
        return contents

    def get_pagagraphs(self, entry_id: str) -> list[LatexPagagraph]:
        with DBSession() as session:
            content_mdls = (
                session.query(ContentModel)
                .filter(ContentModel.entry_id == entry_id)
                .order_by(ContentModel.order_idx)
                .all()
            )
            if not content_mdls:
                return []
            return self._convert_orm_to_pydantic(content_mdls)

    def create_content(
        self,
        entry_id: str,
        pagagraphs: list[LatexPagagraph],
        is_translated: bool = False,
    ) -> bool:
        with DBSession() as session:
            contents = self._convert_pydantic_to_orm(
                entry_id, is_translated, pagagraphs
            )
            session.bulk_save_objects(contents)
            session.commit()
            return True

    def create_content_item(
        self,
        entry_id: str,
        order_idx: int,
        pagagraph: LatexPagagraph,
        is_translated: bool = False,
    ) -> bool:
        with DBSession() as session:
            session.add(
                ContentModel(
                    entry_id=entry_id,
                    type=pagagraph.type,
                    order_idx=order_idx,
                    text=pagagraph.text,
                    zh_text=pagagraph.zh_text,
                    text_level=pagagraph.text_level,
                    is_translated=is_translated,
                )
            )
            session.commit()
            return True

    def remove_content_by_entry_id(self, entry_id: str) -> bool:
        with DBSession() as session:
            m = (
                session.query(ContentModel)
                .filter(ContentModel.entry_id == entry_id)
                .delete()
            )
            if not m:
                return False
            session.commit()
            return True

    def update_zh_field(
        self,
        entry_id: str,
        order_idx: int,
        update_data: dict[str, str],
    ) -> bool:
        with DBSession() as session:
            content_mdl = (
                session.query(ContentModel)
                .filter(ContentModel.entry_id == entry_id)
                .filter(ContentModel.order_idx == order_idx)
                .first()
            )
            if content_mdl:
                count = 0
                for k, v in update_data.items():
                    if k not in self.zh_fields:
                        continue
                    count += 1
                    setattr(content_mdl, k, v)
                if count > 0:
                    setattr(content_mdl, "is_translated", True)
                    session.commit()
                    return True
        return False
