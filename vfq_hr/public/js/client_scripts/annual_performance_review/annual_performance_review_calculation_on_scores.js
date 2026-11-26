// Client Script: Annual Performance Review Calculation on Scores (Annual Performance Review, Form)
frappe.ui.form.on("Annual Performance Review", {
    refresh(frm) {
        calculate_score(frm);
    },

    technical_skills: calculate_score,
    communication: calculate_score,
    teamwork: calculate_score,
    leadership: calculate_score,
    problem_solving: calculate_score,
    innovation: calculate_score
});

frappe.ui.form.on("Annual Review KRA", {
    rating: function(frm) {
        calculate_score(frm);
    },
    weightage: function(frm) {
        calculate_score(frm);
    }
});

function calculate_score(frm) {

    // KRA Score
    let total_weighted = 0;
    let total_weight = 0;

    (frm.doc.kra_evaluation || []).forEach(row => {

        total_weighted +=
            (row.weightage || 0) *
            (row.rating || 0);

        total_weight +=
            (row.weightage || 0);
    });

    let kra_score = 0;

    if (total_weight > 0) {
        kra_score =
            total_weighted / total_weight;
    }

    // Competency Score

    let competencies = [
        frm.doc.technical_skills || 0,
        frm.doc.communication || 0,
        frm.doc.teamwork || 0,
        frm.doc.leadership || 0,
        frm.doc.problem_solving || 0,
        frm.doc.innovation || 0
    ];

    let competency_score =
        competencies.reduce((a,b)=>a+b,0)
        / competencies.length;

    // Final Rating

    let final_rating =
        (kra_score * 0.7) +
        (competency_score * 0.3);

    frm.set_value(
        "kra_score",
        Number(kra_score.toFixed(2))
    );

    frm.set_value(
        "competency_score",
        Number(competency_score.toFixed(2))
    );

    frm.set_value(
        "final_rating",
        Number(final_rating.toFixed(2))
    );

    // Rating Band

    let band = "";

    if (final_rating >= 4.5) {
        band = "Outstanding";
    }
    else if (final_rating >= 4.0) {
        band = "Exceeds Expectations";
    }
    else if (final_rating >= 3.0) {
        band = "Meets Expectations";
    }
    else if (final_rating >= 2.0) {
        band = "Needs Improvement";
    }
    else {
        band = "Unsatisfactory";
    }

    frm.set_value(
        "performance_band",
        band
    );
}
