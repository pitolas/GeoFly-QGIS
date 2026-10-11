# Changelog

## 1.0.1 — 2026-10-10

- Correção de segurança para publicação no repositório oficial do QGIS.
- Removida a importação não utilizada `xml.sax.saxutils.escape`, sinalizada pelo Bandit.
- Nenhuma alteração funcional no planejamento de voo, acompanhamento de terreno, cálculos, interface ou exportação KMZ DJI Fly.

## 1.0.0 — 2026-10-10

Primeira versão pública estável preparada para distribuição pelo repositório oficial de plugins do QGIS.

- Planejamento a partir de polígono selecionado.
- Home Point no mapa ou centroide.
- Altitude AGL, overlaps, direção, velocidade e gimbal configuráveis.
- Voo simples e voo cruzado.
- Perfis DJI Mini 5 Pro, Mini 4 Pro, Mini 3 Pro e Lito X1.
- Modos de resolução de câmera conforme os perfis disponíveis.
- Cálculo de pegada, espaçamento e GSD.
- Acompanhamento de terreno por raster MDE/MDT.
- Camadas temporárias de linhas de voo, waypoints e Home.
- Exportação KMZ DJI Fly validada em campo para DJI Mini 4 Pro.
- Documentação do procedimento de substituição do KMZ de uma missão previamente criada no DJI Fly.
