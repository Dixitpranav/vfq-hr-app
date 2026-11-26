// Client Script: CXO Hiring Approval - Approval Timeline (CXO Hiring Approval, Form)
// Approval progress shown to everyone: green = approved, amber = waiting now, grey = not reached yet.
function cxo_timeline_esc(v) { return frappe.utils.escape_html(String(v || '')); }
function cxo_render_timeline(frm) {
    const f = frm.fields_dict.custom_approval_timeline_html;
    if (!f || !f.$wrapper) return;
    if (frm.is_new()) { f.$wrapper.empty(); return; }
    const d = frm.doc;
    const st = d.workflow_state || 'Draft';
    const steps = [
        { label: 'Created (HR)', state: 'Draft', by: d.owner, on: d.creation },
        { label: 'Head of OD', state: 'Pending Head of OD Approval', by: d.custom_hod_approved_by, on: d.custom_hod_approved_on },
        { label: 'CHRO', state: 'Pending CHRO Approval', by: d.custom_chro_approved_by, on: d.custom_chro_approved_on },
        { label: 'CAO', state: 'Pending CAO Approval', by: d.cao_approved_by, on: d.cao_approved_on },
        { label: 'CEO', state: 'Pending CEO Approval', by: d.ceo_approved_by, on: d.ceo_approved_on }
    ];
    const done_states = ['Approved', 'Approved to onboard'];
    let html = '<div class="cxo-tl">';
    steps.forEach(function (s, i) {
        let cls = 'todo', note = 'Not reached yet';
        if (i === 0) { cls = 'done'; note = 'Created'; }
        else if (s.by) { cls = 'done'; note = 'Approved'; }
        else if (st === s.state) { cls = 'now'; note = 'Waiting for approval'; }
        else if (st === 'Rejected') { cls = 'todo'; note = 'Not approved'; }
        else if (done_states.includes(st)) { cls = 'skip'; note = 'Not part of the earlier flow'; }
        const who = s.by ? frappe.user.full_name(s.by) : '';
        const when = s.on ? frappe.datetime.str_to_user(s.on) : '';
        html += '<div class="cxo-tl-step ' + cls + '">'
            + '<div class="cxo-tl-dot">' + (cls === 'done' ? '&#10003;' : (i + 1)) + '</div>'
            + '<div class="cxo-tl-label">' + cxo_timeline_esc(s.label) + '</div>'
            + '<div class="cxo-tl-note">' + cxo_timeline_esc(note) + '</div>'
            + (who ? '<div class="cxo-tl-who">' + cxo_timeline_esc(who) + '</div>' : '')
            + (when ? '<div class="cxo-tl-when">' + cxo_timeline_esc(when) + '</div>' : '')
            + '</div>';
        if (i < steps.length - 1) html += '<div class="cxo-tl-line ' + (cls === 'done' ? 'done' : '') + '"></div>';
    });
    if (st === 'Rejected') html += '<div class="cxo-tl-flag">Rejected</div>';
    html += '</div><style>'
        + '.cxo-tl{display:flex;align-items:flex-start;gap:0;padding:14px 6px 6px;flex-wrap:nowrap;overflow-x:auto}'
        + '.cxo-tl-step{flex:0 0 120px;text-align:center}'
        + '.cxo-tl-dot{width:30px;height:30px;border-radius:50%;margin:0 auto 6px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;background:#e5e7eb;color:#6b7280;border:2px solid #d1d5db}'
        + '.cxo-tl-step.done .cxo-tl-dot{background:#16a34a;border-color:#16a34a;color:#fff}'
        + '.cxo-tl-step.now .cxo-tl-dot{background:#fff7ed;border-color:#f59e0b;color:#b45309}'
        + '.cxo-tl-step.skip .cxo-tl-dot{background:#f3f4f6;border-style:dashed}'
        + '.cxo-tl-label{font-weight:600;font-size:12.5px;color:#111827}'
        + '.cxo-tl-step.todo .cxo-tl-label,.cxo-tl-step.skip .cxo-tl-label{color:#9ca3af}'
        + '.cxo-tl-note{font-size:11px;color:#6b7280}'
        + '.cxo-tl-step.done .cxo-tl-note{color:#16a34a}'
        + '.cxo-tl-step.now .cxo-tl-note{color:#b45309;font-weight:600}'
        + '.cxo-tl-who{font-size:11px;color:#374151;margin-top:2px}'
        + '.cxo-tl-when{font-size:10.5px;color:#9ca3af}'
        + '.cxo-tl-line{flex:1 1 30px;min-width:20px;height:2px;background:#d1d5db;margin-top:15px}'
        + '.cxo-tl-line.done{background:#16a34a}'
        + '.cxo-tl-flag{align-self:center;margin-left:12px;padding:3px 10px;border-radius:12px;background:#fee2e2;color:#b91c1c;font-size:12px;font-weight:600}'
        + '</style>';
    f.$wrapper.html(html);
}
frappe.ui.form.on('CXO Hiring Approval', {
    refresh: cxo_render_timeline,
    workflow_state: cxo_render_timeline
});
