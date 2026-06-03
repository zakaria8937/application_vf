from flask import Blueprint, render_template, redirect, url_for, jsonify, send_file, Response
from flask_login import login_required, current_user
from models import db
from models.calculation import Calculation
from models.molecule import Molecule
from core.gas_database import GAS_DB
from sqlalchemy import func
from datetime import datetime, timedelta
import io
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

main_bp = Blueprint("main", __name__)


@main_bp.context_processor
def utility_processor():
    return {
        "current_year": datetime.utcnow().year,
        "app_name": "EOS Compare",
        "app_version": "1.0.0",
        "gas_count": len(GAS_DB),
    }


@main_bp.route("/")
def index():
    """Page d'accueil - Dashboard utilisateur"""
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    
    recent_calcs = Calculation.query.filter_by(user_id=current_user.id)\
        .order_by(Calculation.created_at.desc()).limit(10).all()
    
    total_calcs = Calculation.query.filter_by(user_id=current_user.id).count()
    
    eos_count = 4
    predefined_gas_count = len(GAS_DB)
    custom_gas_count = Molecule.query.filter_by(user_id=current_user.id).count()
    
    top_gases = db.session.query(
        Calculation.gas_name,
        func.count(Calculation.id).label('count')
    ).filter_by(user_id=current_user.id)\
     .group_by(Calculation.gas_name)\
     .order_by(func.count(Calculation.id).desc())\
     .limit(5).all()
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_activity = Calculation.query.filter(
        Calculation.user_id == current_user.id,
        Calculation.created_at >= week_ago
    ).count()
    
    return render_template(
        "index.html",
        recent_calcs=recent_calcs,
        total_calcs=total_calcs,
        top_gases=top_gases,
        recent_activity=recent_activity,
        custom_gases_count=custom_gas_count,
        eos_count=eos_count,
        predefined_gas_count=predefined_gas_count,
        total_available_gases=predefined_gas_count + custom_gas_count
    )


@main_bp.route("/eos")
@login_required
def eos_explorer():
    return render_template("eos_explorer.html")


@main_bp.route("/isotherms")
@login_required
def isotherms():
    return render_template("isotherms.html")


@main_bp.route("/z-factor")
@login_required
def z_factor():
    return render_template("z_factor.html")


@main_bp.route("/therm-prop")
@login_required
def therm_prop():
    return render_template("therm_prop.html")


@main_bp.route("/vle")
@login_required
def vle():
    return render_template("vle.html")


@main_bp.route("/history")
@login_required
def history():
    """Page d'historique des calculs"""
    calcs = Calculation.query.filter_by(user_id=current_user.id)\
        .order_by(Calculation.created_at.desc()).limit(100).all()
    
    for calc in calcs:
        if not hasattr(calc, 'calculation_type') or not calc.calculation_type:
            if 'isotherms' in (calc.equations_used or '').lower():
                calc.calculation_type = 'isotherm'
            elif 'vle' in (calc.equations_used or '').lower():
                calc.calculation_type = 'vle'
            elif 'z_factor' in (calc.equations_used or '').lower():
                calc.calculation_type = 'z_factor'
            else:
                calc.calculation_type = 'eos_explorer'
    
    return render_template("history.html", calcs=calcs)


@main_bp.route("/history/recall/<int:calc_id>", methods=["GET"])
@login_required
def recall_calculation(calc_id):
    """Récupère un calcul précédent pour le recharger"""
    calc = Calculation.query.filter_by(id=calc_id, user_id=current_user.id).first()
    if not calc:
        return jsonify({'error': 'Calcul non trouvé'}), 404
    
    results = calc.get_results()
    calc_type = calc.calculation_type if hasattr(calc, 'calculation_type') and calc.calculation_type else 'eos_explorer'
    
    if calc_type == 'z_factor' or (calc.equations_used == 'z_factor'):
        if 'Z' not in results and 'z_values' in results:
            results['Z'] = results['z_values']
        if 'P' not in results and 'pressures' in results:
            results['P'] = results['pressures']
    
    return jsonify({
        'success': True,
        'calculation': {
            'id': calc.id,
            'gas_name': calc.gas_name,
            'temperature': calc.temperature,
            'pressure': calc.pressure / 1e5,
            'calculation_type': calc_type,
            'results': results
        }
    })


