"""
SCRPA / Hackensack PD styled HTML report builder for CAD and RMS validation.

Generates a single self-contained validation_summary.html with HPD Navy (#0d233c)
branding, KPI cards, Executive Summary, Findings table, Score Breakdown, and
print-safe CSS. Used by validate_cad.py and validate_rms.py.

Author: R. A. Carucci (from Gemini SCRPA spec)
Date: 2026-02-02
"""

import pandas as pd
from typing import Dict


def _escape_html(s: str) -> str:
    """Escape < and > for safe display in HTML."""
    if not s:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# Score component keys only (exclude priority_*_issues from breakdown table)
SCORE_CATEGORIES = [
    "required_fields",
    "valid_formats",
    "address_quality",
    "domain_compliance",
    "consistency_checks",
]
SCORE_MAX = {
    "required_fields": 30,
    "valid_formats": 25,
    "address_quality": 20,
    "domain_compliance": 15,
    "consistency_checks": 10,
}

# Fallback text when we cannot derive from data (report-type specific; no cross-reference to other system)
SCORE_CATEGORY_FALLBACK = {
    "cad": {
        "required_fields": "Required columns missing or empty: ReportNumberNew, FullAddress2, PDZone, HowReported, or others.",
        "valid_formats": "Values not in expected format (e.g. case number YY-NNNNNN, date/time).",
        "address_quality": "Address null/blank, missing street number or name, cross-street only, or failed standardization.",
        "domain_compliance": "Values outside allowed list (e.g. HowReported, Disposition).",
        "consistency_checks": "Related fields disagree or times are impossible (e.g. incident date after report date, or time out of range).",
    },
    "rms": {
        "required_fields": "Required columns missing or empty: Case Number, FullAddress, Zone, or others.",
        "valid_formats": "Values not in expected format (e.g. case number YY-NNNNNN, date/time).",
        "address_quality": "Address null/blank, missing street number or name, cross-street only, or failed standardization.",
        "domain_compliance": "Values outside allowed list.",
        "consistency_checks": "Related fields disagree or times are impossible (e.g. incident date after report date, or time out of range).",
    },
}


def _insight_from_action_items(
    action_items: pd.DataFrame, score_category: str, data_source: str
) -> str:
    """Build a short, data-driven description of what went wrong in this run for one score category."""
    if action_items.empty or "category" not in action_items.columns:
        return ""
    parts = []
    if score_category == "required_fields":
        sub = action_items[action_items["category"] == "Missing Data"]
        if not sub.empty and "field" in sub.columns:
            by_field = sub.groupby("field").size().sort_values(ascending=False).head(5)
            parts = [_escape_html(f"{fld} empty or missing ({int(n):,})") for fld, n in by_field.items()]
    elif score_category == "valid_formats":
        sub = action_items[
            action_items["category"].isin([
                "Data Quality", "Date Validation", "Time Validation", "Call Type Format"
            ])
        ]
        if not sub.empty:
            if "rule_violated" in sub.columns:
                by_rule = sub.groupby("rule_violated").size().sort_values(ascending=False).head(3)
                parts = [_escape_html(f"{r} ({int(n):,})") for r, n in by_rule.items()]
            elif "field" in sub.columns:
                by_field = sub.groupby("field").size().sort_values(ascending=False).head(3)
                parts = [f"{f} invalid format ({int(n):,})" for f, n in by_field.items()]
    elif score_category == "address_quality":
        addr_col = "FullAddress" if data_source == "rms" else "FullAddress2"
        field_match = action_items.get("field") == addr_col if "field" in action_items.columns else pd.Series(False, index=action_items.index)
        cat_match = action_items["category"].str.contains("Address", case=False, na=False) if "category" in action_items.columns else pd.Series(False, index=action_items.index)
        sub = action_items[field_match | cat_match]
        if not sub.empty:
            if "rule_violated" in sub.columns:
                by_rule = sub.groupby("rule_violated").size().sort_values(ascending=False).head(3)
                parts = [_escape_html(f"{r} ({int(n):,})") for r, n in by_rule.items()]
            else:
                n = len(sub)
                parts = [f"{addr_col} null or invalid ({n:,})"]
    elif score_category == "domain_compliance":
        sub = action_items[action_items["category"].astype(str).str.contains("Domain", case=False, na=False)] if "category" in action_items.columns else pd.DataFrame()
        if not sub.empty and "field" in sub.columns:
            by_field = sub.groupby("field").size().sort_values(ascending=False).head(3)
            parts = [f"{f} out of allowed values ({int(n):,})" for f, n in by_field.items()]
    elif score_category == "consistency_checks":
        cat_match = action_items["category"].isin(["Date Validation", "Time Validation"])
        rule_col = action_items.get("rule_violated")
        rule_match = pd.Series(False, index=action_items.index)
        if rule_col is not None and rule_col.notna().any():
            rule_match = rule_col.astype(str).str.contains("after|before|future|old|out of range", case=False, na=False)
        sub = action_items[cat_match | rule_match]
        if not sub.empty and "rule_violated" in sub.columns:
            by_rule = sub.groupby("rule_violated").size().sort_values(ascending=False).head(3)
            parts = [_escape_html(f"{r} ({int(n):,})") for r, n in by_rule.items()]
    return ". ".join(parts) if parts else ""


