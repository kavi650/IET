/**
 * pdf_export.js  — Branded PDF download for Production, Assembly & Electrical
 * Uses jsPDF (UMD) + jspdf-autotable, loaded via CDN in admin.html
 */

/* ── shared helpers ─────────────────────────────────────────── */

function _getDoc() {
    const { jsPDF } = window.jspdf;
    return new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
}

const BRAND_COLOR  = [15, 76, 129];   // #0f4c81 deep blue
const ACCENT_COLOR = [0, 168, 168];   // #00a8a8 teal
const LIGHT_GRAY   = [245, 247, 250];
const MID_GRAY     = [108, 117, 125];

function _addHeader(doc, title, subtitle) {
    const pw = doc.internal.pageSize.getWidth();

    // Top brand bar
    doc.setFillColor(...BRAND_COLOR);
    doc.rect(0, 0, pw, 18, 'F');

    // Logo text
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.setTextColor(255, 255, 255);
    doc.text('TESTINY', 12, 11.5);

    // Right side: generated date
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    const now = new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
    doc.text(`Generated: ${now}`, pw - 12, 11.5, { align: 'right' });

    // Accent stripe
    doc.setFillColor(...ACCENT_COLOR);
    doc.rect(0, 18, pw, 2, 'F');

    // Report title
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(16);
    doc.setTextColor(...BRAND_COLOR);
    doc.text(title, 12, 32);

    // Subtitle / description
    if (subtitle) {
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        doc.setTextColor(...MID_GRAY);
        doc.text(subtitle, 12, 39);
    }

    return 44; // y position after header
}

function _addFooter(doc) {
    const pw    = doc.internal.pageSize.getWidth();
    const ph    = doc.internal.pageSize.getHeight();
    const pages = doc.internal.getNumberOfPages();

    for (let i = 1; i <= pages; i++) {
        doc.setPage(i);
        doc.setFillColor(...LIGHT_GRAY);
        doc.rect(0, ph - 10, pw, 10, 'F');
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7.5);
        doc.setTextColor(...MID_GRAY);
        doc.text('Testiny — Confidential', 12, ph - 3.5);
        doc.text(`Page ${i} of ${pages}`, pw - 12, ph - 3.5, { align: 'right' });
    }
}

function _statusColor(status) {
    const map = {
        pending:     [255, 193, 7],
        in_progress: [13, 110, 253],
        completed:   [25, 135, 84],
        cancelled:   [220, 53, 69],
        passed:      [25, 135, 84],
        failed:      [220, 53, 69],
        new:         [13, 202, 240],
        won:         [25, 135, 84],
        lost:        [220, 53, 69],
    };
    return map[status] || [108, 117, 125];
}

function _statusPill(doc, text, x, y, color) {
    const w = 24, h = 5.5, r = 2;
    doc.setFillColor(...color);
    doc.roundedRect(x, y - 4, w, h, r, r, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7);
    doc.setTextColor(255, 255, 255);
    doc.text(text.replace(/_/g, ' ').toUpperCase(), x + w / 2, y, { align: 'center' });
}

/* ── summary badge row ──────────────────────────────────────── */
function _drawSummaryBadges(doc, startY, badges) {
    const pw      = doc.internal.pageSize.getWidth();
    const n       = badges.length;
    const boxW    = (pw - 24 - (n - 1) * 5) / n;
    let   x       = 12;

    badges.forEach(b => {
        doc.setFillColor(255, 255, 255);
        doc.setDrawColor(...BRAND_COLOR);
        doc.setLineWidth(0.3);
        doc.roundedRect(x, startY, boxW, 18, 2, 2, 'FD');

        // Coloured top strip
        doc.setFillColor(...b.color);
        doc.roundedRect(x, startY, boxW, 3.5, 2, 2, 'F');
        doc.rect(x, startY + 1.5, boxW, 2, 'F'); // flatten bottom of strip

        // Value
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(16);
        doc.setTextColor(...BRAND_COLOR);
        doc.text(String(b.value), x + boxW / 2, startY + 12, { align: 'center' });

        // Label
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7.5);
        doc.setTextColor(...MID_GRAY);
        doc.text(b.label, x + boxW / 2, startY + 17, { align: 'center' });

        x += boxW + 5;
    });

    return startY + 24;
}