@main_bp.route("/history/duplicate/<int:calc_id>", methods=["POST"])
@login_required
def duplicate_calculation(calc_id):
    """Duplique un calcul existant"""
    original = Calculation.query.filter_by(id=calc_id, user_id=current_user.id).first()
    if not original:
        return jsonify({'error': 'Calcul non trouvé'}), 404
    
    new_calc = Calculation(
        user_id=current_user.id,
        gas_name=original.gas_name,
        temperature=original.temperature,
        pressure=original.pressure,
        equations_used=original.equations_used,
        result_json=original.result_json,
        calculation_type=original.calculation_type if hasattr(original, 'calculation_type') else 'eos_explorer'
    )
    
    db.session.add(new_calc)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'new_id': new_calc.id,
        'message': 'Calcul dupliqué avec succès'
    })




@main_bp.route("/history/export-pdf/<int:calc_id>", methods=["GET"])
@login_required
def export_calculation_pdf(calc_id):
    """Exporte un calcul au format PDF - Design moderne avec graphiques recalculés"""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, Image as RLImage,
                                    HRFlowable, BaseDocTemplate, Frame, PageTemplate)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    import numpy as np
    import traceback

    # ── Palette ────────────────────────────────────────────────────────────
    C_NAVY    = rl_colors.HexColor('#1e3a8a')
    C_BLUE    = rl_colors.HexColor('#2563eb')
    C_CYAN    = rl_colors.HexColor('#06b6d4')
    C_GREEN   = rl_colors.HexColor('#10b981')
    C_AMBER   = rl_colors.HexColor('#f59e0b')
    C_RED     = rl_colors.HexColor('#ef4444')
    C_PURPLE  = rl_colors.HexColor('#8b5cf6')
    C_LIGHT   = rl_colors.HexColor('#f1f5f9')
    C_BORDER  = rl_colors.HexColor('#e2e8f0')
    C_WHITE   = rl_colors.white
    C_DARK    = rl_colors.HexColor('#1e293b')
    C_GREY    = rl_colors.HexColor('#64748b')

    MCOLORS = ['#2563eb','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4']

    # ── Récupération calcul ────────────────────────────────────────────────
    calc = Calculation.query.filter_by(id=calc_id, user_id=current_user.id).first()
    if not calc:
        return jsonify({'error': 'Calcul non trouvé'}), 404

    saved   = calc.get_results()
    gname   = calc.gas_name
    T       = calc.temperature
    P_pa    = calc.pressure
    P_bar   = P_pa / 1e5
    ctype   = getattr(calc, 'calculation_type', None) or 'eos_explorer'
    date_s  = calc.created_at.strftime('%d/%m/%Y  %H:%M')

    PAGE_W, PAGE_H = A4
    MARGIN = 1.8 * cm

    # ── Styles ─────────────────────────────────────────────────────────────
    def S(name, **kw):
        base = ParagraphStyle(name, fontName='Helvetica', fontSize=10,
                               textColor=C_DARK, leading=14)
        for k, v in kw.items():
            setattr(base, k, v)
        return base

    ST = {
        'h1':   S('h1', fontSize=22, fontName='Helvetica-Bold', textColor=C_NAVY,
                   alignment=TA_CENTER, spaceAfter=6),
        'h2':   S('h2', fontSize=13, fontName='Helvetica-Bold', textColor=C_BLUE,
                   spaceBefore=14, spaceAfter=6),
        'h3':   S('h3', fontSize=10, fontName='Helvetica-Bold', textColor=C_DARK,
                   spaceAfter=4),
        'body': S('body', fontSize=9, leading=13, textColor=C_DARK),
        'sm':   S('sm',  fontSize=8, textColor=C_GREY, leading=11),
        'kv':   S('kv',  fontSize=17, fontName='Helvetica-Bold', textColor=C_BLUE,
                   alignment=TA_CENTER, leading=20),
        'kl':   S('kl',  fontSize=7,  textColor=C_GREY, alignment=TA_CENTER, leading=10),
        'tag':  S('tag', fontSize=8,  fontName='Helvetica-Bold', textColor=C_WHITE,
                   alignment=TA_CENTER),
    }

    # ── Helpers matplotlib ─────────────────────────────────────────────────
    def style_ax(ax):
        ax.set_facecolor('#ffffff')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#e2e8f0')
        ax.spines['bottom'].set_color('#e2e8f0')
        ax.tick_params(colors='#64748b', labelsize=8.5)
        ax.yaxis.label.set_color('#475569')
        ax.xaxis.label.set_color('#475569')
        ax.title.set_color('#1e293b')
        ax.title.set_fontsize(10.5)
        ax.title.set_fontweight('bold')
        ax.grid(axis='y', color='#e2e8f0', linewidth=0.6, linestyle='--', zorder=0)

    def fig2img(fig, w, h):
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=200, bbox_inches='tight',
                    facecolor='#f8fafc')
        buf.seek(0)
        plt.close(fig)
        return RLImage(buf, width=w*cm, height=h*cm)

    # ── Tableau stylé ──────────────────────────────────────────────────────
    def make_table(rows, widths, header_bg=None):
        hbg = header_bg or C_NAVY
        t = Table(rows, colWidths=widths)
        n = len(rows)
        ts = TableStyle([
            ('BACKGROUND',     (0,0),(-1,0),  hbg),
            ('TEXTCOLOR',      (0,0),(-1,0),  C_WHITE),
            ('FONTNAME',       (0,0),(-1,0),  'Helvetica-Bold'),
            ('FONTSIZE',       (0,0),(-1,0),  9),
            ('ALIGN',          (0,0),(-1,-1), 'CENTER'),
            ('VALIGN',         (0,0),(-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1),(-1,-1), [C_WHITE, C_LIGHT]),
            ('FONTNAME',       (0,1),(-1,-1), 'Helvetica'),
            ('FONTSIZE',       (0,1),(-1,-1), 8.5),
            ('TEXTCOLOR',      (0,1),(-1,-1), C_DARK),
            ('LINEBELOW',      (0,0),(-1,0),  1.5, C_BLUE),
            ('GRID',           (0,0),(-1,-1), 0.4, C_BORDER),
            ('TOPPADDING',     (0,0),(-1,-1), 6),
            ('BOTTOMPADDING',  (0,0),(-1,-1), 6),
            ('LEFTPADDING',    (0,0),(-1,-1), 9),
            ('RIGHTPADDING',   (0,0),(-1,-1), 9),
        ])
        t.setStyle(ts)
        return t

    # ── Cartes KPI ─────────────────────────────────────────────────────────
    def kpi_row(items):
        """items = [(valeur_str, label, hex_color), ...]"""
        n   = len(items)
        cw  = (PAGE_W - 2*MARGIN - (n-1)*0.3*cm) / n
        cells = []
        for val, lbl, col in items:
            inner = Table(
                [[Paragraph(val, ParagraphStyle('kv2', fontSize=16,
                              fontName='Helvetica-Bold',
                              textColor=rl_colors.HexColor(col),
                              alignment=TA_CENTER))],
                 [Paragraph(lbl, ST['kl'])]],
                colWidths=[cw]
            )
            inner.setStyle(TableStyle([
                ('BACKGROUND',    (0,0),(-1,-1), C_WHITE),
                ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
                ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
                ('BOX',           (0,0),(-1,-1), 0.8, C_BORDER),
                ('TOPPADDING',    (0,0),(-1,-1), 10),
                ('BOTTOMPADDING', (0,0),(-1,-1), 10),
            ]))
            cells.append(inner)
        row = Table([cells], colWidths=[cw]*n)
        row.setStyle(TableStyle([
            ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
            ('LEFTPADDING',   (0,0),(-1,-1), 3),
            ('RIGHTPADDING',  (0,0),(-1,-1), 3),
        ]))
        return row

    # ── Header / Footer ────────────────────────────────────────────────────
    def on_page(canv, doc):
        canv.saveState()
        # Header band
        canv.setFillColor(C_NAVY)
        canv.rect(0, PAGE_H - 1.4*cm, PAGE_W, 1.4*cm, fill=1, stroke=0)
        canv.setFillColor(C_WHITE)
        canv.setFont('Helvetica-Bold', 8.5)
        canv.drawString(MARGIN, PAGE_H - 0.92*cm, 'EOS COMPARE  —  Rapport thermodynamique')
        canv.setFont('Helvetica', 8)
        canv.setFillColor(rl_colors.HexColor('#93c5fd'))
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.92*cm, date_s)
        # Footer band
        canv.setFillColor(C_LIGHT)
        canv.rect(0, 0, PAGE_W, 0.9*cm, fill=1, stroke=0)
        canv.setFillColor(C_GREY)
        canv.setFont('Helvetica', 7.5)
        canv.drawCentredString(PAGE_W/2, 0.3*cm,
            f'EOS Compare  ·  {gname}  ·  Page {canv.getPageNumber()}  ·  {date_s}')
        canv.restoreState()

    # ── Doc setup ──────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=2.0*cm, bottomMargin=1.2*cm)
    frame = Frame(MARGIN, 1.2*cm, PAGE_W - 2*MARGIN, PAGE_H - 3.2*cm, id='main')
    doc.addPageTemplates([PageTemplate(id='main', frames=frame, onPage=on_page)])

    story = []

    type_labels = {
        'eos_explorer': 'Explorateur EOS',
        'isotherm':     'Isothermes P-V',
        'z_factor':     'Facteur de Compressibilité Z(P)',
        'vle':          'Équilibre Liquide-Vapeur (VLE)',
    }
    tlabel = type_labels.get(ctype, ctype.replace('_',' ').title())

    # ══════════════════════════════════════════════════════════
    #  BANNIÈRE DE TITRE
    # ══════════════════════════════════════════════════════════
    banner_rows = [
        [Paragraph('RAPPORT DE CALCUL', ParagraphStyle('br0', fontSize=9,
                    fontName='Helvetica-Bold', textColor=rl_colors.HexColor('#93c5fd'),
                    alignment=TA_CENTER))],
        [Paragraph(gname, ParagraphStyle('br1', fontSize=24, fontName='Helvetica-Bold',
                    textColor=C_WHITE, alignment=TA_CENTER, leading=28))],
        [Paragraph(tlabel, ParagraphStyle('br2', fontSize=12,
                    textColor=rl_colors.HexColor('#67e8f9'), alignment=TA_CENTER))],
        [Spacer(1, 4)],
        [Paragraph(f'T = {T} K  ({T-273.15:.1f} °C)  ·  P = {P_bar:.3f} bar  ·  {date_s}',
                   ParagraphStyle('br3', fontSize=9,
                    textColor=rl_colors.HexColor('#cbd5e1'), alignment=TA_CENTER))],
    ]
    banner = Table(banner_rows, colWidths=[PAGE_W - 2*MARGIN])
    banner.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_NAVY),
        ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
        ('TOPPADDING',    (0,0),(-1,-1), 14),
        ('BOTTOMPADDING', (0,0),(-1,-1), 14),
    ]))
    story.append(banner)
    story.append(Spacer(1, 14))

    # ══════════════════════════════════════════════════════════
    #  PARAMÈTRES
    # ══════════════════════════════════════════════════════════
    story.append(HRFlowable(width='100%', thickness=2, color=C_BLUE, spaceAfter=4))
    story.append(Paragraph('🔧  Paramètres du calcul', ST['h2']))
    param_rows = [
        ['Paramètre', 'Valeur'],
        ['Substance / Système', gname],
        ['Type de calcul',      tlabel],
        ['Température',         f'{T} K  ({T-273.15:.1f} °C)'],
        ['Pression de référence', f'{P_bar:.4f} bar'],
        ['Équations / Modèle',  calc.equations_used or 'N/A'],
        ['Date du calcul',      date_s],
        ['ID',                  f'#{calc.id}'],
    ]
    story.append(make_table(param_rows, [5.5*cm, 10.5*cm]))
    story.append(Spacer(1, 14))

    # ══════════════════════════════════════════════════════════
    #  SECTION PAR TYPE
    # ══════════════════════════════════════════════════════════
    try:
        # ── EOS EXPLORER ─────────────────────────────────────
        if ctype == 'eos_explorer':
            story.append(HRFlowable(width='100%', thickness=2, color=C_BLUE, spaceAfter=4))
            story.append(Paragraph('📊  Résultats — Équations d\'état', ST['h2']))

            eos_names, vm_vals, z_vals = [], [], []
            for key, d in saved.items():
                if isinstance(d, dict) and 'Vm' in d and 'Z' in d:
                    eos_names.append(d.get('label', key))
                    vm_vals.append(d['Vm'] * 1000)   # L/mol
                    z_vals.append(d['Z'])

            if eos_names:
                # KPI
                story.append(kpi_row([
                    (f'{z_vals[0]:.5f}',   f'Z  —  {eos_names[0]}',  '#2563eb'),
                    (f'{vm_vals[0]:.4f} L', f'Vm — {eos_names[0]}',   '#10b981'),
                    (f'{len(eos_names)}',    'Équations comparées',    '#8b5cf6'),
                    (f'{T} K',              'Température',             '#f59e0b'),
                ]))
                story.append(Spacer(1, 12))

                # Graphiques
                fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
                fig.patch.set_facecolor('#f8fafc')
                x   = list(range(len(eos_names)))
                bcl = MCOLORS[:len(eos_names)]

                # Vm bar
                ax1 = axes[0]
                bars = ax1.bar(x, vm_vals, color=bcl, width=0.52,
                               edgecolor='white', linewidth=1.1, zorder=3)
                ax1.set_xticks(x); ax1.set_xticklabels(eos_names, rotation=18, ha='right')
                ax1.set_ylabel('Volume molaire (L/mol)')
                ax1.set_title('Volume Molaire par EOS')
                for b, v in zip(bars, vm_vals):
                    ax1.text(b.get_x()+b.get_width()/2, v + max(vm_vals)*0.015,
                             f'{v:.5f}', ha='center', va='bottom',
                             fontsize=7.5, color='#1e293b', fontweight='bold')
                style_ax(ax1)

                # Z bar
                ax2 = axes[1]
                bars2 = ax2.bar(x, z_vals, color=bcl, width=0.52,
                                edgecolor='white', linewidth=1.1, zorder=3)
                ax2.axhline(1.0, color='#dc2626', linestyle='--', linewidth=1.4,
                            label='Gaz parfait Z=1', zorder=4)
                ax2.set_xticks(x); ax2.set_xticklabels(eos_names, rotation=18, ha='right')
                ax2.set_ylabel('Facteur de compressibilité Z')
                ax2.set_title('Facteur Z par EOS')
                ax2.legend(fontsize=8)
                for b, v in zip(bars2, z_vals):
                    ax2.text(b.get_x()+b.get_width()/2, v + max(z_vals)*0.015,
                             f'{v:.5f}', ha='center', va='bottom',
                             fontsize=7.5, color='#1e293b', fontweight='bold')
                style_ax(ax2)

                fig.tight_layout(pad=2.5)
                story.append(fig2img(fig, 16, 6.5))
                story.append(Spacer(1, 12))

                # Tableau
                story.append(HRFlowable(width='100%', thickness=1, color=C_BORDER, spaceAfter=4))
                story.append(Paragraph('📋  Tableau comparatif', ST['h2']))
                trows = [['Équation d\'état', 'Vm (L/mol)', 'Z', 'Écart au gaz parfait']]
                for nm, vm, z in zip(eos_names, vm_vals, z_vals):
                    trows.append([nm, f'{vm:.6f}', f'{z:.6f}', f'{abs(z-1)*100:.3f}%'])
                story.append(make_table(trows, [5.5*cm, 3.5*cm, 3.5*cm, 3.5*cm]))

            else:
                story.append(Paragraph('Aucune donnée EOS trouvée dans ce calcul.', ST['body']))

        # ── Z-FACTOR ─────────────────────────────────────────
        elif ctype == 'z_factor':
            story.append(HRFlowable(width='100%', thickness=2, color=C_BLUE, spaceAfter=4))
            story.append(Paragraph('📈  Résultats — Facteur de Compressibilité Z(P)', ST['h2']))

            # Recalcul depuis les paramètres (Z et P peuvent être vides en DB)
            from core.z_factor import z_curve
            from core.gas_database import GAS_DB, get_gas_by_formula

            # Trouver le gaz
            gas_obj = None
            for k, g in GAS_DB.items():
                if g['name'].lower() == gname.lower() or g['name'] in gname:
                    gas_obj = g; break
            if gas_obj is None:
                for k, g in GAS_DB.items():
                    if k.lower() in gname.lower():
                        gas_obj = g; break

            Z_list = saved.get('Z', [])
            P_list = saved.get('P', [])  # already in bar from z_curve

            # Si pas de données, recalculer
            if (not Z_list or not P_list) and gas_obj:
                res = z_curve(gas_obj, T)
                Z_list = res.get('Z', [])
                P_list = res.get('P', [])  # bar

            if Z_list and P_list:
                # Adapter unités si P en Pa
                if P_list and P_list[0] > 1000:
                    P_bar_arr = [p / 1e5 for p in P_list]
                else:
                    P_bar_arr = P_list

                z_min = min(Z_list); z_max = max(Z_list)
                z_mid = Z_list[len(Z_list)//2]
                p_min = min(P_bar_arr); p_max = max(P_bar_arr)

                story.append(kpi_row([
                    (f'{z_min:.5f}', 'Z minimum',         '#ef4444'),
                    (f'{z_max:.5f}', 'Z maximum',         '#10b981'),
                    (f'{z_mid:.5f}', 'Z à P médiane',     '#2563eb'),
                    (f'{T} K',       'Température',        '#f59e0b'),
                ]))
                story.append(Spacer(1, 12))

                # Courbe Z(P)
                fig, ax = plt.subplots(figsize=(13, 5))
                fig.patch.set_facecolor('#f8fafc')
                ax.plot(P_bar_arr, Z_list, color='#2563eb', linewidth=2.2, zorder=3, label='Z calculé (Peng-Robinson)')
                ax.axhline(1.0, color='#dc2626', linestyle='--', linewidth=1.5, label='Gaz parfait (Z=1)', zorder=4)
                ax.fill_between(P_bar_arr, Z_list, 1.0,
                                where=[z < 1 for z in Z_list],
                                alpha=0.13, color='#ef4444', label='Attractif (Z < 1)')
                ax.fill_between(P_bar_arr, Z_list, 1.0,
                                where=[z >= 1 for z in Z_list],
                                alpha=0.13, color='#10b981', label='Répulsif (Z > 1)')
                ax.set_xlabel('Pression (bar)')
                ax.set_ylabel('Facteur de compressibilité Z')
                ax.set_title(f'Z = f(P)  —  {gname}  à  T = {T} K')
                ax.legend(fontsize=8.5)
                style_ax(ax)
                fig.tight_layout()
                story.append(fig2img(fig, 16, 6))
                story.append(Spacer(1, 12))

                # Tableau échantillon
                story.append(HRFlowable(width='100%', thickness=1, color=C_BORDER, spaceAfter=4))
                story.append(Paragraph('📋  Données tabulées (extrait 15 points)', ST['h2']))
                step = max(1, len(P_bar_arr) // 15)
                trows = [['P (bar)', 'Z', 'PVm/RT', 'Écart gaz parfait']]
                for i in range(0, len(P_bar_arr), step):
                    dev = abs(Z_list[i] - 1.0) * 100
                    trows.append([
                        f'{P_bar_arr[i]:.2f}',
                        f'{Z_list[i]:.6f}',
                        f'{Z_list[i]:.6f}',
                        f'{dev:.3f}%'
                    ])
                story.append(make_table(trows, [3.5*cm, 4*cm, 4*cm, 4.5*cm]))
            else:
                story.append(Paragraph('Données Z(P) non disponibles pour ce calcul.', ST['body']))

        # ── VLE ──────────────────────────────────────────────
        elif ctype == 'vle':
            story.append(HRFlowable(width='100%', thickness=2, color=C_BLUE, spaceAfter=4))
            story.append(Paragraph('⚗️  Résultats — Équilibre Liquide-Vapeur', ST['h2']))

            comps = saved.get('components', ['Composant 1', 'Composant 2'])
            mf    = saved.get('mole_fractions', [0.5, 0.5])
            P_bub = saved.get('bubble_pressure')
            y_vap = saved.get('vapor_composition', [])
            comp_str = ' / '.join(comps) if comps else 'Système binaire'

            kpi_items = [
                (comp_str[:22], 'Système', '#1e3a8a'),
                (f'{mf[0]:.4f} / {mf[1]:.4f}' if len(mf)>=2 else '-', 'Fractions x₁/x₂', '#2563eb'),
            ]
            if P_bub:
                kpi_items.append((f'{P_bub/1e3:.2f} kPa', 'Pression de bulle', '#10b981'))
            if y_vap and len(y_vap) >= 2:
                kpi_items.append((f'{y_vap[0]:.4f} / {y_vap[1]:.4f}', 'Comp. vapeur y₁/y₂', '#f59e0b'))
            story.append(kpi_row(kpi_items))
            story.append(Spacer(1, 12))

            # Graphiques VLE
            if y_vap and len(y_vap) >= 2 and len(mf) >= 2:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
                fig.patch.set_facecolor('#f8fafc')

                # Diagramme x-y
                ax1.plot([0,1],[0,1], color='#94a3b8', linestyle='--', lw=1.2, label='y = x (idéal)')
                ax1.scatter([mf[0]], [y_vap[0]], s=120, color='#2563eb', zorder=6,
                            label=f'Point calculé\nx₁={mf[0]:.3f} → y₁={y_vap[0]:.3f}')
                ax1.annotate(f'  ({mf[0]:.3f}, {y_vap[0]:.3f})',
                             xy=(mf[0], y_vap[0]), fontsize=8, color='#1d4ed8')
                ax1.set_xlabel(f'x₁  ({comps[0]})')
                ax1.set_ylabel(f'y₁  ({comps[0]})')
                ax1.set_title('Diagramme x-y')
                ax1.set_xlim(0, 1); ax1.set_ylim(0, 1)
                ax1.legend(fontsize=7.5)
                style_ax(ax1)

                # Barres comparaison liq/vap
                labels = comps[:2]
                xdata  = mf[:2]
                ydata  = y_vap[:2]
                bx = [0, 1]; w = 0.28
                b1 = ax2.bar([v-w/2 for v in bx], xdata, w, color='#2563eb',
                             label='Liquide (x)', edgecolor='white', linewidth=0.8)
                b2 = ax2.bar([v+w/2 for v in bx], ydata, w, color='#10b981',
                             label='Vapeur (y)', edgecolor='white', linewidth=0.8)
                ax2.set_xticks(bx); ax2.set_xticklabels(labels, fontsize=9)
                ax2.set_ylabel('Fraction molaire')
                ax2.set_title('Compositions Liquide vs Vapeur')
                ax2.legend(fontsize=8)
                ax2.set_ylim(0, 1.15)
                for b, v in zip(list(b1)+list(b2), list(xdata)+list(ydata)):
                    ax2.text(b.get_x()+b.get_width()/2, v+0.025,
                             f'{v:.3f}', ha='center', fontsize=8,
                             fontweight='bold', color='#1e293b')
                style_ax(ax2)

                fig.tight_layout(pad=2.5)
                story.append(fig2img(fig, 16, 6))
                story.append(Spacer(1, 12))

            # Tableau
            story.append(HRFlowable(width='100%', thickness=1, color=C_BORDER, spaceAfter=4))
            story.append(Paragraph('📋  Résumé des conditions VLE', ST['h2']))
            trows = [['Paramètre', 'Valeur']]
            trows.append(['Composant 1', comps[0] if comps else '-'])
            trows.append(['Composant 2', comps[1] if len(comps)>1 else '-'])
            trows.append(['Fraction molaire x₁', f'{mf[0]:.6f}' if mf else '-'])
            trows.append(['Fraction molaire x₂', f'{mf[1]:.6f}' if len(mf)>1 else '-'])
            if P_bub:
                trows.append(['Pression de bulle', f'{P_bub:.2f} Pa  =  {P_bub/1e5:.5f} bar  =  {P_bub/1e3:.3f} kPa'])
            if y_vap:
                trows.append(['Composition vapeur y₁', f'{y_vap[0]:.6f}'])
                if len(y_vap)>1:
                    trows.append(['Composition vapeur y₂', f'{y_vap[1]:.6f}'])
            trows.append(['Température', f'{T} K  =  {T-273.15:.2f} °C'])
            trows.append(['Modèle utilisé', calc.equations_used or 'N/A'])
            story.append(make_table(trows, [6*cm, 10*cm]))

        # ── ISOTHERMES ────────────────────────────────────────
        elif ctype == 'isotherm':
            story.append(HRFlowable(width='100%', thickness=2, color=C_BLUE, spaceAfter=4))
            story.append(Paragraph('🌡️  Résultats — Isothermes P-V', ST['h2']))

            from core.isotherms import generate_isotherms
            from core.gas_database import GAS_DB

            temps = saved.get('temperatures', [T])

            gas_obj = None
            for k, g in GAS_DB.items():
                if g['name'].lower() == gname.lower() or g['name'] in gname:
                    gas_obj = g; break
            if gas_obj is None:
                for k, g in GAS_DB.items():
                    if k.lower() in gname.lower():
                        gas_obj = g; break

            story.append(kpi_row([
                (str(len(temps)),    'Isothermes tracées', '#2563eb'),
                (f'{min(temps)} K',  'T minimum',          '#10b981'),
                (f'{max(temps)} K',  'T maximum',          '#ef4444'),
                (gname[:18],         'Substance',           '#8b5cf6'),
            ]))
            story.append(Spacer(1, 12))

            if gas_obj:
                iso_res = generate_isotherms(gas_obj, temps, n_points=300)
                datasets = iso_res.get('datasets', [])

                fig, ax = plt.subplots(figsize=(14, 5.5))
                fig.patch.set_facecolor('#f8fafc')

                eos_to_plot = ['Peng-Robinson', 'SRK', 'Van der Waals', 'Gaz Parfait']
                eos_styles = {
                    'Peng-Robinson': ('#2563eb', '-',  2.0),
                    'SRK':           ('#10b981', '--', 1.8),
                    'Van der Waals': ('#f59e0b', '-.',  1.6),
                    'Gaz Parfait':   ('#94a3b8', ':',  1.4),
                }
                plotted = set()
                for ds in datasets:
                    lbl = ds.get('label', '')
                    pts = ds.get('data', [])
                    if not pts: continue
                    xv = [p['x'] for p in pts]
                    yv = [p['y'] for p in pts if p.get('y')]
                    xv = [p['x'] for p in pts if p.get('y')]
                    if not xv: continue

                    eos_name = next((e for e in eos_to_plot if e in lbl), None)
                    T_part   = lbl.split('T=')[-1].replace('K','').strip() if 'T=' in lbl else ''
                    color, ls, lw = eos_styles.get(eos_name, ('#64748b', '-', 1.2))
                    show_label = lbl if lbl not in plotted else '_nolegend_'
                    ax.plot(xv, yv, color=color, linestyle=ls, linewidth=lw,
                            label=show_label, alpha=0.85)
                    plotted.add(lbl)

                ax.set_xlabel('Volume molaire Vm (L/mol)')
                ax.set_ylabel('Pression P (bar)')
                ax.set_title(f'Isothermes P-Vm  —  {gname}  (EOS comparées)')
                ax.set_ylim(0, 300)
                ax.legend(fontsize=7, ncol=3, loc='upper right')
                style_ax(ax)
                fig.tight_layout()
                story.append(fig2img(fig, 16, 6))
                story.append(Spacer(1, 12))

            # Tableau températures
            story.append(HRFlowable(width='100%', thickness=1, color=C_BORDER, spaceAfter=4))
            story.append(Paragraph('📋  Températures des isothermes', ST['h2']))
            trows = [['N°', 'Température (K)', 'Température (°C)', 'T / Tc']]
            Tc = gas_obj['Tc'] if gas_obj else None
            for i, tc in enumerate(sorted(temps), 1):
                tr = f'{tc/Tc:.3f}' if Tc else 'N/A'
                trows.append([str(i), f'{tc} K', f'{tc-273.15:.1f} °C', tr])
            story.append(make_table(trows, [1.8*cm, 4.5*cm, 4.5*cm, 5.2*cm]))

        # ── Générique ─────────────────────────────────────────
        else:
            story.append(HRFlowable(width='100%', thickness=2, color=C_BLUE, spaceAfter=4))
            story.append(Paragraph('📋  Résultats', ST['h2']))
            if saved:
                trows = [['Clé', 'Valeur']]
                for k, v in saved.items():
                    vs = str(v)
                    trows.append([str(k), vs[:100]+('…' if len(vs)>100 else '')])
                story.append(make_table(trows, [5*cm, 11*cm]))
            else:
                story.append(Paragraph('Aucun résultat sauvegardé.', ST['body']))

    except Exception as exc:
        traceback.print_exc()
        story.append(Spacer(1, 10))
        story.append(Paragraph(f'⚠️  Erreur lors du rendu : {exc}', ST['body']))

    # ══════════════════════════════════════════════════════════
    #  PIED DE RAPPORT
    # ══════════════════════════════════════════════════════════
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width='100%', thickness=1, color=C_BORDER, spaceAfter=6))
    info_rows = [
        ['Champ', 'Valeur'],
        ['Plateforme',   'EOS Compare — Thermodynamique avancée'],
        ['Utilisateur',  getattr(current_user, 'username', str(current_user.id))],
        ['Calcul ID',    f'#{calc.id}'],
        ['Export généré', datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')],
    ]
    story.append(make_table(info_rows, [5*cm, 11*cm], header_bg=C_GREY))

    # ── Build ──────────────────────────────────────────────────────────────
    doc.build(story)
    buffer.seek(0)
    safe_name = gname.replace(' ', '_').replace(':', '-').replace('/', '-')
    return send_file(buffer, as_attachment=True,
                     download_name=f'EOS_{safe_name}_{ctype}_{calc.id}.pdf',
                     mimetype='application/pdf')


@main_bp.route("/apropos")
def apropos():
    return render_template("apropos.html")