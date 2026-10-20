// The hits screen. Like the client's armor page, the page tells the lobby it supports the full screen mode: the
// Flash lobby page then gives the window the whole screen and draws its header and footer over it in the new style
// (not as opaque bars). The space the header and the footer take is given as external paddings, put into the CSS
// variables --external-padding-top/right/bottom/left.
function applyExternalPaddings() {
    const paddings = viewEnv.getExternalPaddingsRem();
    const style = document.documentElement.style;
    style.setProperty("--external-padding-top", `${paddings.top}rem`);
    style.setProperty("--external-padding-right", `${paddings.right}rem`);
    style.setProperty("--external-padding-bottom", `${paddings.bottom}rem`);
    style.setProperty("--external-padding-left", `${paddings.left}rem`);
}

function init() {
    applyExternalPaddings();
    engine.on("self.onPaddingsUpdated", applyExternalPaddings);
    viewEnv.setFullscreenModeSupported(true);
}

if (engine.whenReady) {
    engine.whenReady.then(init);
} else {
    init();
}

// Mouse over the 3D scene, like the client's SceneWrapper: a drag with the left button turns the camera by the
// mouse deltas in pixels, the wheel zooms by a fixed step.
const WHEEL_STEP = 600;
const sceneInput = document.querySelector(".sceneInput");
let dragging = false;
let lastX = 0;
let lastY = 0;

function moveSpace(dx, dy, dz) {
    if (window.model) {
        window.model.onMoveSpace({ dx, dy, dz });
    }
}

function setOverScene(isOver3dScene) {
    if (window.model) {
        window.model.onMouseOver3dScene({ isOver3dScene });
    }
}

sceneInput.addEventListener("mousedown", (event) => {
    event.preventDefault();
    if (event.buttons === 1) {
        dragging = true;
        lastX = event.clientX;
        lastY = event.clientY;
    }
});
sceneInput.addEventListener("mousemove", (event) => {
    event.preventDefault();
    if (!dragging) {
        return;
    }
    const dx = event.clientX - lastX;
    const dy = event.clientY - lastY;
    lastX = event.clientX;
    lastY = event.clientY;
    if (dx || dy) {
        moveSpace(dx, dy, 0);
    }
});
window.addEventListener("mouseup", () => {
    dragging = false;
});
sceneInput.addEventListener("wheel", (event) => {
    event.preventDefault();
    moveSpace(0, 0, event.deltaY < 0 ? -WHEEL_STEP : WHEEL_STEP);
});
// Scrolled lists: Gameface's own wheel scrolling of an overflow moves a few pixels a step, so the page scrolls them
// itself, a part of the visible height a step. Gameface gives a negative deltaY for the wheel turned towards the user
// (down).
const LIST_STEP = 0.3;
Array.prototype.forEach.call(document.querySelectorAll(".battleSelector__list, .hitsPanel__list"), (list) => {
    list.addEventListener("wheel", (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (event.deltaY) {
            const step = Math.max(40, list.clientHeight * LIST_STEP);
            list.scrollTop += event.deltaY < 0 ? step : -step;
        }
    });
});

sceneInput.addEventListener("mouseover", () => setOverScene(true));
sceneInput.addEventListener("mouseout", () => {
    setOverScene(false);
    dragging = false;
});

// Battle selector: the card shows the selected battle, a click opens the list of the session's battles, a click on
// a battle selects it (onSelect in the model), a click elsewhere or Escape closes the list. The data is in
// window.model.battleSelector and the page draws it again on every model change.
const selector = document.querySelector(".battleSelector");
const selectorCard = selector.querySelector(".battleSelector__card");
const selectorItems = selector.querySelector(".battleSelector__items");

// Array items of a view model may come wrapped as {value: item}.
function arrayItems(array) {
    const items = [];
    for (let index = 0; array && index < array.length; index++) {
        const item = array[index];
        items.push(item && item.value !== undefined ? item.value : item);
    }
    return items;
}

function element(tag, className, text) {
    const node = document.createElement(tag);
    node.className = className;
    if (text !== undefined) {
        node.textContent = text;
    }
    return node;
}

