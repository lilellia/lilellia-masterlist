function identifyScripts() {
    let scripts = {};

    for (const element of document.getElementsByClassName("script-data")) {
        const id = element.id;
        const title = element.querySelector("p").textContent.trim();
        const summary = element.querySelector("blockquote").textContent.trim();
        

        scripts[id] = {
            title: title,
            summary: summary,
            fills: getNumberOfFills(id),
            filledBy: getFilledBy(id),
            series: getSeriesData(id),
            speakers: getSpeakers(id),
            audienceTags: getAudienceTags(id),
        };
    }

    return scripts;
}


function getAudienceTags(scriptId) {
    const elements = document.getElementById(scriptId).querySelectorAll("li.audience-tag");
    
    let results = [];
    for (const e of elements) {
        results.push(e.textContent);
    }

    return results;
}


function getFilledBy(scriptId) {
    const ul = document.getElementById(scriptId).querySelector("ul.script-fills");

    if (ul === null) {
        return [];
    }

    let filledBy = [];
    for (const e of ul.querySelectorAll("li")) {
        filledBy.push(e.querySelector("a").textContent);
    }

    return filledBy;
}


function getSpeakers(scriptId) {
    const el = document.getElementById(scriptId).querySelector("li.audience-tag");

    // MTMFNBTF4A -> speaker = "MTMFNBTF4A"
    const speaker = el.textContent.split("4")[0];

    // recognised speaker tags
    // TF, TM, TA = transfem, transmasc, transany
    // F, M, A = fem, masc, any
    // NB = nonbinary
    return speaker.matchAll(/TF|TM|TA|M|F|NB|A/g).toArray()
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


function filterScripts() {
    const filterText = document.getElementById("filterInput").value.trim().toLowerCase();
    const fillsFilter = document.getElementById("fillsFilter").value;
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

        if (filledByFilter !== "" && !data["filledBy"].includes(filledByFilter)) {
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
