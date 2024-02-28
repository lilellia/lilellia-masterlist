function identifyScripts() {
    let scripts = {};

    for (const element of document.getElementsByClassName("script-data")) {
        const id = element.id;
        const title = element.querySelector("p").textContent.trim();
        const summary = element.querySelector("blockquote").textContent.trim();

        scripts[id] = {
            title: title,
            summary: summary,
            fills: getNumberOfFills(id)
        };
    }

    return scripts;
}

function getNumberOfFills(scriptId) {
    const el = document.getElementById(scriptId).querySelector("span.fill-count");

    if (el === null) {
        return 0;
    }

    return parseInt(el.textContent);
}


function filterScripts() {
    const filterText = document.getElementById("filterInput").value.trim().toLowerCase();
    let scripts = identifyScripts();
    console.log(scripts);

    let scriptsShown = 0;
    let fillsShown = 0;

    for (const id in scripts) {
        const element = document.getElementById(id);
        const data = scripts[id];

        // if filter is empty, show all scripts
        if (filterText === "") {
            element.style.display = "block";
            scriptsShown += 1;
            fillsShown += data["fills"];
            continue;
        }

        // determine if the title or description contains the target filter
        if (data["title"].toLowerCase().includes(filterText) || data["summary"].toLowerCase().includes(filterText)) {
            element.style.display = "block";
            scriptsShown += 1;
            fillsShown += data["fills"];
        } else {
            element.style.display = "none";
        }
    }

    document.getElementById("numScripts").textContent = scriptsShown;
    document.getElementById("numFills").textContent = fillsShown;
}