function setImage(node, path) {
    node.style.backgroundImage = path ? `url(${path})` : "none";
}

function setSelectorOpen(open) {
    selector.classList.toggle("battleSelector__open", open && !selector.classList.contains("battleSelector__empty"));
}

const RESULT_CLASSES = {
    win: "battleSelector__resultWin",
    defeat: "battleSelector__resultDefeat",
    draw: "battleSelector__resultDraw",
};

// The result after the map name; empty when it is not known.
function setResult(node, battle) {
    node.className = `battleSelector__result ${RESULT_CLASSES[battle.result] || ""}`;
    node.textContent = battle.resultText || "";
}

function titleRow(battle) {
    const row = element("div", "battleSelector__titleRow");
    row.appendChild(element("div", "battleSelector__itemMap", battle.mapName));
    const result = element("div", "");
    setResult(result, battle);
    row.appendChild(result);
    return row;
}

function drawBattleSelector() {
    const model = window.model && window.model.battleSelector;
    if (!model) {
        return;
    }
    const battles = arrayItems(model.battles);
    const selected = battles.find((battle) => battle.id === model.selectedId) || battles[0];
    selector.classList.toggle("battleSelector__empty", !selected);
    if (!selected) {
        // No battles yet: the card shows the empty title only.
        setSelectorOpen(false);
        selector.querySelector(".battleSelector__mapName").textContent = model.emptyTitle;
        selectorItems.textContent = "";
        return;
    }
    setImage(selector.querySelector(".battleSelector__mapImage"), selected.mapImage);
    selector.querySelector(".battleSelector__mapName").textContent = selected.mapName;
    setResult(selector.querySelector(".battleSelector__result"), selected);
    selector.querySelector(".battleSelector__vehicle").textContent = selected.vehicleName;
    selector.querySelector(".battleSelector__time").textContent = selected.time;

    // The battles come newest first: a day row starts each day.
    selectorItems.textContent = "";
    let day = null;
    battles.forEach((battle) => {
        if (battle.day !== day) {
            day = battle.day;
            selectorItems.appendChild(element("div", "battleSelector__day", day));
        }
        const item = element("div", "battleSelector__item");
        item.classList.toggle("battleSelector__itemSelected", battle === selected);
        item.appendChild(element("div", "battleSelector__itemBg"));
        const image = element("div", "battleSelector__itemImage");
        setImage(image, battle.mapImage);
        item.appendChild(image);
        const info = element("div", "battleSelector__itemInfo");
        info.appendChild(titleRow(battle));
        info.appendChild(element("div", "battleSelector__line battleSelector__vehicle", battle.vehicleName));
        item.appendChild(info);
        item.appendChild(element("div", "battleSelector__itemTime", battle.time));
        // Handlers keep plain values: the model's items are destroyed when the model is filled again.
        const id = battle.id;
        item.addEventListener("click", (event) => {
            event.stopPropagation();
            setSelectorOpen(false);
            window.model.battleSelector.onSelect({ id });
        });
        selectorItems.appendChild(item);
    });
}

selectorCard.addEventListener("click", (event) => {
    event.stopPropagation();
    setSelectorOpen(!selector.classList.contains("battleSelector__open"));
});
selector.querySelector(".battleSelector__list").addEventListener("click", (event) => event.stopPropagation());
document.addEventListener("click", () => setSelectorOpen(false));
document.addEventListener("keydown", (event) => {
    if (event.keyCode === 27) {
        setSelectorOpen(false);
    }
});

// Hits panel: tabs (received or dealt hits), result filters, the chosen hit and the list
// (window.model.hitsPanel). Every click goes to the presenter, which fills the model again.
const hitsPanel = document.querySelector(".hitsPanel");
const hitsFilters = hitsPanel.querySelector(".hitsPanel__filters");
const hitsList = hitsPanel.querySelector(".hitsPanel__list");

function hitIcon(kind, side) {
    return element("div", `hitIcon hitIcon__${kind}__${side}`);
}


function chip(selected, onClick) {
    const node = element("div", "hitsPanel__chip");
    node.classList.toggle("hitsPanel__chipSelected", selected);
    node.addEventListener("click", onClick);
    return node;
}