/* ══════════════════════════════════════════════════════════════
   1. PRODUCTION ORDERS PDF
   ══════════════════════════════════════════════════════════════ */
async function downloadProductionPDF() {
    const btn = document.getElementById('downloadProdPdfBtn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating…'; }

    try {
        // Fetch ALL orders (up to 500 for PDF)
        const res  = await fetch('/api/production/orders?page=1&per_page=500');
        const data = await res.json();
        const orders = data.orders || [];

        const doc    = _getDoc();
        let   startY = _addHeader(doc, 'Production Orders Report',
            `Total Records: ${data.total || orders.length}`);

        // Summary badges
        const statusCounts = {};
        ['pending','in_progress','completed','cancelled'].forEach(s => statusCounts[s] = 0);
        orders.forEach(o => { if (statusCounts[o.status] !== undefined) statusCounts[o.status]++; });

        startY = _drawSummaryBadges(doc, startY, [
            { label: 'Total Orders',  value: orders.length,                  color: BRAND_COLOR  },
            { label: 'Pending',       value: statusCounts.pending,            color: [255,193,7]  },
            { label: 'In Progress',   value: statusCounts.in_progress,        color: [13,110,253] },
            { label: 'Completed',     value: statusCounts.completed,          color: [25,135,84]  },
            { label: 'Cancelled',     value: statusCounts.cancelled,          color: [220,53,69]  },
        ]);

        startY += 4;

        // Table
        doc.autoTable({
            startY,
            head: [['#', 'Product', 'Qty', 'Start Date', 'Due Date', 'Progress', 'Status', 'Notes']],
            body: orders.map(o => [
                `#${o.id}`,
                o.product_name || '—',
                o.quantity,
                o.start_date   || '—',
                o.due_date     || '—',
                `${o.progress}%`,
                o.status.replace(/_/g,' '),
                (o.notes || '—').substring(0, 60),
            ]),
            styles: {
                fontSize:  8,
                cellPadding: 3,
                lineColor: [220, 225, 230],
                lineWidth: 0.2,
            },
            headStyles: {
                fillColor: BRAND_COLOR,
                textColor: [255,255,255],
                fontStyle: 'bold',
                fontSize:  8.5,
            },
            alternateRowStyles: { fillColor: LIGHT_GRAY },
            columnStyles: {
                0: { cellWidth: 12 },
                6: { cellWidth: 22 },
                7: { cellWidth: 50 },
            },
            didDrawCell(data) {
                // Draw coloured status pill
                if (data.section === 'body' && data.column.index === 6) {
                    const rawStatus = orders[data.row.index]?.status || '';
                    _statusPill(doc,
                        data.cell.text[0],
                        data.cell.x + 1,
                        data.cell.y + data.cell.height / 2 + 1,
                        _statusColor(rawStatus)
                    );
                    data.cell.text = [];   // clear default text
                }
            },
            margin: { left: 12, right: 12 },
        });

        _addFooter(doc);
        doc.save(`Testiny_ProductionOrders_${_dateStamp()}.pdf`);
        showToast('Production PDF downloaded', 'success');
    } catch (err) {
        console.error(err);
        showToast('Failed to generate PDF', 'error');
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-file-pdf"></i> Download PDF'; }
    }
}

/* ══════════════════════════════════════════════════════════════
   2. ASSEMBLY PDF
   ══════════════════════════════════════════════════════════════ */
