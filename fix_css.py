import re

with open(r'static/css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

old_pattern = r'@media\s*\(max-width:\s*1080px\)\s*\{[\s\S]*?\}\s*\}\s*@media\s*\(max-width:\s*760px\)\s*\{[\s\S]*?\}\s*\}\s*$'

new_media = """@media (max-width: 1080px) {
  .hero-panel, .auth-stage { grid-template-columns: 1fr; }
  .topnav-links { display: none; }
  .topnav-burger { display: flex; }
  .topnav.open .topnav-links {
    display: flex; flex-direction: column;
    position: absolute; top: 68px; left: 0; right: 0;
    background: rgba(8, 17, 31, 0.96);
    backdrop-filter: blur(20px);
    padding: 16px 28px;
    border-bottom: 1px solid var(--line);
    gap: 4px; z-index: 99;
  }
  [data-theme="light"] .topnav.open .topnav-links { background: rgba(255,255,255,0.96); }
}

@media (max-width: 760px) {
  .content, .auth-shell { padding: 18px; }
  .card, .hero-panel, .auth-panel, .auth-showcase, .mini-note { padding: 18px; }
  .page-header { flex-direction: column; align-items: flex-start; }
  .auth-showcase { min-height: auto; }
  .auth-kpis, .hero-mini-grid, .best-eos-card, .best-eos-metrics, .chart-grid { grid-template-columns: 1fr; }
  .btn-actions, .hero-actions { flex-direction: column; }
  .btn, .btn-block { width: 100%; }
  .topnav { padding: 0 16px; }
}
"""

css = re.sub(old_pattern, new_media, css)
with open(r'static/css/style.css', 'w', encoding='utf-8') as f:
    f.write(css)
print('Done')