function drawHitsPanel() {
    const model = window.model && window.model.hitsPanel;
    hitsPanel.classList.toggle("hitsPanel__visible", Boolean(model && model.isVisible));
    if (!model || !model.isVisible) {
        return;
    }
    const side = model.side;
    hitsPanel.querySelectorAll(".hitsPanel__tab").forEach((tab) => {
        const tabSide = tab.getAttribute("data-side");
        tab.textContent = tabSide === "received" ? model.receivedLabel : model.dealtLabel;
        tab.classList.toggle("hitsPanel__tabSelected", tabSide === side);
    });

    hitsFilters.textContent = "";
    arrayItems(model.filters).forEach((filter) => {
        const id = filter.id;
        const node = chip(id === model.selectedFilter, () => window.model.hitsPanel.onFilter({ id }));
        if (id) {
            node.appendChild(hitIcon(id, side));
        } else {
            node.appendChild(document.createTextNode(model.allLabel));
        }
        node.appendChild(element("span", "hitsPanel__count", String(filter.count)));
        hitsFilters.appendChild(node);
    });

    const hits = arrayItems(model.hits);
    hitsPanel.querySelector(".hitsPanel__position").textContent = hits.length
        ? `${model.selectedHit + 1} / ${hits.length}`
        : "0 / 0";
    hitsList.textContent = "";
    hits.forEach((hit, index) => {
        const row = element("div", "hitsPanel__row");
        row.classList.toggle("hitsPanel__rowSelected", index === model.selectedHit);
        row.appendChild(element("div", "hitsPanel__number", String(hit.number)));
        row.appendChild(element("div", "hitsPanel__time", hit.time));
        // Then the order of the client's damage log: damage (none when the hit took none), result, shell, class,
        // vehicle; the player last.
        // Like the client's log: the damage, or "xN" crits for a hit on modules without damage.
        let damage = hit.damage ? String(hit.damage) : "";
        if (!hit.damage && hit.result === "critical" && hit.critsCount) {
            damage = `x${hit.critsCount}`;
        }
        row.appendChild(element("div", "hitsPanel__damage", damage));
        row.appendChild(hitIcon(hit.result, side));
        const shell = element("div", "hitsPanel__shell", hit.shellText);
        shell.classList.toggle("hitsPanel__shellNone", !hit.shellText);
        shell.classList.toggle("hitsPanel__shellGold", Boolean(hit.isGoldShell));
        shell.title = hit.shellName;
        row.appendChild(shell);
        row.appendChild(element("div", hit.vehicleClass ? `hitIcon hitIcon__class__${hit.vehicleClass}` : "hitIcon"));
        row.appendChild(element("div", "hitsPanel__vehicle", hit.vehicleName));
        row.appendChild(element("div", "hitsPanel__player", hit.playerName));
        row.addEventListener("click", () => window.model.hitsPanel.onHit({ index }));
        hitsList.appendChild(row);
    });
}

hitsPanel.querySelectorAll(".hitsPanel__tab").forEach((tab) => {
    tab.addEventListener("click", () => window.model.hitsPanel.onSide({ side: tab.getAttribute("data-side") }));
});
hitsPanel.querySelector(".hitsPanel__prev").addEventListener("click", () => window.model.hitsPanel.onStep({ delta: -1 }));
hitsPanel.querySelector(".hitsPanel__next").addEventListener("click", () => window.model.hitsPanel.onStep({ delta: 1 }));

// File buttons: save the chosen battle to its file, load the battle files (window.model.fileButtons); the save is off
// without a battle.
const fileButtons = document.querySelector(".fileButtons");

function drawFileButtons() {
    const model = window.model && window.model.fileButtons;
    fileButtons.classList.toggle("fileButtons__visible", Boolean(model));
    fileSave.classList.toggle("fileButtons__disabled", !(model && model.canSave));
    fileButtons.querySelector(".fileButtons__saveLabel").textContent = model ? model.saveLabel : "";
    fileButtons.querySelector(".fileButtons__importLabel").textContent = model ? model.importLabel : "";
}

