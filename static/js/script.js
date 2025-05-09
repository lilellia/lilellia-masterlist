/**
 * Return an array of the ID for every script on the page.
 * @returns {Array<String>}
 */
const getScriptIds = function () {
  return Array.from(document.querySelectorAll(".script-data")).map((element) => element.id);
};

/**
 * Extract tag values from a string of the form "[tag1] [tag2] [tag3] ..."
 * @param {*} tagString - string in the form of "[tag1] [tag2] [tag3] ..."
 * @returns {Array<String>} the array of strings
 */
const extractTags = function (tagString) {
  const matches = Array.from(tagString.matchAll(/\[(.*?)\]/g));
  return matches.map((m) => m[1]);
};

/**
 * Extract a list of speakers for the given audience tag.
 * Example: extractSpeakers("FFM4A") --> ["F", "F", "M"]
 * @param {String} audienceTag - the audience tag
 * @returns {Array<String>} - an array of speaker abbreviations
 */
const extractSpeakers = function (audienceTag) {
  // audienceTag = MTMFNBTF4A
  // -> speaker = "MTMFNBTF"
  const speaker = audienceTag.split("4")[0];

  // recognised speaker tags
  // TF, TM, TA = transfem, transmasc, transany
  // F, M, A = fem, masc, any
  // NB = nonbinary
  const matches = speaker.matchAll(/TF|TM|TA|M|F|NB|A/g);

  return Array.from(matches);
};

function getScriptLinks(scriptId) {
  const root = document.getElementById(scriptId).querySelector("div.script-links");

  if (root === null) {
    return [];
  }

  let results = [];
  for (const a of root.querySelectorAll("div.script-links a")) {
    results.push(a.href);
  }

  return results;
}

/**
 *
 * @param {String} scriptId - the id of the script to check
 * @param {String} filterText - the text to filter against
 * @returns {boolean} - whether the given script matches the given text filter
 */
function matchesTextFilter(scriptId, filterText) {
  if (filterText === "") {
    // all scripts match the empty filter
    return true;
  }

  const element = document.getElementById(scriptId);
  if (element.getAttribute("data-title").toLowerCase().includes(filterText)) {
    return true;
  }

  if (element.getAttribute("data-summary").toLowerCase().includes(filterText)) {
    return true;
  }

  for (const tag of extractTags(element.getAttribute("data-tags").toLowerCase())) {
    if (tag.toLowerCase().includes(filterText)) {
      return true;
    }
  }

  return false;
}

/**
 * Determine whether the given series value matches the target value.
 * @param {String} target - the "target" value for the series title
 * @param {String} actual - the "actual" value for the series title
 * @returns {boolean} whether the script matches the series value
 */
const matchesSeries = function (target, actual) {
  if (target === "") {
    // empty string for target means we have no filter
    // i.e., everything passes
    return true;
  }

  if (target === "(one-shots only)") {
    // only those which do not have series data will pass
    return actual === "";
  }

  // we know that the target is some particular series
  if (actual === "") {
    return false;
  }

  return actual === target;
};

/**
 * Return an array of values checked within the given div.
 * @param {String} divId - the ID of the div to look within
 * @returns {Array<String>} - the values of all checked checkboxes
 */
function getCheckedIn(divId) {
  const checkboxes = document.querySelectorAll(`div#${divId} input[type=checkbox]`);
  let values = [];

  for (const checkbox of checkboxes) {
    if (checkbox.checked) {
      values.push(checkbox.value);
    }
  }

  return values;
}

/**
 * Determine whether two arrays share any elements.
 * @param {Array} arr1
 * @param {Array} arr2
 * @returns {boolean} whether the arrays share at least one element
 */
function doArraysOverlap(arr1, arr2) {
  const set1 = new Set(arr1);
  const set2 = new Set(arr2);

  return set1.intersection(set2).size > 0;
}