async function downloadAssemblyPDF() {
    const btn = document.getElementById('downloadAsmPdfBtn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating…'; }

    try {
        const res  = await fetch('/api/assembly/?page=1&per_page=500');
        const data = await res.json();
        const items = data.assemblies || [];

        const doc    = _getDoc();
        let   startY = _addHeader(doc, 'Assembly Checklists Report',
            `Total Records: ${data.total || items.length}`);

        // Summary badges
        const counts = { pending: 0, in_progress: 0, completed: 0 };
        items.forEach(a => { if (counts[a.status] !== undefined) counts[a.status]++; });
        const avgProg = items.length
            ? Math.round(items.reduce((s, a) => s + a.progress, 0) / items.length)
            : 0;

        startY = _drawSummaryBadges(doc, startY, [
            { label: 'Total',       value: items.length,        color: BRAND_COLOR  },
            { label: 'Pending',     value: counts.pending,      color: [255,193,7]  },
            { label: 'In Progress', value: counts.in_progress,  color: [13,110,253] },
            { label: 'Completed',   value: counts.completed,    color: [25,135,84]  },
            { label: 'Avg Progress',value: avgProg + '%',        color: ACCENT_COLOR },
        ]);

        startY += 4;

        // Main summary table
        doc.autoTable({
            startY,
            head: [['#', 'Order #', 'Assigned To', 'Progress', 'Status', 'Notes', 'Last Updated']],
            body: items.map(a => [
                `#${a.id}`,
                `#${a.production_id}`,
                a.assigned_to || '—',
                `${a.progress}%`,
                a.status.replace(/_/g,' '),
                (a.notes || '—').substring(0, 55),
                a.updated_at ? a.updated_at.substring(0,10) : '—',
            ]),
            styles:      { fontSize: 8, cellPadding: 3, lineColor: [220,225,230], lineWidth: 0.2 },
            headStyles:  { fillColor: BRAND_COLOR, textColor: [255,255,255], fontStyle: 'bold', fontSize: 8.5 },
            alternateRowStyles: { fillColor: LIGHT_GRAY },
            columnStyles: {
                0: { cellWidth: 12 },
                3: { cellWidth: 20 },
                4: { cellWidth: 26 },
                5: { cellWidth: 55 },
                6: { cellWidth: 28 },
            },
            didDrawCell(data) {
                if (data.section === 'body' && data.column.index === 4) {
                    const rawStatus = items[data.row.index]?.status || '';
                    _statusPill(doc,
                        data.cell.text[0],
                        data.cell.x + 1,
                        data.cell.y + data.cell.height / 2 + 1,
                        _statusColor(rawStatus)
                    );
                    data.cell.text = [];
                }
            },
            margin: { left: 12, right: 12 },
        });

        // ── Per-order checklist detail pages ──────────────────────
        for (const a of items) {
            if (!a.checklist || !a.checklist.length) continue;

            doc.addPage();
            const pw = doc.internal.pageSize.getWidth();

            // Page header
            doc.setFillColor(...BRAND_COLOR);
            doc.rect(0, 0, pw, 14, 'F');
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(10);
            doc.setTextColor(255, 255, 255);
            doc.text(`Assembly Checklist — Order #${a.production_id}  (Assembly #${a.id})`, 12, 9);

            // Assigned / Status / Progress
            doc.setFillColor(...LIGHT_GRAY);
            doc.rect(0, 14, pw, 12, 'F');
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(8.5);
            doc.setTextColor(30, 30, 30);
            doc.text(`Assigned To: ${a.assigned_to || '—'}`, 12, 21);
            doc.text(`Status: ${a.status.replace(/_/g,' ')}   |   Progress: ${a.progress}%`, 80, 21);
            if (a.notes) doc.text(`Notes: ${a.notes.substring(0,90)}`, 12, 27);

            // Progress bar graphic
            const barX = 12, barY = 30, barW = pw - 24, barH = 4;
            doc.setFillColor(220, 225, 230);
            doc.roundedRect(barX, barY, barW, barH, 1, 1, 'F');
            doc.setFillColor(...ACCENT_COLOR);
            doc.roundedRect(barX, barY, barW * a.progress / 100, barH, 1, 1, 'F');

            doc.autoTable({
                startY: 38,
                head: [['#', 'Checklist Item', 'Status']],
                body: a.checklist.map((item, i) => [
                    i + 1,
                    item.item,
                    item.done ? '✔ Done' : '✘ Pending',
                ]),
                styles:     { fontSize: 8.5, cellPadding: 3.5 },
                headStyles: { fillColor: ACCENT_COLOR, textColor: [255,255,255], fontStyle: 'bold' },
                alternateRowStyles: { fillColor: LIGHT_GRAY },
                columnStyles: {
                    0: { cellWidth: 12, halign: 'center' },
                    2: { cellWidth: 30, halign: 'center' },
                },
                didDrawCell(data) {
                    if (data.section === 'body' && data.column.index === 2) {
                        const done  = a.checklist[data.row.index]?.done;
                        const color = done ? [25,135,84] : [220,53,69];
                        doc.setTextColor(...color);
                        doc.setFont('helvetica', 'bold');
                        doc.setFontSize(8.5);
                        doc.text(data.cell.text[0], data.cell.x + data.cell.width / 2,
                            data.cell.y + data.cell.height / 2 + 1.5, { align: 'center' });
                        doc.setTextColor(30, 30, 30);
                        doc.setFont('helvetica', 'normal');
                        data.cell.text = [];
                    }
                },
                margin: { left: 12, right: 12 },
            });
        }

        _addFooter(doc);
        doc.save(`Testiny_AssemblyChecklists_${_dateStamp()}.pdf`);
        showToast('Assembly PDF downloaded', 'success');
    } catch (err) {
        console.error(err);
        showToast('Failed to generate PDF', 'error');
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-file-pdf"></i> Download PDF'; }
    }
}

