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
            series: getSeriesData(id),
            speakers: getSpeakers(id),
        };
    }

    return scripts;
}

function getSpeakers(scriptId) {
    const el = document.getElementById(scriptId).querySelector("li.audience-tag");

    // MTMFNBTF4A -> speaker = "MTMFNBTF4A"
    const speaker = el.textContent.split("4")[0];

    // recognised speaker tags
    // TF, TM, TA = transfem, transmasc, transany
    // F, M, A = fem, masc, any
    // NB = nonbinary
    return speaker.matchAll(/TF|TM|TA|M|F|NB|A/).toArray()
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


function filterScripts() {
    const filterText = document.getElementById("filterInput").value.trim().toLowerCase();
    const unfilledOnly = document.getElementById("unfilledScripts").checked;
    const oneShotsOnly = document.getElementById("oneShots").checked;
    const singleSpeakerOnly = document.getElementById("singleSpeaker").checked;
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

        if (unfilledOnly && data["fills"] > 0) {
            element.style.display = "none";
            continue;
        }

        if (oneShotsOnly && data["series"] !== null) {
            element.style.display = "none";
            continue;
        }

        if (singleSpeakerOnly && data["speakers"].length > 1) {
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
