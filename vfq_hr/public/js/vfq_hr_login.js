// Sign-in page branding from Company > Portal Branding (see vfq_hr/branding.py).
(function () {
	var b = window.vfq_hr_branding || {};
	var root = document.body;
	if (b.color) root.style.setProperty("--vfq-brand", b.color);

	function el(tag, cls, text) {
		var e = document.createElement(tag);
		e.className = cls;
		if (text) e.textContent = text; // text only: company-entered values are never rendered as HTML
		return e;
	}

	document.querySelectorAll(".login-content.page-card").forEach(function (card) {
		var section = card.parentElement;
		if (!section || section.querySelector(".vfq-brand-head")) return;
		var head = el("div", "vfq-brand-head");
		if (b.title) head.appendChild(el("div", "vfq-brand-title", b.title));
		if (b.tagline) head.appendChild(el("div", "vfq-brand-tagline", b.tagline));
		section.insertBefore(head, card);
		if (b.note) section.appendChild(el("div", "vfq-brand-note", b.note));
		var logo = card.querySelector(".app-logo");
		if (logo && b.logo) logo.src = b.logo;
	});
})();