/* ══════════════════════════════════════════════════════════════
   3. ELECTRICAL TESTS PDF
   ══════════════════════════════════════════════════════════════ */
async function downloadElectricalPDF() {
    const btn = document.getElementById('downloadElecPdfBtn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating…'; }

    try {
        const res  = await fetch('/api/electrical/?page=1&per_page=500');
        const data = await res.json();
        const tests = data.tests || [];

        const doc    = _getDoc();
        let   startY = _addHeader(doc, 'Electrical Test Records',
            `Total Records: ${data.total || tests.length}`);

        // Summary badges
        const counts = { pending: 0, passed: 0, failed: 0 };
        tests.forEach(t => { if (counts[t.test_status] !== undefined) counts[t.test_status]++; });
        const passRate = tests.length
            ? Math.round(counts.passed / tests.length * 100) + '%'
            : '0%';

        startY = _drawSummaryBadges(doc, startY, [
            { label: 'Total Tests', value: tests.length,    color: BRAND_COLOR  },
            { label: 'Pending',     value: counts.pending,  color: [255,193,7]  },
            { label: 'Passed',      value: counts.passed,   color: [25,135,84]  },
            { label: 'Failed',      value: counts.failed,   color: [220,53,69]  },
            { label: 'Pass Rate',   value: passRate,         color: ACCENT_COLOR },
        ]);

        startY += 4;

        doc.autoTable({
            startY,
            head: [['#', 'Order #', 'Panel Type', 'PLC Type', 'Voltage', 'Test Date', 'Result', 'Tested By', 'Remarks']],
            body: tests.map(t => [
                `#${t.id}`,
                `#${t.production_id}`,
                t.panel_type  || '—',
                t.plc_type    || '—',
                t.voltage     || '—',
                t.test_date   || '—',
                t.test_status,
                t.tested_by   || '—',
                (t.remarks || '—').substring(0, 55),
            ]),
            styles:     { fontSize: 7.5, cellPadding: 3, lineColor: [220,225,230], lineWidth: 0.2 },
            headStyles: { fillColor: BRAND_COLOR, textColor: [255,255,255], fontStyle: 'bold', fontSize: 8 },
            alternateRowStyles: { fillColor: LIGHT_GRAY },
            columnStyles: {
                0: { cellWidth: 12 },
                1: { cellWidth: 18 },
                6: { cellWidth: 22 },
                8: { cellWidth: 52 },
            },
            didDrawCell(data) {
                if (data.section === 'body' && data.column.index === 6) {
                    const rawStatus = tests[data.row.index]?.test_status || '';
                    _statusPill(doc,
                        data.cell.text[0],
                        data.cell.x + 1,
                        data.cell.y + data.cell.height / 2 + 1,
                        _statusColor(rawStatus)
                    );
                    data.cell.text = [];
                }
            },
            margin: { left: 12, right: 12 },
        });

        _addFooter(doc);
        doc.save(`Testiny_ElectricalTests_${_dateStamp()}.pdf`);
        showToast('Electrical PDF downloaded', 'success');
    } catch (err) {
        console.error(err);
        showToast('Failed to generate PDF', 'error');
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-file-pdf"></i> Download PDF'; }
    }
}