const fileSave = fileButtons.querySelector(".fileButtons__save");
fileSave.addEventListener("click", () => window.model.fileButtons.onSave());
fileButtons.querySelector(".fileButtons__import").addEventListener("click", () => window.model.fileButtons.onImport());

// Overlay panel: the overlay type dropdown (window.model.overlayPanel). A click on
// the dropdown opens its list, a click on a type chooses it (onSelect), a click elsewhere or Escape closes the list.
const overlayPanel = document.querySelector(".overlayPanel");
const overlayDropdown = overlayPanel.querySelector(".overlayPanel__dropdown");
const overlayList = overlayPanel.querySelector(".overlayPanel__list");

function setOverlayOpen(open) {
    overlayDropdown.classList.toggle("overlayPanel__open", open);
}

function drawOverlayPanel() {
    const model = window.model && window.model.overlayPanel;
    if (!model) {
        return;
    }
    overlayPanel.querySelector(".overlayPanel__title").textContent = model.title;
    const selectedId = model.selectedId;
    const items = arrayItems(model.items);
    const selected = items.filter((item) => item.id === selectedId)[0];
    overlayPanel.querySelector(".overlayPanel__selected").textContent = selected ? selected.label : "";
    overlayList.innerHTML = "";
    items.forEach((item) => {
        const row = element("div", `overlayPanel__item${item.id === selectedId ? " overlayPanel__itemSelected" : ""}`);
        row.appendChild(element("div", "overlayPanel__itemBg"));
        row.appendChild(element("div", "overlayPanel__itemLabel", item.label));
        // Handlers keep plain values: the model's items are destroyed when the model is filled again.
        const id = item.id;
        row.addEventListener("click", (event) => {
            event.stopPropagation();
            setOverlayOpen(false);
            window.model.overlayPanel.onSelect({ id });
        });
        overlayList.appendChild(row);
    });
}

overlayPanel.querySelector(".overlayPanel__trigger").addEventListener("click", (event) => {
    event.stopPropagation();
    setOverlayOpen(!overlayDropdown.classList.contains("overlayPanel__open"));
});
document.addEventListener("click", () => setOverlayOpen(false));
document.addEventListener("keydown", (event) => {
    if (event.keyCode === 27) {
        setOverlayOpen(false);
    }
});

// Scene panel: lines of all the shown hits or of the chosen one (onLines), the shooter view (onShooterView), from
// window.model.scenePanel.
const scenePanel = document.querySelector(".scenePanel");
const sceneSegments = scenePanel.querySelectorAll(".scenePanel__segment");
const sceneShooter = scenePanel.querySelector(".scenePanel__shooter");

function drawScenePanel() {
    const model = window.model && window.model.scenePanel;
    if (!model) {
        return;
    }
    for (let index = 0; index < sceneSegments.length; index++) {
        const segment = sceneSegments[index];
        const all = segment.getAttribute("data-all") === "1";
        segment.textContent = all ? model.allLabel : model.currentLabel;
        segment.classList.toggle("scenePanel__segmentSelected", all === Boolean(model.allLines));
    }
    sceneShooter.querySelector(".scenePanel__shooterLabel").textContent = model.shooterLabel;
    // On the dealt side only the chosen hit's line is drawn: no choice of lines to show.
    scenePanel.classList.toggle("scenePanel__oneLine", !model.allLinesEnabled);
    sceneShooter.classList.toggle("scenePanel__shooterOn", Boolean(model.shooterView));
}

for (let index = 0; index < sceneSegments.length; index++) {
    const all = sceneSegments[index].getAttribute("data-all") === "1";
    sceneSegments[index].addEventListener("click", () => window.model.scenePanel.onLines({ all }));
}
sceneShooter.addEventListener("click", () => window.model.scenePanel.onShooterView());

// Shot panel: the chosen hit's shooter and target cards, its result, its sections (window.model.shotPanel). A value
// counted in the garage is underlined with dashes.
const shotPanel = document.querySelector(".shotPanel");
const shotVehicles = shotPanel.querySelector(".shotPanel__vehicles");
const shotSections = shotPanel.querySelector(".shotPanel__sections");

