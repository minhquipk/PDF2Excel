from __future__ import annotations
from typing import Iterable
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from core.models import PDFResult
from enum import IntEnum


class Column(IntEnum):
    PDF = 0
    TYPE = 1
    STATUS = 2
    NOTE = 3


_HEADERS = ("PDF", "TYPE", "STATUS", "NOTE")


assert len(_HEADERS) == len(Column)


class ProcessingTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._items)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(Column)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        item = self._items[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            c = index.column()
            if c == Column.PDF:
                return getattr(item, 'file_name', '')
            if c == Column.TYPE:
                v = getattr(item, 'pdf_type', '')
                return getattr(v, 'name', str(v))
            if c == Column.STATUS:
                v = getattr(item, 'status', '')
                return getattr(v, 'name', str(v))
            if c == Column.NOTE:
                return getattr(item, 'note', '')
        if role == Qt.ItemDataRole.ToolTipRole:
            return getattr(item, 'note', '')
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() in (
                    Column.TYPE,
                    Column.STATUS,
            ):
                return Qt.AlignmentFlag.AlignCenter
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(_HEADERS):
                return _HEADERS[section]
            return None

    def append(self, item: PDFResult):
        r = len(self._items)
        self.beginInsertRows(QModelIndex(), r, r)
        self._items.append(item)
        self.endInsertRows()

    def append_many(self, items: Iterable[PDFResult]):
        new_items = list(items)
        if not items:
            return
        f = len(self._items)
        j = f+len(new_items)-1
        self.beginInsertRows(QModelIndex(), f, j)
        self._items.extend(new_items)
        self.endInsertRows()

    def refresh_row(self, row: int):
        if 0 <= row < len(self._items):
            self.dataChanged.emit(self.index(row, 0), self.index(row, len(Column)-1))

    def clear(self):
        self.beginResetModel()
        self._items.clear()
        self.endResetModel()

    def item(self, row: int):
        return self._items[row]

    def items(self):
        return list(self._items)
