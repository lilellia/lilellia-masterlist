const scriptData = await fetch("./script-data.json").then(res => res.json());

/**
 * Wrap the value in the given HTML tag.
 * tagged("value", "b") => <b>value</b>
 * 
 * @param {String} value 
 * @param {String} tag 
 */
function tagged(value, tag) {
    return `<${tag}>${value}</${tag}>`
}

/**
 * 
 * @param {String} audience - the audience tag
 */
function summariseGender(audience) {
    if (audience.match(/^M+4/)) {
        return "male";
    }
    
    if (audience.match(/^F+4/)) {
        return "female";
    }

    return "neutral";
}


/**
 * Serialise the string, converting spaces to hyphens and removing quote marks
 * @param {String} value 
 */
function serialise(value) {
    return value.toLowerCase().replace(" ", "-").replace(/['"]/g, "");
}



/**
 * Return a new element with the given tag and the given class.
 * @param {String} tag 
 * @param {String} cls 
 * @returns 
 */
function createElementWithClass(tag, cls) {
    const element = document.createElement(tag);
    element.setAttribute("class", cls);

    return element;
}


function makeWordCountTag(wordCountData) {
    // wordCountData has the form {spoken => {name => words}, total => words}
    const tag = createElementWithClass("li", "script-tag meta-tag");

    const roleWordCounts = Object.values(wordCountData.spoken);

    if (roleWordCounts.length == 1) {
        const totalWords = Object.values(wordCountData.spoken)[0];
        tag.innerHTML = totalWords.toLocaleString();
    } else {
        const individual = roleWordCounts
                            .map(val => val.toLocaleString())
                            .join("+");
        const allSpoken = roleWordCounts.reduce((prev, current) => prev + current);
        tag.innerHTML = `${individual} (=${allSpoken})`;
    }

    return tag;
}


function htmlifyScriptTags(script) {
    const ul = createElementWithClass("ul", "script-tags");
    
    // date tag
    const dateTag = createElementWithClass("li", "script-tag meta-tag");
    dateTag.innerHTML = script.published;
    ul.appendChild(dateTag);

    // audience tag
    for (audience of script.audience) {
        const audienceTag = createElementWithClass("li", `script-tag audience-tag ${audience.toLowerCase()}`);
        audienceTag.innerHTML = audience.toUpperCase();
        ul.appendChild(audienceTag);
    }

    // content tags
    for (tag of script.tags) {
        const contentTag = createElementWithClass("li", "script-tag");
        if (["18+", "nsfw", "r18"].includes(tag.toLowerCase())) {
            contentTag.className += " nsfw-tag"
        }
        contentTag.innerHTML = tag;
        ul.appendChild(contentTag);
    }

    // word count
    const wordCountTag = makeWordCountTag(script.words);
    ul.appendChild(wordCountTag);

    return ul;
}


function extractFillLink(fill) {
    const sources = ["YouTube", "soundgasm", "Patreon"];

    for (const src of sources) {
        const link = fill.links[src];
        if (link !== undefined) {
            return {"source": src, "link": link};
        }
    }
}


function htmlifyFill(fill, attendantVA) {
    const cls = `fill-${summariseGender(fill.audience)}`;
    const li = createElementWithClass("li", cls);

    li.innerHTML = `${icon}<a href="${href}">${creators}</a>${label}${attendantMark}${selfFillMark}`;
    return li;
}


function htmlifyFills(fills, attendantVA) {
    const div = createElementWithClass("div", "fill-summary");

    // "Fills (3):"
    const summary = document.createElement("b");
    summary.innerHTML = `Fills (<span class="fill-count">${fills.length}</span>):`;
    div.appendChild(summary);

    // and then the actual set of fills
    const ul = createElementWithClass("ul", "script-fills");

    for (const li of fills.map(f => htmlifyFill(f, attendantVA))) {
        ul.appendChild(li);
    }

    div.appendChild(ul);
}


function htmlifyScript(script) {
    // create the div element that will be returned
    const div = createElementWithClass("div", "container script-data");
    div.setAttribute("id", serialise(script.title));

    // add the title component
    const p = createElementWithClass("p", "script-title");
    p.innerHTML = script.title;
    div.appendChild(p);

    // add all of the "tags"
    const ul = htmlifyScriptTags(script);
    div.appendChild(ul);

    // series data
    if (script.series !== undefined) {
        const ul = createElementWithClass("ul", "script-tags");
        const li = createElementWithClass("li", `script-tag series-tag ${serialise(script.title)}`);
        li.innerHTML = `Series: <span class="series-title">${script.series.title}</span> (Part <span class="series-index">${script.series.index}</span>)`

        ul.appendChild(li);
        div.appendChild(ul);
    }

    // summary
    const summary = createElementWithClass("blockquote", "script-summary");
    for (const line of script.summary.split("\n")) {
        const p = document.createElement("p");
        p.innerHTML = line;
        summary.appendChild(p);
    }
    div.appendChild(summary);

    // links
    const links = createElementWithClass("ul", "script-links");
    for (const label in script.links.script) {
        const li = createElementWithClass("li", "script-link");
        const href = script.links.script[label];

        li.innerHTML = `<a href="${href}">${label}</a>`;
        links.appendChild(li);
    }

    for (const label in script.links.post) {
        const li = createElementWithClass("li", "post-link");
        const href = script.links.post[label];

        li.innerHTML = `<a href="${href}">${label}</a>`;
        links.appendChild(li);
    }

    // fills
    if (script.fills !== undefined && script.fills.length >= 1) {
        const fills = htmlifyFills(script.fills, script["attendant VA"]);
        div.appendChild(fills);
    }

    return div;
}