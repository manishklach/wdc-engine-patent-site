const header = document.querySelector("[data-header]");
const navToggle = document.querySelector("[data-nav-toggle]");
const siteNav = document.getElementById("site-nav");
const navLinks = Array.from(document.querySelectorAll("[data-nav-link]"));
const sections = Array.from(document.querySelectorAll("[data-section]"));
const counterGroups = document.querySelectorAll("[data-counter-group]");
const normalizeButton = document.querySelector("[data-normalize-trigger]");
const copyButtons = document.querySelectorAll("[data-copy-target]");

const syncHeaderState = () => {
  if (!header) return;
  header.classList.toggle("is-scrolled", window.scrollY > 8);
};

syncHeaderState();
window.addEventListener("scroll", syncHeaderState, { passive: true });

if (navToggle && siteNav) {
  navToggle.addEventListener("click", () => {
    const expanded = navToggle.getAttribute("aria-expanded") === "true";
    navToggle.setAttribute("aria-expanded", String(!expanded));
    siteNav.classList.toggle("is-open", !expanded);
  });
}

navLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    const href = link.getAttribute("href") || "";
    if (!href.startsWith("#")) return;
    const target = document.querySelector(href);
    if (!target) return;
    event.preventDefault();
    const y = target.getBoundingClientRect().top + window.scrollY - 82;
    window.scrollTo({ top: y, behavior: "smooth" });
    siteNav?.classList.remove("is-open");
    navToggle?.setAttribute("aria-expanded", "false");
  });
});

const setActiveNav = (id) => {
  navLinks.forEach((link) => link.classList.toggle("is-active", link.getAttribute("href") === `#${id}`));
};

if ("IntersectionObserver" in window && sections.length) {
  const sectionObserver = new IntersectionObserver(
    (entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible?.target?.id) setActiveNav(visible.target.id);
    },
    { rootMargin: "-35% 0px -45% 0px", threshold: [0.2, 0.4, 0.6] }
  );
  sections.forEach((section) => sectionObserver.observe(section));
}

const formatCounterValue = (value, node) => {
  const decimals = Number(node.dataset.decimals || 0);
  const prefix = node.dataset.prefix || "";
  const suffix = node.dataset.suffix || "";
  const format = node.dataset.format || "";
  let rendered = decimals ? value.toFixed(decimals) : Math.round(value).toString();
  if (format === "integer") rendered = Math.round(value).toLocaleString("en-US");
  return `${prefix}${rendered}${suffix}`;
};

const animateCounter = (node) => {
  if (node.dataset.animated === "true") return;
  node.dataset.animated = "true";
  const target = Number(node.dataset.target || 0);
  const duration = 1400;
  const start = performance.now();

  const tick = (now) => {
    const elapsed = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - elapsed, 3);
    node.innerHTML = formatCounterValue(target * eased, node);
    if (elapsed < 1) requestAnimationFrame(tick);
    else node.innerHTML = formatCounterValue(target, node);
  };

  requestAnimationFrame(tick);
};

if ("IntersectionObserver" in window) {
  const counterObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.querySelectorAll("[data-counter]").forEach(animateCounter);
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.3 }
  );
  counterGroups.forEach((group) => counterObserver.observe(group));
} else {
  document.querySelectorAll("[data-counter]").forEach(animateCounter);
}

const timelineWindow = document.querySelector("[data-window]");
const executionArrow = document.querySelector("[data-execution]");
const multiplierBadge = document.querySelector("[data-multiplier]");
const bubbles = {
  a: document.querySelector('[data-bubble="a"]'),
  b: document.querySelector('[data-bubble="b"]'),
  c: document.querySelector('[data-bubble="c"]')
};
const fanouts = {
  a: document.querySelector('[data-fanout="a"]'),
  b: document.querySelector('[data-fanout="b"]'),
  c: document.querySelector('[data-fanout="c"]')
};
let timelineTimers = [];

const resetTimeline = () => {
  timelineTimers.forEach((timer) => window.clearTimeout(timer));
  timelineTimers = [];
  timelineWindow?.classList.remove("is-active");
  [...Object.values(bubbles), ...Object.values(fanouts), executionArrow, multiplierBadge].forEach((node) => node?.classList.remove("is-visible"));
};

const playTimeline = () => {
  resetTimeline();
  timelineWindow?.classList.add("is-active");
  timelineTimers.push(window.setTimeout(() => bubbles.a?.classList.add("is-visible"), 250));
  timelineTimers.push(window.setTimeout(() => bubbles.b?.classList.add("is-visible"), 1100));
  timelineTimers.push(window.setTimeout(() => bubbles.c?.classList.add("is-visible"), 1500));
  timelineTimers.push(window.setTimeout(() => executionArrow?.classList.add("is-visible"), 2200));
  timelineTimers.push(window.setTimeout(() => fanouts.a?.classList.add("is-visible"), 2550));
  timelineTimers.push(window.setTimeout(() => fanouts.b?.classList.add("is-visible"), 2700));
  timelineTimers.push(window.setTimeout(() => fanouts.c?.classList.add("is-visible"), 2850));
  timelineTimers.push(window.setTimeout(() => multiplierBadge?.classList.add("is-visible"), 3000));
};