/* ── utility ─────────────────────────────────────────────────── */
function _dateStamp() {
    return new Date().toISOString().slice(0, 10);
}

/* ── portrait doc helper (for reports) ──────────────────────── */
function _getPortraitDoc() {
    const { jsPDF } = window.jspdf;
    return new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
}

function _addPortraitHeader(doc, title, subtitle) {
    const pw = doc.internal.pageSize.getWidth();
    doc.setFillColor(...BRAND_COLOR);
    doc.rect(0, 0, pw, 18, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.setTextColor(255, 255, 255);
    doc.text('TESTINY', 12, 11.5);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    const now = new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
    doc.text(`Generated: ${now}`, pw - 12, 11.5, { align: 'right' });
    doc.setFillColor(...ACCENT_COLOR);
    doc.rect(0, 18, pw, 2, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(15);
    doc.setTextColor(...BRAND_COLOR);
    doc.text(title, 12, 31);
    if (subtitle) {
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8.5);
        doc.setTextColor(...MID_GRAY);
        doc.text(subtitle, 12, 38);
    }
    return 44;
}

/* ══════════════════════════════════════════════════════════════
   4a. INDIVIDUAL REPORT PDF  (called from per-card button)
   ══════════════════════════════════════════════════════════════ */
async function downloadReportPDF(type) {
    const btnMap = { enquiries: 'dlEnquiriesBtn', stock: 'dlStockBtn', production: 'dlProductionBtn' };
    const btn    = document.getElementById(btnMap[type]);
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'; }

    try {
        const doc = _getPortraitDoc();

        if (type === 'enquiries') {
            await _buildEnquiriesSection(doc, true);
        } else if (type === 'stock') {
            await _buildStockSection(doc, true);
        } else if (type === 'production') {
            await _buildProductionSummarySection(doc, true);
        }

        _addFooter(doc);
        doc.save(`Testiny_Report_${type}_${_dateStamp()}.pdf`);
        showToast('Report downloaded', 'success');
    } catch (err) {
        console.error(err);
        showToast('Failed to generate report PDF', 'error');
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-download"></i>'; }
    }
}

/* ══════════════════════════════════════════════════════════════
   4b. ALL REPORTS PDF  (master button)
   ══════════════════════════════════════════════════════════════ */
async function downloadAllReportsPDF() {
    const btn = document.getElementById('downloadAllReportsBtn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating…'; }

    try {
        const doc = _getPortraitDoc();
        let isFirst = true;

        // Page 1: Enquiries
        await _buildEnquiriesSection(doc, isFirst);
        isFirst = false;

        // Page 2: Stock
        doc.addPage();
        await _buildStockSection(doc, true);

        // Page 3: Production Summary
        doc.addPage();
        await _buildProductionSummarySection(doc, true);

        _addFooter(doc);
        doc.save(`Testiny_AllReports_${_dateStamp()}.pdf`);
        showToast('All Reports PDF downloaded', 'success');
    } catch (err) {
        console.error(err);
        showToast('Failed to generate PDF', 'error');
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-file-pdf"></i> Download All Reports'; }
    }
}

/* ══════════════════════════════════════════════════════════════
   REPORT SECTION BUILDERS  (shared between single + all)
   ══════════════════════════════════════════════════════════════ */

async function _buildEnquiriesSection(doc, addHeader = true) {
    const res  = await fetch('/api/admin/reports/enquiries');
    const rows = await res.json();
    const pw   = doc.internal.pageSize.getWidth();

    let y = 10;
    if (addHeader) {
        y = _addPortraitHeader(doc, 'Monthly Enquiries Report',
            'Enquiry counts, win rate and pipeline value for the last 12 months');
    }

    if (!rows.length) {
        doc.setFont('helvetica', 'italic');
        doc.setFontSize(9);
        doc.setTextColor(...MID_GRAY);
        doc.text('No enquiry data available.', 12, y + 10);
        return;
    }

    // KPI summary badges from totals
    const totalEnq = rows.reduce((s, r) => s + Number(r.total), 0);
    const totalWon = rows.reduce((s, r) => s + Number(r.won),   0);
    const totalLost= rows.reduce((s, r) => s + Number(r.lost),  0);
    const totalVal = rows.reduce((s, r) => s + Number(r.pipeline_value || 0), 0);
    const winRate  = totalEnq ? Math.round(totalWon / totalEnq * 100) + '%' : '0%';

    y = _drawSummaryBadges(doc, y, [
        { label: 'Total Enquiries', value: totalEnq,                            color: BRAND_COLOR  },
        { label: 'Won',             value: totalWon,                            color: [25,135,84]  },
        { label: 'Lost',            value: totalLost,                           color: [220,53,69]  },
        { label: 'Win Rate',        value: winRate,                             color: ACCENT_COLOR },
        { label: 'Pipeline (₹)',    value: '₹' + _shortNum(totalVal),           color: [102,16,242] },
    ]);

    y += 4;

    doc.autoTable({
        startY: y,
        head:   [['Month', 'Total', 'Won', 'Lost', 'Pipeline Value (₹)']],
        body:   rows.map(r => [
            r.month,
            r.total,
            r.won,
            r.lost,
            Number(r.pipeline_value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 }),
        ]),
        styles:     { fontSize: 9, cellPadding: 3.5, lineColor: [220,225,230], lineWidth: 0.2 },
        headStyles: { fillColor: BRAND_COLOR, textColor: [255,255,255], fontStyle: 'bold' },
        alternateRowStyles: { fillColor: LIGHT_GRAY },
        columnStyles: {
            0: { cellWidth: 32 },
            1: { cellWidth: 28, halign: 'center' },
            2: { cellWidth: 28, halign: 'center' },
            3: { cellWidth: 28, halign: 'center' },
        },
        didDrawCell(data) {
            if (data.section === 'body' && data.column.index === 2) {
                doc.setTextColor(25, 135, 84);
                doc.setFont('helvetica', 'bold');
                doc.setFontSize(9);
                doc.text(String(data.cell.text[0]), data.cell.x + data.cell.width / 2,
                    data.cell.y + data.cell.height / 2 + 1.5, { align: 'center' });
                doc.setTextColor(30, 30, 30);
                doc.setFont('helvetica', 'normal');
                data.cell.text = [];
            }
            if (data.section === 'body' && data.column.index === 3) {
                doc.setTextColor(220, 53, 69);
                doc.setFont('helvetica', 'bold');
                doc.setFontSize(9);
                doc.text(String(data.cell.text[0]), data.cell.x + data.cell.width / 2,
                    data.cell.y + data.cell.height / 2 + 1.5, { align: 'center' });
                doc.setTextColor(30, 30, 30);
                doc.setFont('helvetica', 'normal');
                data.cell.text = [];
            }
        },
        margin: { left: 12, right: 12 },
    });
}