function shotVehicle(vehicle) {
    const node = element("div", "shotPanel__vehicle");
    const who = element("div", "shotPanel__who");
    who.appendChild(element("div", "shotPanel__role", vehicle.role));
    who.appendChild(element("div", "shotPanel__player", vehicle.player));
    node.appendChild(who);
    const body = element("div", "shotPanel__body");
    const card = element("div", "shotPanel__card");
    const flag = element("div", "shotPanel__flag");
    setImage(flag, vehicle.flag);
    card.appendChild(flag);
    const icon = element("div", "shotPanel__vehicleIcon");
    setImage(icon, vehicle.icon);
    card.appendChild(icon);
    const caption = element("div", "shotPanel__caption");
    caption.appendChild(element("div", "", vehicle.tier));
    caption.appendChild(element("div", "shotPanel__vehicleName", vehicle.vehicleName));
    card.appendChild(caption);
    body.appendChild(card);
    const modules = element("div", "shotPanel__modules");
    arrayItems(vehicle.modules).forEach((module) => {
        const row = element("div", "shotPanel__module");
        const moduleIcon = element("div", "shotPanel__moduleIcon");
        setImage(moduleIcon, module.icon);
        if (module.tier) {
            moduleIcon.appendChild(element("div", "shotPanel__moduleTier", module.tier));
        }
        row.appendChild(moduleIcon);
        row.appendChild(element("div", "shotPanel__moduleLabel", module.label));
        modules.appendChild(row);
    });
    body.appendChild(modules);
    node.appendChild(body);
    return node;
}

function drawShotPanel() {
    const model = window.model && window.model.shotPanel;
    shotPanel.classList.toggle("shotPanel__visible", Boolean(model && model.isVisible));
    if (!model || !model.isVisible) {
        return;
    }
    shotVehicles.innerHTML = "";
    shotVehicles.appendChild(shotVehicle(model.shooter));
    shotVehicles.appendChild(shotVehicle(model.target));
    shotPanel.querySelector(".shotPanel__resultIcon").className = `shotPanel__resultIcon hitIcon hitIcon__${model.resultIcon}`;
    shotPanel.querySelector(".shotPanel__number").textContent = model.number;
    shotSections.innerHTML = "";
    arrayItems(model.sections).forEach((section) => {
        const head = element("div", `shotPanel__head shotPanel__head__${section.kind}`);
        const value = element("div", "shotPanel__value");
        value.appendChild(element("span", section.counted ? "shotPanel__counted" : "", section.value));
        head.appendChild(value);
        const title = element("div", "shotPanel__title", section.title);
        if (section.units) {
            title.appendChild(element("span", "shotPanel__units", section.units));
        }
        head.appendChild(title);
        shotSections.appendChild(head);
        arrayItems(section.rows).forEach((item) => {
            const row = element("div", "shotPanel__row");
            const rowValue = element("div", "shotPanel__rowValue");
            rowValue.appendChild(element("span", item.counted ? "shotPanel__counted" : "", item.value));
            row.appendChild(rowValue);
            row.appendChild(element("div", "shotPanel__rowLabel", item.label));
            shotSections.appendChild(row);
        });
    });
}

function draw() {
    drawBattleSelector();
    drawHitsPanel();
    drawFileButtons();
    drawOverlayPanel();
    drawScenePanel();
    drawShotPanel();
}

// The page draws again on a change of the model or of any of its parts: a change inside a part (its arrays, its
// selection) is told to the observers of that part's path.
engine.whenReady.then(() => {
    const paths = ["model", "model.battleSelector", "model.hitsPanel", "model.fileButtons", "model.overlayPanel",
        "model.scenePanel", "model.shotPanel",
        "model.shotPanel.shooter", "model.shotPanel.target"];
    const callbackIDs = paths.map((path) =>
        viewEnv.addDataChangedCallback(path, 0, true),
    );
    engine.on("viewEnv.onDataChanged", (data, indexes, changedIDs) => {
        if (callbackIDs.some((id) => changedIDs.indexOf(id) !== -1)) {
            draw();
        }
    });
    draw();
});
