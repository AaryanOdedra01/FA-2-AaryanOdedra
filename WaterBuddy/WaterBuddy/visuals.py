"""Original SVG battery and chart. No external images or desktop graphics."""


def drop_icon() -> str:
    return '<svg viewBox="0 0 40 48" aria-hidden="true"><path d="M20 4C15 13 5 24 5 31a15 15 0 0 0 30 0C35 24 25 13 20 4Z" fill="none" stroke="currentColor" stroke-width="3"/><path d="M12 31q0 7 7 8" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>'


def battery_svg(fill: float, uid: str = "main", previous_fill: float = None) -> str:
    """Animate only a changed refill, from the previous value to the current one."""
    fill = min(1.0, max(0.0, fill))
    previous = fill if previous_fill is None else min(1.0, max(0.0, previous_fill))
    colors = ("#8dd5bb", "#4f9e87") if fill >= 1 else ("#8dccff", "#458dcb")
    cells = []
    for i in range(8):
        x = 25 + i * 55
        fraction = min(1.0, max(0.0, fill * 8 - i))
        old_fraction = min(1.0, max(0.0, previous * 8 - i))
        changing = " is-changing" if abs(fraction - old_fraction) > 0.00001 else ""
        water = f'''<g clip-path="url(#{uid}-cell-{i})"><g class="liquid-fill{changing}" style="--from-y:{82*(1-old_fraction):.3f}px;--to-y:{82*(1-fraction):.3f}px;transform:translateY({82*(1-fraction):.3f}px)"><rect x="{x}" y="30" width="45" height="82" fill="url(#{uid}-water)"/><path d="M{x} 32q11 -3 22 0t23 0" fill="none" stroke="white" stroke-opacity=".25" stroke-width="2"/></g></g>''' if fraction or old_fraction else ""
        cells.append(f'<clipPath id="{uid}-cell-{i}"><rect x="{x}" y="30" width="45" height="82" rx="6"/></clipPath><rect x="{x}" y="30" width="45" height="82" rx="6" fill="var(--cell)"/>{water}')
    return f'''<svg class="battery" viewBox="0 0 500 142" role="img" aria-label="Water battery {fill*100:.1f} percent full, eight cells">
    <defs><linearGradient id="{uid}-water" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{colors[0]}"/><stop offset="1" stop-color="{colors[1]}"/></linearGradient></defs>
    <rect x="475" y="53" width="13" height="36" rx="4" fill="var(--battery-outline)"/>
    <rect x="7" y="14" width="469" height="114" rx="14" fill="var(--battery-bg)" stroke="var(--battery-outline)" stroke-width="2.5"/>
    {''.join(cells)}</svg>'''


def week_chart(records: dict, days: list) -> str:
    bars = []
    for i, day in enumerate(days):
        record = records.get(day.isoformat(), {"entries": [], "goal": 1})
        ratio = min(1.0, sum(e["amount"] for e in record["entries"]) / record["goal"])
        x = 35 + i * 64
        height = ratio * 95
        color = "#72bca4" if ratio >= 1 else "#76b7ef"
        bars.append(f'<rect x="{x}" y="20" width="30" height="95" rx="5" fill="var(--cell)"/><rect x="{x}" y="{115-height:.2f}" width="30" height="{height:.2f}" rx="5" fill="{color}"/><text x="{x+15}" y="140" text-anchor="middle" fill="var(--muted)" font-size="12">{day.strftime("%a")}</text>')
    return '<svg class="week-chart" viewBox="0 0 480 152" role="img" aria-label="Seven day goal completion chart">'+''.join(bars)+'</svg>'
