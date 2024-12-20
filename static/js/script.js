function identifyScripts() {
    let scripts = {};

    for (const element of document.getElementsByClassName("script-data")) {
        const id = element.id;
        const title = element.querySelector("p").textContent.trim();        

        scripts[id] = {
            title: title,
            summary: getSummary(id),
            fills: getNumberOfFills(id),
            filledBy: getFilledBy(id),
            series: getSeriesData(id),
            speakers: getSpeakers(id),
            audienceTags: getAudienceTags(id),
            contentTags: getContentTags(id),
            scriptLinks: getScriptLinks(id)
        };
    }

    return scripts;
}

function getSummary(scriptId) {
    const blockquote = document.getElementById(scriptId).querySelector("blockquote");

    let lines = [];

    for (const p of blockquote.querySelectorAll("p")) {
        lines.push(p.textContent.replace(/\n\s+/g, " ").trim());
    }

    return lines.join("  \n> ");
}


function getAudienceTags(scriptId) {
    const elements = document.getElementById(scriptId).querySelectorAll("li.audience-tag");
    
    let results = [];
    for (const e of elements) {
        results.push(e.textContent);
    }

    return results;
}


function getContentTags(scriptId) {
    const elements = document.getElementById(scriptId).querySelectorAll("li.script-tag:not(.meta-tag):not(.audience-tag)");

    let results = [];
    for (const e of elements) {
        results.push(e.textContent);
    }

    return results;
}

function getFilledBy(scriptId) {
    const container = document.getElementById(scriptId).querySelector("div.script-fills");

    if (container === null) {
        return [];
    }

    let filledBy = [];
    for (const e of container.querySelectorAll("div.fill-details")) {
        const text = e.querySelector("span").textContent;  // "VA1, VA2, VA3"
        const voices = text.split(", "); // ["VA1", "VA2", "VA3"]
        filledBy.push(voices);
    }

    return filledBy; // [["VA1", "VA2"], ["VA3", "VA4"]]
}


function getSpeakers(scriptId) {
    const el = document.getElementById(scriptId).querySelector("li.audience-tag");

    // MTMFNBTF4A -> speaker = "MTMFNBTF4A"
    const speaker = el.textContent.split("4")[0];

    // recognised speaker tags
    // TF, TM, TA = transfem, transmasc, transany
    // F, M, A = fem, masc, any
    // NB = nonbinary
    const matches = speaker.matchAll(/TF|TM|TA|M|F|NB|A/g)

    return Array.from(matches);
}


function getNumberOfFills(scriptId) {
    const el = document.getElementById(scriptId).querySelector("span.fill-count");

    if (el === null) {
        return 0;
    }

    return parseInt(el.textContent);
}

function getSeriesData(scriptId) {
    const root = document.getElementById(scriptId).querySelector("li.series-tag");
    
    if (root === null) {
        return null;
    }

    return {
        title: root.querySelector("span.series-title").textContent,
        index: parseInt(root.querySelector("span.series-index").textContent)
    };

}

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


function matchesTextFilter(scriptData, filterText) {
    if (filterText === "") {
        // all scripts match the empty filter
        return true;
    }

    if (scriptData["title"].toLowerCase().includes(filterText)) {
        return true;
    }

    if (scriptData["summary"].toLowerCase().includes(filterText)) {
        return true;
    }

    if (scriptData["series"] !== null && scriptData["series"]["title"].toLowerCase().includes(filterText)) {
        return true;
    }

    for (const tag of scriptData["contentTags"]) {
        if (tag.toLowerCase().includes(filterText)) {
            return true;
        }
    }

    return false;
}


function matchesSeries(target, actual) {
    if (target === "") {
        // empty string for target means we have no filter
        // i.e., everything passes
        return true;
    }

    if (target === "(one-shots only)") {
        // only those which do not have series data will pass
        return (actual === null)
    }

    // we know that the target is some particular series
    if (actual === null) {
        return false;
    }

    return actual["title"] === target;
}


function isVoicedBy(scriptData, targetVA) {
    for (const voices of scriptData["filledBy"]) {
        if (voices.includes(targetVA)) {
            return true;
        }
    }

    return false;
}


function filterScripts() {
    const filterText = document.getElementById("filterInput").value.trim().toLowerCase();
    const seriesFilter = document.getElementById("seriesFilter").value;
    const audienceTagFilter = document.getElementById("audienceTagFilter").value;
    const filledByFilter = document.getElementById("filledByFilter").value;
    const unfilledOnlyFilter = document.getElementById("unfilledOnlyFilter").value;
    let scripts = identifyScripts();

    let scriptsShown = 0;
    let fillsShown = 0;

    for (const id in scripts) {
        const element = document.getElementById(id);
        const data = scripts[id];

        if (!matchesTextFilter(data, filterText)) {
            element.style.display = "none";
            continue;
        }

        if (unfilledOnlyFilter === "yes" && data["fills"] !== 0) {
            element.style.display = "none";
            continue;
        }

        if (!matchesSeries(seriesFilter, data["series"])) {
            element.style.display = "none";
            continue;
        }

        if (audienceTagFilter !== "" && !data["audienceTags"].includes(audienceTagFilter)) {
            element.style.display = "none";
            continue;
        }

        if (filledByFilter !== "" && !isVoicedBy(data, filledByFilter)) { 
            element.style.display = "none";
            continue;
        }

        element.style.display = "block";
        scriptsShown += 1;
        fillsShown += data["fills"];
    }

    document.getElementById("numScripts").textContent = scriptsShown;
    document.getElementById("numFills").textContent = fillsShown;
}


function chooseScriptPostLink(links) {
    for (const link of links) {
        if (link.includes("reddit\.com")) {
            return link;
        }
    }
}


function scriptToMarkdown(scriptId) {
    const scripts = identifyScripts();
    const script = scripts[scriptId];

    const link = chooseScriptPostLink(script["scriptLinks"]);
    const audience = script["audienceTags"][0];

    const f = function(text) {
        return text.replace(/\n\s+/g, " ").trim();
    };
    const tags = script["contentTags"].map(tag => `\\[${f(tag)}\\]`).join(" ");
    
    console.log(script["summary"]);
    return `**[${script["title"]}](${link})**  \n\\[${audience}\\] ${tags}  \n> _${script["summary"]}_`;
}



function copyToClipboard(scriptId) {
    markdown = scriptToMarkdown(scriptId);
    navigator.clipboard.writeText(markdown);
}