function filterScripts() {
  const filterText = document.getElementById("filterInput").value.trim().toLowerCase();
  const minSpokenWords = document.getElementById("filterWordCountMin").valueAsNumber;
  const maxSpokenWords = document.getElementById("filterWordCountMax").valueAsNumber;
  const seriesFilter = document.getElementById("seriesFilter").value;
  const audienceTagFilter = getCheckedIn("audienceTagFilter");
  const filledByFilter = document.getElementById("filledByFilter").value;
  const numSpeakersFilter = getCheckedIn("numSpeakersFilter");
  const filledStatusFilter = getCheckedIn("filledStatusFilter");
  const nsfwStatusFilter = getCheckedIn("nsfwFilter");

  let scriptIds = getScriptIds();

  let scriptsShown = 0;
  let fillsShown = 0;

  for (const id of scriptIds) {
    const script = document.getElementById(id);

    // -----------------------------------------------------------------------------------------------------------
    // filter by title / tags / summary
    // -----------------------------------------------------------------------------------------------------------
    if (!matchesTextFilter(id, filterText)) {
      script.style.display = "none";
      continue;
    }

    // -----------------------------------------------------------------------------------------------------------
    // filter by word count
    // -----------------------------------------------------------------------------------------------------------
    const wordcount = +script.getAttribute("data-wordcount");

    if (minSpokenWords !== NaN && wordcount < minSpokenWords) {
      script.style.display = "none";
      continue;
    }

    if (maxSpokenWords !== NaN && wordcount > maxSpokenWords) {
      script.style.display = "none";
      continue;
    }

    // -----------------------------------------------------------------------------------------------------------
    // filter by filled status
    // -----------------------------------------------------------------------------------------------------------
    const numFills = +script.getAttribute("data-numFills");
    if (numFills === 0 && !filledStatusFilter.includes("unfilled")) {
      script.style.display = "none";
      continue;
    }

    if (numFills > 0 && !filledStatusFilter.includes("filled")) {
      script.style.display = "none";
      continue;
    }

    // -----------------------------------------------------------------------------------------------------------
    // filter by series
    // -----------------------------------------------------------------------------------------------------------
    const series = script.getAttribute("data-series");
    if (!matchesSeries(seriesFilter, series)) {
      script.style.display = "none";
      continue;
    }

    // -----------------------------------------------------------------------------------------------------------
    // filter by audience / number of speakers
    // -----------------------------------------------------------------------------------------------------------
    const audiences = script.getAttribute("data-audience").split(",");
    const numSpeakers = audiences.map((audience) => extractSpeakers(audience).length.toString());

    if (!doArraysOverlap(numSpeakersFilter, numSpeakers)) {
      script.style.display = "none";
      continue;
    }

    if (!doArraysOverlap(audiences, audienceTagFilter)) {
      script.style.display = "none";
      continue;
    }

    // -----------------------------------------------------------------------------------------------------------
    // filter by VAs filled
    // -----------------------------------------------------------------------------------------------------------
    const filledBy = script.getAttribute("data-VAsFilled").split("===");
    if (filledByFilter !== "" && !filledBy.includes(filledByFilter)) {
      script.style.display = "none";
      continue;
    }

    // -----------------------------------------------------------------------------------------------------------
    // filter by SFW/NSFW status
    // -----------------------------------------------------------------------------------------------------------
    nsfwStatus = script.getAttribute("data-nsfw");
    if (!nsfwStatusFilter.includes(nsfwStatus)) {
      script.style.display = "none";
      continue;
    }

    script.style.display = "block";
    scriptsShown += 1;
    fillsShown += numFills;
  }

  document.getElementById("numScripts").textContent = scriptsShown;
  document.getElementById("numFills").textContent = fillsShown;
}

function scriptToMarkdown(scriptId) {
  const script = document.getElementById(scriptId);

  const title = script.getAttribute("data-title");
  const summary = script.getAttribute("data-summary");
  const link = script.getAttribute("data-link");
  const audience = script.getAttribute("data-audience").split(",")[0];
  const tags = extractTags(script.getAttribute("data-tags"))
    .map((tag) => `\\[${tag.replace(/\n\s+/g, " ").trim()}\\]`)
    .join(" ");

  return `**[${title}](${link})**  \n\\[${audience}\\] ${tags}  \n> _${summary}_`;
}

function copyToClipboard(scriptId) {
  markdown = scriptToMarkdown(scriptId);
  navigator.clipboard.writeText(markdown);
}
