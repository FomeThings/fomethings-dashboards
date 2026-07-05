# fomethings-dashboards

**Público a propósito** — hostea, vía GitHub Pages, los `progress.html` de las iniciativas umbrella del
FomeThings OS para poder embeberlos en sus páginas de Notion. El contenido es solo **estado de fases**
(no sensible); el repo de metodología/código (`fomethings-os`) sigue **privado**.

## Cómo funciona (UMC Tier 2)

1. La umbrella vive en su repo de proyecto (privado): `docs/plans/<umbrella>/STATE.yaml` (canónico) →
   `render_umbrella.py` → `progress.html`.
2. Ese `progress.html` se publica acá como `<umbrella>/index.html` (URL limpia).
3. GitHub Pages sirve `https://fomethings.github.io/fomethings-dashboards/<umbrella>/`.
4. Esa URL se embebe en la página umbrella de Notion (`/embed`).

Derivado, no duplicado: el estado canónico es el `STATE.yaml` en el repo del proyecto; esto es solo la
proyección visual publicada.