async function _buildStockSection(doc, addHeader = true) {
    const res  = await fetch('/api/admin/reports/stock');
    const rows = await res.json();

    let y = 10;
    if (addHeader) {
        y = _addPortraitHeader(doc, 'Stock Usage Report (Last 30 Days)',
            'Consumption and replenishment activity per product');
    }

    if (!rows.length) {
        doc.setFont('helvetica', 'italic');
        doc.setFontSize(9);
        doc.setTextColor(...MID_GRAY);
        doc.text('No stock movements in the last 30 days.', 12, y + 10);
        return;
    }

    const totalConsumed = rows.reduce((s, r) => s + Number(r.consumed || 0), 0);
    const totalAdded    = rows.reduce((s, r) => s + Number(r.added    || 0), 0);
    const lowStock      = rows.filter(r => Number(r.current_stock) < Number(r.reorder_level)).length;

    y = _drawSummaryBadges(doc, y, [
        { label: 'Products Tracked', value: rows.length,    color: BRAND_COLOR  },
        { label: 'Total Consumed',   value: totalConsumed,  color: [220,53,69]  },
        { label: 'Total Added',      value: totalAdded,     color: [25,135,84]  },
        { label: 'Low Stock Items',  value: lowStock,        color: [255,193,7]  },
    ]);

    y += 4;

    doc.autoTable({
        startY: y,
        head:   [['Product', 'Consumed', 'Added', 'Current Stock', 'Reorder Level', 'Status']],
        body:   rows.map(r => [
            r.product_name,
            r.consumed || 0,
            r.added    || 0,
            r.current_stock,
            r.reorder_level,
            Number(r.current_stock) < Number(r.reorder_level) ? 'Low Stock' : 'OK',
        ]),
        styles:     { fontSize: 9, cellPadding: 3.5, lineColor: [220,225,230], lineWidth: 0.2 },
        headStyles: { fillColor: BRAND_COLOR, textColor: [255,255,255], fontStyle: 'bold' },
        alternateRowStyles: { fillColor: LIGHT_GRAY },
        columnStyles: {
            1: { halign: 'center' },
            2: { halign: 'center' },
            3: { halign: 'center' },
            4: { halign: 'center' },
            5: { cellWidth: 28, halign: 'center' },
        },
        didDrawCell(data) {
            if (data.section === 'body' && data.column.index === 5) {
                const isLow  = data.cell.text[0] === 'Low Stock';
                const color  = isLow ? [220,53,69] : [25,135,84];
                _statusPill(doc,
                    data.cell.text[0],
                    data.cell.x + (data.cell.width - 24) / 2,
                    data.cell.y + data.cell.height / 2 + 1,
                    color
                );
                data.cell.text = [];
            }
        },
        margin: { left: 12, right: 12 },
    });
}

