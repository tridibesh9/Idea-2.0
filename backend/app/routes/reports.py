import csv
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.complaint import Complaint
from app.models.audit_log import AuditLog

router = APIRouter()


@router.get("/export")
async def export_complaints(
    format: str = Query("csv", regex="^(csv|pdf)$"),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    channel: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Export complaints as CSV or a printable HTML report."""
    query = select(Complaint).order_by(Complaint.created_at.desc())
    if status:
        query = query.where(Complaint.status == status)
    if severity:
        query = query.where(Complaint.severity == severity)
    if category:
        query = query.where(Complaint.category == category)
    if channel:
        query = query.where(Complaint.channel == channel)

    result = await db.execute(query)
    complaints = result.scalars().all()

    if format == "csv":
        return _generate_csv(complaints)
    else:
        return _generate_html_report(complaints)


def _generate_csv(complaints) -> StreamingResponse:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Channel", "Subject", "Category", "Product", "Severity",
        "Sentiment", "Status", "SLA Deadline", "SLA Breached",
        "Regulatory Flags", "Created At", "Resolved At",
    ])
    for c in complaints:
        flags = ""
        if c.regulatory_flags:
            try:
                flags = ", ".join(json.loads(c.regulatory_flags))
            except (json.JSONDecodeError, TypeError):
                flags = str(c.regulatory_flags)
        writer.writerow([
            str(c.id), c.channel, c.subject or "", c.category or "",
            c.product or "", c.severity,
            f"{c.sentiment_label} ({c.sentiment_score})" if c.sentiment_score else "",
            c.status,
            c.sla_deadline.isoformat() if c.sla_deadline else "",
            "Yes" if c.is_sla_breached else "No",
            flags,
            c.created_at.isoformat() if c.created_at else "",
            c.resolved_at.isoformat() if c.resolved_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=complaints_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"},
    )


def _generate_html_report(complaints) -> StreamingResponse:
    """Generate a printable HTML report (can be saved as PDF from browser)."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(complaints)
    critical = sum(1 for c in complaints if c.severity == "critical")
    breached = sum(1 for c in complaints if c.is_sla_breached)
    flagged = sum(1 for c in complaints if c.regulatory_flags and c.regulatory_flags != "[]")

    rows = ""
    for c in complaints:
        flags = ""
        if c.regulatory_flags:
            try:
                parsed = json.loads(c.regulatory_flags)
                flags = ", ".join(parsed) if parsed else ""
            except (json.JSONDecodeError, TypeError):
                pass
        rows += f"""<tr>
            <td>{str(c.id)[:8]}...</td>
            <td>{c.channel}</td>
            <td>{c.subject or c.body[:60] if c.body else ''}</td>
            <td>{c.category or '-'}</td>
            <td class="sev-{c.severity}">{c.severity}</td>
            <td>{c.status}</td>
            <td>{'YES' if c.is_sla_breached else 'No'}</td>
            <td style="color: {'red' if flags else 'inherit'}">{flags or '-'}</td>
            <td>{c.created_at.strftime('%Y-%m-%d') if c.created_at else ''}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>ComplaintIQ Report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 40px; color: #1a1a1a; }}
  h1 {{ color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 10px; }}
  .meta {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
  .kpis {{ display: flex; gap: 20px; margin: 20px 0; }}
  .kpi {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; text-align: center; flex: 1; }}
  .kpi .number {{ font-size: 2em; font-weight: bold; }}
  .kpi .label {{ font-size: 0.8em; color: #64748b; }}
  .kpi.critical .number {{ color: #ef4444; }}
  .kpi.breached .number {{ color: #f97316; }}
  .kpi.flagged .number {{ color: #dc2626; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 0.85em; }}
  th {{ background: #1e40af; color: white; padding: 10px 8px; text-align: left; }}
  td {{ padding: 8px; border-bottom: 1px solid #e2e8f0; }}
  tr:nth-child(even) {{ background: #f8fafc; }}
  .sev-critical {{ color: #ef4444; font-weight: bold; }}
  .sev-high {{ color: #f97316; font-weight: bold; }}
  .sev-medium {{ color: #eab308; }}
  .sev-low {{ color: #22c55e; }}
  @media print {{ body {{ padding: 20px; }} .no-print {{ display: none; }} }}
</style></head><body>
<h1>ComplaintIQ — Regulatory Compliance Report</h1>
<p class="meta">Generated: {now} | Total Records: {total}</p>
<div class="kpis">
  <div class="kpi"><div class="number">{total}</div><div class="label">Total Complaints</div></div>
  <div class="kpi critical"><div class="number">{critical}</div><div class="label">Critical</div></div>
  <div class="kpi breached"><div class="number">{breached}</div><div class="label">SLA Breached</div></div>
  <div class="kpi flagged"><div class="number">{flagged}</div><div class="label">Regulatory Flagged</div></div>
</div>
<p class="no-print" style="color:#3b82f6;cursor:pointer" onclick="window.print()">🖨 Print / Save as PDF</p>
<table>
<thead><tr><th>ID</th><th>Channel</th><th>Subject</th><th>Category</th><th>Severity</th><th>Status</th><th>SLA Breach</th><th>Reg. Flags</th><th>Date</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<p style="margin-top:30px;font-size:0.8em;color:#94a3b8;text-align:center">ComplaintIQ Automated Report — Confidential</p>
</body></html>"""

    return StreamingResponse(
        io.StringIO(html),
        media_type="text/html",
        headers={"Content-Disposition": f"inline; filename=report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.html"},
    )
