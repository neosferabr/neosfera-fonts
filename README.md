# Sistema Tipográfico Neosfera (`v1.000`) · Google Fonts Ready

Este repositório reúne a superfamília tipográfica **Neosfera**, organizada com nomenclatura padronizada OpenType/Google Fonts, cobertura completa do conjunto **`GF_Latin_Core` + `Latin Extended-A`** e pacotes oficiais prontos para submissão no repositório `google/fonts`.

---

## 1. Arquitetura Oficial de Famílias e Nomes

| Família Oficial | Pasta de Trabalho | Pacote Google Fonts (`ofl/`) | Categoria GF | Estilos | Glifos | Descrição Conceitual |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`Neosfera Serif`** | `neosfera-serif/` | `google-fonts/ofl/neosferaserif/` | `SERIF` | Light (300), Light Italic (300i), Regular (400), Italic (400i), Bold (700), Bold Italic (700i) | 363 | Desenho autoral paramétrico com meia-serifa unilateral nas hastes verticais, `a` de dois andares (romano e itálico) e caudas em gancho reto (`g`, `j`, `y`, `J`). |
| **`Neosfera Sans`** | `neosfera-sans/` | `google-fonts/ofl/neosferasans/` | `SANS_SERIF` | Light (300), Light Italic (300i), Regular (400), Italic (400i), Bold (700), Bold Italic (700i) | 363 | Versão grotesca limpa (sem meia-serifa) do motor paramétrico autoral Neosfera, ideal para interfaces e texto corrido. |
| **`Neosfera Display`** | `neosfera-display/` | `google-fonts/ofl/neosferadisplay/` | `DISPLAY` | Regular (400), Bold (700), Black (900) | 363 | Versão condensada sem serifa de alto impacto vertical para títulos, capas e redes sociais. |
| **`Neosfera Dither`** | `neosfera-dither/` | `google-fonts/ofl/neosferadither/` | `DISPLAY` | Regular (400), Bold (700) | 408 | Fonte display com trama de meio-tom ordenada Bayer 8×8 (célula fina de 6px no Regular, célula densa de 12px no Bold). |
| **`Neosfera Dither Condensed`** | `neosfera-dither-condensed/` | `google-fonts/ofl/neosferadithercondensed/` | `DISPLAY` | Regular (400), Bold (700) | 408 | Versão condensada de alta densidade com trama ordenada Bayer 8×8. |
| **`Neosfera Glitch`** | `neosfera-glitch/` | `google-fonts/ofl/neosferaglitch/` | `DISPLAY` | Regular (400), Bold (700) + estados 1..4 | 2032 | Trama Bayer 8×8 fatiada em bandas horizontais deslocadas com Stylistic Sets OpenType (`ss01`–`ss04`). |
| **`Neosfera Glitch Condensed`** | `neosfera-glitch/` | `google-fonts/ofl/neosferaglitchcondensed/` | `DISPLAY` | Regular (400), Bold (700) + estados 1..4 | 2032 | Versão condensada da Neosfera Glitch com Stylistic Sets OpenType (`ss01`–`ss04`). |

---

## 2. Adequações Técnicas Implementadas para o Google Fonts

1. **Cobertura de Glifos (`GF_Latin_Core` + `Latin-Ext`):**
   - Expansão do motor paramétrico (`motor/grotesk.py`) de 113 para **363 glifos**, cobrindo 100% dos 219 codepoints obrigatórios do `GF_Latin_Core` (ASCII completo, Latin-1 Supplement completo, ligaturas `fi`/`fl`, `ẞ`, `Œ`/`œ`, `Š`/`š`, `Ž`/`ž`, `Ÿ`, `ƒ`, `ȷ`, moedas `€$£¥¢¤`, símbolos matemáticos, frações, sobrescritos, pontuação tipográfica completa e diacríticos da Europa Ocidental e Central).
   - Adição dos glifos `uni0237` (`ȷ`), `uni1E9E` (`ẞ`) e `fl` (`ﬂ`) nas famílias Dither e Glitch para atingir 100% do `GF_Latin_Core`.
2. **Tabelas OpenType e Metadados (`name`, `OS/2`, `STAT`, `hhea`, `gasp`, `post`):**
   - `OS/2.fsType = 0` (*Installable Embedding*, exigência obrigatória do Google Fonts).
   - `OS/2.fsSelection` com bit 7 (`USE_TYPO_METRICS`) ativo e métricas verticais unificadas por família (`hhea.ascent == sTypoAscender`, `hhea.descent == sTypoDescender`, `lineGap == 0`, `usWinAscent`/`usWinDescent` constantes).
   - Tabela `STAT` (*Style Attributes Table*) gerada em todas as fontes.
   - Tabela `gasp` configurada com `0x000F` (gridfit + grayscale + symmetric smoothing).
   - Tabela `name` limpa (exclusivamente `platformID=3, platEncID=1, langID=0x409`), seguindo a distinção estrita entre estilos RIBBI (`Regular`, `Italic`, `Bold`, `Bold Italic`) e não-RIBBI (`Light`, `Light Italic`, `Black` com `NameID 16` e `17`).
   - Glifos `space` (`0x0020`) e `uni00A0` (`0x00A0`) separados com a mesma largura de avanço.
   - Kerning OpenType compilado por classes (`PairPosFormat2`) no `GPOS` e ligaturas padrão (`fi`, `fl`) no `GSUB`.
3. **Estrutura Oficial de Submissão (`google-fonts/ofl/<slug>/`):**
   - Cada família possui seu diretório pronto para Pull Request em `google/fonts/ofl/<slug>/` contendo os arquivos `.ttf`, `OFL.txt`, `DESCRIPTION.en_us.html` e `METADATA.pb`.

---

## 3. Como Reconstruir e Validar

```bash
# Reconstruir todas as famílias (.ttf, .woff2 e pacotes google-fonts/ofl/*)
.venv/bin/python3 motor/build_all.py

# Rodar a auditoria de conformidade Google Fonts QA
.venv/bin/python3 motor/validate_google_fonts.py
```