def build_scrpa_report(
    report_title: str,
    input_file_name: str,
    timestamp: str,
    total_records: int,
    quality_score: float,
    quality_label: str,
    breakdown: Dict,
    action_items: pd.DataFrame,
    script_name: str,
    accent_color: str = "#0d233c",
    output_folder_name: str = "",
    data_source: str = "",
) -> str:
    """
    Generates a self-contained HTML report matching SCRPA / Hackensack PD styling.

    Args:
        report_title: e.g. "CAD Data Quality Validation"
        input_file_name: Name of validated file
        timestamp: Validation run timestamp
        total_records: Number of records validated
        quality_score: Overall score 0-100
        quality_label: "Excellent", "Good", "Needs Attention", or "Critical"
        breakdown: Dict with required_fields, valid_formats, etc. and priority_*_issues
        action_items: DataFrame with columns priority, category, field, rule_violated
        script_name: e.g. "monthly_validation/scripts/validate_cad.py"
        accent_color: HPD Navy #0d233c
        output_folder_name: Optional report folder name for sub-line
        data_source: "cad" or "rms" so text refers only to this export (default: inferred from script_name)

    Returns:
        Full HTML string (single file, no external deps).
    """
    if not data_source:
        data_source = "rms" if "rms" in script_name.lower() else "cad"
    action_items_count = len(action_items) if not action_items.empty else 0
    pass_rate = (
        round((total_records - action_items_count) / total_records * 100, 2)
        if total_records > 0
        else 0
    )

    color_map = {
        "Excellent": "#d4edda",
        "Good": "#d1ecf1",
        "Needs Attention": "#fff3cd",
        "Critical": "#f8d7da",
    }
    label_bg = color_map.get(quality_label, "#f8f9fa")

    if not action_items.empty:
        category_summary = (
            action_items.groupby(["priority", "category"]).size().reset_index(name="count")
        )
        category_summary["percent"] = (
            (category_summary["count"] / total_records * 100).round(2)
        )
        top_5 = category_summary.sort_values("count", ascending=False).head(5)
        if len(top_5) > 0:
            top_issue_row = top_5.iloc[0]
            top_category = top_issue_row["category"]
            subset = action_items[action_items["category"] == top_category]
            top_field = subset["field"].iloc[0] if len(subset) > 0 and "field" in subset.columns else "N/A"
        else:
            top_category = "N/A"
            top_field = "N/A"
    else:
        top_5 = pd.DataFrame(columns=["priority", "category", "count", "percent"])
        top_category = "None"
        top_field = "N/A"

    sub_line = f"File: {input_file_name} | Generated: {timestamp}"
    if output_folder_name:
        sub_line += f" | Output: {output_folder_name}"

    # Score categories that are below max — add to Findings & Data Quality Issues (data-driven when possible; fallback is report-type specific only)
    below_max_rows = ""
    fallbacks = SCORE_CATEGORY_FALLBACK.get(data_source, SCORE_CATEGORY_FALLBACK["cad"])
    for cat in SCORE_CATEGORIES:
        score = breakdown.get(cat, 0)
        max_pts = SCORE_MAX.get(cat)
        if isinstance(score, (int, float)) and isinstance(max_pts, (int, float)) and max_pts > 0 and score < max_pts:
            pct = round(score / max_pts * 100, 1)
            cat_label = cat.replace("_", " ").title()
            insight = _insight_from_action_items(action_items, cat, data_source)
            if not insight:
                insight = _escape_html(fallbacks.get(cat, ""))
            else:
                insight = "In this run: " + _escape_html(insight)
            below_max_rows += f"                        <tr><td>{cat_label}</td><td>{score}</td><td>{max_pts}</td><td>{pct}%</td><td style=\"font-size: 12px;\">{insight}</td></tr>\n"

    # Per-category detail: top fields/rules for "Missing Data", "Data Quality", etc.
    def _detail_for_category(cat_name: str, priority: int) -> str:
        if action_items.empty or "category" not in action_items.columns:
            return ""
        sub = action_items[(action_items["category"] == cat_name) & (action_items["priority"] == priority)]
        if sub.empty:
            return ""
        # Prefer (field + rule_violated) for specificity; fall back to field or rule_violated
        parts = []
        if "field" in sub.columns and "rule_violated" in sub.columns:
            # Top 3 (field, rule) pairs by count
            pairs = sub.groupby(["field", "rule_violated"]).size().reset_index(name="n").sort_values("n", ascending=False).head(3)
            for _, r in pairs.iterrows():
                fld = str(r["field"]).strip() or "—"
                rule = str(r["rule_violated"]).strip() or ""
                if rule and rule != "nan":
                    r_short = rule[:50] + ("…" if len(rule) > 50 else "")
                    parts.append(_escape_html(f"{fld} ({r_short})"))
                else:
                    parts.append(_escape_html(fld))
        elif "field" in sub.columns:
            top_fields = sub["field"].value_counts().head(3)
            parts = [_escape_html(f"{f} (missing or invalid)") for f in top_fields.index]
        elif "rule_violated" in sub.columns:
            top_rules = sub["rule_violated"].value_counts().head(3)
            parts = [_escape_html(r) for r in top_rules.index]
        return "; ".join(parts) if parts else ""

    # Build Findings table rows (top issue categories by volume) with Details column
    findings_rows = ""
    for i, (_, row) in enumerate(top_5.iterrows(), 1):
        detail = _detail_for_category(row["category"], row["priority"])
        detail_cell = f'<td style="font-size: 12px;">{detail}</td>' if detail else "<td></td>"
        findings_rows += f"""                        <tr><td>{i}</td><td>{row['category']}</td><td>P{int(row['priority'])}</td><td>{int(row['count']):,}</td><td>{row['percent']}%</td>{detail_cell}</tr>
"""

    if not findings_rows:
        findings_rows = """                        <tr><td colspan="6" style="text-align: center; color: #28a745;">No issues found.</td></tr>
"""

    # Build Score Breakdown rows (only score components); display total as percentage
    score_rows = ""
    for cat in SCORE_CATEGORIES:
        score = breakdown.get(cat, 0)
        if isinstance(score, (int, float)):
            max_pts = SCORE_MAX.get(cat, "-")
            score_rows += f"                        <tr><td>{cat.replace('_', ' ').title()}</td><td>{score}</td><td>{max_pts}</td></tr>\n"
    score_rows += f"                        <tr style=\"font-weight: bold;\"><td>Total</td><td>{quality_score}%</td><td>100%</td></tr>\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title} - {timestamp}</title>
    <style>
        :root {{
            --hpd-navy: {accent_color};
            --panel-gray: #f8f9fa;
            --border-gray: #e1e4e8;
            --text-dark: #24292e;
            --spacing: 8px;
        }}
        body {{
            font-family: "DIN Condensed", "DIN", "Segoe UI", Arial, sans-serif;
            margin: 0;
            padding: 20px;
            color: var(--text-dark);
            background: #fff;
            line-height: 1.5;
        }}
        .header-band {{
            border-left: 10px solid var(--hpd-navy);
            padding: 20px;
            margin-bottom: 24px;
            background: var(--panel-gray);
        }}
        .header-band h1 {{
            margin: 0;
            text-transform: uppercase;
            font-size: 28px;
            color: var(--hpd-navy);
        }}
        .header-band p {{
            margin: 8px 0 0;
            font-size: 14px;
            color: #666;
        }}
        .kpi-row {{
            display: flex;
            gap: 16px;
            margin-bottom: 24px;
        }}
        .kpi-card {{
            flex: 1;
            padding: 16px;
            border: 1px solid var(--border-gray);
            text-align: center;
            border-radius: 4px;
            background: #fff;
        }}
        .kpi-value {{
            font-size: 32px;
            font-weight: bold;
            color: var(--hpd-navy);
            display: block;
        }}
        .kpi-label {{
            font-size: 12px;
            text-transform: uppercase;
            color: #666;
            letter-spacing: 1px;
        }}
        .status-band {{
            margin-top: 8px;
            padding: 4px;
            font-weight: bold;
            font-size: 14px;
            border-radius: 2px;
        }}
        .main-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }}
        .panel {{
            border: 1px solid var(--border-gray);
            padding: 20px;
            border-radius: 4px;
            margin-bottom: 24px;
            background: #fff;
        }}
        .panel-title {{
            border-bottom: 2px solid var(--hpd-navy);
            padding-bottom: 8px;
            margin-bottom: 16px;
            font-size: 18px;
            text-transform: uppercase;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th {{
            text-align: left;
            background: var(--panel-gray);
            padding: 8px;
            border-bottom: 2px solid var(--border-gray);
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid var(--border-gray);
        }}
        tr:nth-child(even) {{
            background: #fafafa;
        }}
        .footer {{
            margin-top: 40px;
            border-top: 1px solid var(--border-gray);
            padding-top: 10px;
            font-size: 11px;
            color: #999;
        }}
        @media print {{
            body {{ padding: 0; background: #fff; }}
            .panel, .kpi-card {{ break-inside: avoid; box-shadow: none; }}
        }}
        @media (max-width: 800px) {{
            .main-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="header-band">
        <h1>{report_title}</h1>
        <p>{sub_line}</p>
    </div>

    <div class="kpi-row">
        <div class="kpi-card">
            <span class="kpi-label">Quality Score</span>
            <span class="kpi-value">{quality_score}%</span>
            <div class="status-band" style="background: {label_bg};">{quality_label}</div>
        </div>
        <div class="kpi-card">
            <span class="kpi-label">Total Records</span>
            <span class="kpi-value">{total_records:,}</span>
        </div>
        <div class="kpi-card">
            <span class="kpi-label">Action Items</span>
            <span class="kpi-value">{action_items_count:,}</span>
        </div>
        <div class="kpi-card">
            <span class="kpi-label">Pass Rate</span>
            <span class="kpi-value">{pass_rate}%</span>
        </div>
    </div>

    <div class="main-grid">
        <div>
            <div class="panel">
                <div class="panel-title">Executive Summary</div>
                <ul>
                    <li>Quality classified as <strong>{quality_label}</strong> ({quality_score}%).</li>
                    <li><strong>{pass_rate}%</strong> of records passed all automated checks.</li>
                    <li>Primary issue category: <strong>{top_category}</strong>.</li>
                    <li>Field with highest error volume: <strong>{top_field}</strong>.</li>
                    <li>Total of {action_items_count:,} records require manual review/correction.</li>
                </ul>
            </div>
            <div class="panel">
                <div class="panel-title">Findings &amp; Data Quality Issues</div>
                {f'<p style="margin-bottom: 8px; font-weight: bold;">Score categories below maximum</p><table style="margin-bottom: 16px;"><thead><tr><th>Category</th><th>Score</th><th>Max</th><th>%</th><th>Common causes</th></tr></thead><tbody>{below_max_rows}</tbody></table>' if below_max_rows else ''}
                <p style="margin-bottom: 8px; font-weight: bold;">Top issue categories by volume</p>
                <table>
                    <thead>
                        <tr><th>Rank</th><th>Category</th><th>Pri</th><th>Count</th><th>%</th><th>Details</th></tr>
                    </thead>
                    <tbody>
{findings_rows}                    </tbody>
                </table>
            </div>
        </div>
        <div>
            <div class="panel">
                <div class="panel-title">Score Breakdown</div>
                <table>
                    <thead>
                        <tr><th>Category</th><th>Score</th><th>Max</th></tr>
                    </thead>
                    <tbody>
{score_rows}                    </tbody>
                </table>
            </div>
            <div class="panel">
                <div class="panel-title">Methodology</div>
                <p>Validation checks include required field presence, data format regex matching (e.g., Case Numbers YY-NNNNNN), domain value compliance, and call type normalization. Quality scores are weighted based on business priority and field criticality.</p>
            </div>
        </div>
    </div>

    <div class="panel">
        <div class="panel-title">Action Items</div>
        <p>Please refer to <strong>action_items.xlsx</strong> for a row-by-row breakdown of issues. Prioritize correcting <strong>Priority 1 (Critical)</strong> issues first to ensure accurate reporting metrics.</p>
    </div>

    <div class="footer">
        Generated by {script_name} | HPD Data Quality System
    </div>
</body>
</html>"""
    return html