async function _buildProductionSummarySection(doc, addHeader = true) {
    const res  = await fetch('/api/admin/reports/production');
    const rows = await res.json();

    let y = 10;
    if (addHeader) {
        y = _addPortraitHeader(doc, 'Production Summary Report',
            'Order counts, average completion progress and total units by status');
    }

    if (!rows.length) {
        doc.setFont('helvetica', 'italic');
        doc.setFontSize(9);
        doc.setTextColor(...MID_GRAY);
        doc.text('No production orders yet.', 12, y + 10);
        return;
    }

    const totalOrders = rows.reduce((s, r) => s + Number(r.count      || 0), 0);
    const totalUnits  = rows.reduce((s, r) => s + Number(r.total_units || 0), 0);
    const avgProgress = rows.reduce((s, r) => s + Number(r.avg_progress || 0), 0) / rows.length;
    const completed   = rows.find(r => r.status === 'completed');
    const compRate    = totalOrders ? Math.round(Number((completed || {}).count || 0) / totalOrders * 100) + '%' : '0%';

    y = _drawSummaryBadges(doc, y, [
        { label: 'Total Orders',    value: totalOrders,               color: BRAND_COLOR  },
        { label: 'Total Units',     value: totalUnits,                color: ACCENT_COLOR },
        { label: 'Avg Progress',    value: Math.round(avgProgress) + '%', color: [13,110,253] },
        { label: 'Completion Rate', value: compRate,                  color: [25,135,84]  },
    ]);

    y += 4;

    doc.autoTable({
        startY: y,
        head:   [['Status', 'Order Count', 'Total Units', 'Avg. Progress']],
        body:   rows.map(r => [
            r.status.replace(/_/g, ' '),
            r.count,
            r.total_units || 0,
            Math.round(r.avg_progress || 0) + '%',
        ]),
        styles:     { fontSize: 10, cellPadding: 4, lineColor: [220,225,230], lineWidth: 0.2 },
        headStyles: { fillColor: BRAND_COLOR, textColor: [255,255,255], fontStyle: 'bold' },
        alternateRowStyles: { fillColor: LIGHT_GRAY },
        columnStyles: {
            0: { cellWidth: 52 },
            1: { halign: 'center' },
            2: { halign: 'center' },
            3: { halign: 'center' },
        },
        didDrawCell(data) {
            if (data.section === 'body' && data.column.index === 0) {
                const rawStatus = rows[data.row.index]?.status || '';
                _statusPill(doc,
                    data.cell.text[0],
                    data.cell.x + 2,
                    data.cell.y + data.cell.height / 2 + 1,
                    _statusColor(rawStatus)
                );
                data.cell.text = [];
            }
        },
        margin: { left: 12, right: 12 },
    });

    // Visual bar chart of order counts
    const lastY = doc.lastAutoTable.finalY + 10;
    const pw    = doc.internal.pageSize.getWidth();
    const maxCount = Math.max(...rows.map(r => Number(r.count)));
    const barMaxW  = pw - 60;

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.setTextColor(...BRAND_COLOR);
    doc.text('Order Count by Status', 12, lastY);

    rows.forEach((r, i) => {
        const barY   = lastY + 8 + i * 12;
        const barW   = maxCount > 0 ? (Number(r.count) / maxCount) * barMaxW : 0;
        const color  = _statusColor(r.status);

        // Label
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8.5);
        doc.setTextColor(30, 30, 30);
        const label = r.status.replace(/_/g,' ');
        doc.text(label.charAt(0).toUpperCase() + label.slice(1), 12, barY + 4);

        // Track
        doc.setFillColor(230, 233, 240);
        doc.roundedRect(46, barY, barMaxW, 7, 1.5, 1.5, 'F');

        // Fill
        if (barW > 0) {
            doc.setFillColor(...color);
            doc.roundedRect(46, barY, barW, 7, 1.5, 1.5, 'F');
        }

        // Value label
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7.5);
        doc.setTextColor(255, 255, 255);
        if (barW > 12) {
            doc.text(String(r.count), 46 + barW - 5, barY + 5, { align: 'right' });
        } else {
            doc.setTextColor(30, 30, 30);
            doc.text(String(r.count), 46 + barW + 3, barY + 5);
        }
    });
}

/* ── number shortener ────────────────────────────────────────── */
function _shortNum(n) {
    if (n >= 1e7)  return (n / 1e7).toFixed(1) + 'Cr';
    if (n >= 1e5)  return (n / 1e5).toFixed(1) + 'L';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return String(Math.round(n));
}