document.querySelector("[data-timeline-play]")?.addEventListener("click", playTimeline);
document.querySelector("[data-timeline-reset]")?.addEventListener("click", playTimeline);

const sqlSources = {
  a: "SELECT customer_id, SUM(amount) AS total FROM transactions WHERE DATE(created_at) >= '2024-01-01' AND region = 'West' GROUP BY customer_id;",
  b: "select CUSTOMER_ID,sum(AMOUNT) total from TRANSACTIONS t where t.region='West' and date(t.created_at)>='2024-01-01' group by CUSTOMER_ID;",
  c: "SELECT c_id, SUM(amt) FROM txns WHERE txns.region = 'West' AND DATE(txns.created_at) >= '2024-01-01' GROUP BY c_id;"
};

const sqlKeywordPattern = /\b(select|from|where|group by|sum|as|and|date)\b/gi;
const sqlPlaceholderPattern = /(:DATE_\d+|:STR_\d+)/g;
const sqlStringPattern = /'[^']*'/g;
const escapeHtml = (value) => value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

const highlightSql = (value) => {
  let output = escapeHtml(value);
  output = output.replace(sqlStringPattern, (match) => `<span class="sql-string">${escapeHtml(match)}</span>`);
  output = output.replace(sqlPlaceholderPattern, '<span class="sql-placeholder">$1</span>');
  output = output.replace(sqlKeywordPattern, (match) => `<span class="sql-keyword">${match.toLowerCase()}</span>`);
  return output;
};

const normalizeSql = (source) => {
  let query = source.toLowerCase();
  query = query.replace(/\s+/g, " ").trim();
  query = query.replace(/transactions\s+t\b/g, "transactions");
  query = query.replace(/\bt\./g, "");
  query = query.replace(/\btxns\./g, "");
  query = query.replace(/\s*=\s*/g, " = ");
  query = query.replace(/\s*>=\s*/g, " >= ");
  query = query.replace(/,sum/g, ", sum");
  query = query.replace(/\(amount\) total/g, "(amount) as total");
  const whereMatch = query.match(/where (.+?) group by/);
  if (whereMatch) {
    const predicates = whereMatch[1].split(/\s+and\s+/).map((item) => item.trim()).sort((a, b) => a.localeCompare(b));
    query = query.replace(whereMatch[1], predicates.join(" and "));
  }
  query = query.replace(/'2024-01-01'/g, ":DATE_1");
  query = query.replace(/'west'/g, ":STR_1");
  return query;
};

const fakeHash = (value) => {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  const hex = (hash >>> 0).toString(16).padStart(8, "0");
  return `${hex}${hex.split("").reverse().join("")}`.slice(0, 16);
};

Object.entries(sqlSources).forEach(([key, value]) => {
  const node = document.querySelector(`[data-sql-source="${key}"]`);
  if (node) node.innerHTML = highlightSql(value);
});

normalizeButton?.addEventListener("click", () => {
  const canonical = { a: normalizeSql(sqlSources.a), b: normalizeSql(sqlSources.b), c: normalizeSql(sqlSources.c) };
  Object.entries(canonical).forEach(([key, value]) => {
    const outputNode = document.querySelector(`[data-output="${key}"]`);
    const hashNode = document.querySelector(`[data-hash="${key}"]`);
    if (outputNode) outputNode.innerHTML = highlightSql(value);
    if (hashNode) hashNode.textContent = fakeHash(value);
  });
  const badgeA = document.querySelector('[data-badge="a"]');
  const badgeB = document.querySelector('[data-badge="b"]');
  const badgeC = document.querySelector('[data-badge="c"]');
  badgeA?.classList.add("is-match");
  badgeB?.classList.add("is-match");
  badgeC?.classList.add("is-near");
  if (badgeA) badgeA.textContent = "✓ MATCH";
  if (badgeB) badgeB.textContent = "✓ MATCH";
  if (badgeC) badgeC.textContent = "≈ NEAR MATCH (cosine: 0.97)";
});

const copyText = async (text) => {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return true;
  }
  const helper = document.createElement("textarea");
  helper.value = text;
  helper.setAttribute("readonly", "");
  helper.style.position = "absolute";
  helper.style.left = "-9999px";
  document.body.appendChild(helper);
  helper.select();
  const success = document.execCommand("copy");
  document.body.removeChild(helper);
  return success;
};

copyButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    const targetId = button.getAttribute("data-copy-target");
    const source = targetId ? document.getElementById(targetId) : null;
    if (!source) return;
    const originalLabel = button.textContent;
    try {
      await copyText(source.textContent || "");
      button.textContent = "Copied";
      window.setTimeout(() => { button.textContent = originalLabel; }, 1400);
    } catch (error) {
      button.textContent = "Unable to copy";
      window.setTimeout(() => { button.textContent = originalLabel; }, 1400);
    }
  });
});
