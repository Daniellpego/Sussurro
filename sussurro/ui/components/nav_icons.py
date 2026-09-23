"""Ícones de linha da sidebar dos Ajustes e do menu da bandeja — desenhados com QPainter (sem
dependência de font de ícones). Grade 24x24 estilo Lucide, traço arredondado,
mapeada pro retângulo alvo. Cor única (branco/escuro conforme o tile).
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen


def paint(p: QPainter, key: str, rect: QRectF, color: QColor, stroke: float) -> None:
    sx, sy = rect.width() / 24.0, rect.height() / 24.0

    def Pt(x: float, y: float) -> QPointF:
        return QPointF(rect.x() + x * sx, rect.y() + y * sy)

    def line(a: float, b: float, c: float, d: float) -> None:
        p.drawLine(Pt(a, b), Pt(c, d))

    def ring(cx: float, cy: float, r: float) -> None:
        p.drawEllipse(Pt(cx, cy), r * sx, r * sy)

    def dot(cx: float, cy: float, r: float) -> None:
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        p.drawEllipse(Pt(cx, cy), r * sx, r * sy)
        p.restore()

    def rrect(x1: float, y1: float, x2: float, y2: float, rad: float) -> None:
        p.drawRoundedRect(QRectF(Pt(x1, y1), Pt(x2, y2)), rad * sx, rad * sy)

    pen = QPen(color, stroke)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    if key == "geral":  # sliders
        line(4, 9, 20, 9)
        line(4, 15, 20, 15)
        dot(9, 9, 2.4)
        dot(15, 15, 2.4)

    elif key == "modelos":  # chip / cpu
        rrect(7, 7, 17, 17, 2)
        rrect(10.5, 10.5, 13.5, 13.5, 1)
        for v in (10, 14):
            line(v, 7, v, 4.5)
            line(v, 17, v, 19.5)
            line(7, v, 4.5, v)
            line(17, v, 19.5, v)

    elif key == "modos":  # layers
        path = QPainterPath(Pt(12, 4))
        for pt in ((19.5, 8.5), (12, 13), (4.5, 8.5)):
            path.lineTo(Pt(*pt))
        path.closeSubpath()
        p.drawPath(path)
        line(4.5, 12.5, 12, 17)
        line(12, 17, 19.5, 12.5)

    elif key == "audio":  # microfone
        rrect(9, 3.5, 15, 13.5, 3)
        p.drawArc(QRectF(Pt(6, 8), Pt(18, 16)), 180 * 16, -180 * 16)
        line(12, 16, 12, 19.5)
        line(9.5, 19.5, 14.5, 19.5)

    elif key == "atalhos":  # teclado
        rrect(2.5, 7, 21.5, 17, 2.5)
        for x in (7, 11, 15):
            dot(x, 11, 0.95)
        line(8, 14, 16, 14)

    elif key == "dicionario":  # livro
        rrect(7, 4, 18, 20, 1.5)
        line(10, 4, 10, 20)
        line(12, 9, 16, 9)
        line(12, 13, 16, 13)

    elif key == "sobre":  # info
        ring(12, 12, 8.5)
        dot(12, 8, 1.15)
        line(12, 11.5, 12, 16.5)

    # --- ícones do menu da bandeja ---
    elif key == "janela":  # janela do app
        rrect(3.5, 5, 20.5, 19, 2.5)
        line(3.5, 9.5, 20.5, 9.5)
        dot(6.5, 7.25, 0.8)
        dot(9, 7.25, 0.8)

    elif key == "historico":  # relógio
        ring(12, 12, 8.5)
        line(12, 7.5, 12, 12)
        line(12, 12, 15, 14)

    elif key == "ajustes":  # engrenagem simplificada
        ring(12, 12, 3)
        for a, b, c, d in ((12, 3.5, 12, 6), (12, 18, 12, 20.5),
                           (3.5, 12, 6, 12), (18, 12, 20.5, 12),
                           (6, 6, 7.8, 7.8), (16.2, 16.2, 18, 18),
                           (18, 6, 16.2, 7.8), (7.8, 16.2, 6, 18)):
            line(a, b, c, d)
        ring(12, 12, 6.5)

    elif key == "pausar":  # pause
        line(9, 6.5, 9, 17.5)
        line(15, 6.5, 15, 17.5)

    elif key == "retomar":  # play
        path = QPainterPath(Pt(8, 5.5))
        path.lineTo(Pt(18.5, 12))
        path.lineTo(Pt(8, 18.5))
        path.closeSubpath()
        p.drawPath(path)

    elif key == "sair":  # power
        p.drawArc(QRectF(Pt(4.5, 5), Pt(19.5, 20)), 125 * 16, 290 * 16)
        line(12, 3.5, 12, 11)
