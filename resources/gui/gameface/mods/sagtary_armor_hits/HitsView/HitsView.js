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

function modeLine(node, battle) {
    node.textContent = "";
    node.appendChild(document.createTextNode(battle.mode ? `${battle.mode} · ` : ""));
    node.appendChild(element("span", "battleSelector__vehicle", battle.vehicleName));
}

function drawBattleSelector() {
    const model = window.model && window.model.battleSelector;
    if (!model) {
        return;
    }
    const battles = arrayItems(model.battles);
    const selected = battles.find((battle) => battle.id === model.selectedId) || battles[0];
    selector.classList.toggle("battleSelector__empty", !selected);
    selector.querySelector(".battleSelector__listTitle").textContent = model.listTitle;
    if (!selected) {
        setSelectorOpen(false);
        setImage(selector.querySelector(".battleSelector__mapImage"), "");
        selector.querySelector(".battleSelector__mapName").textContent = model.emptyTitle;
        selector.querySelector(".battleSelector__modeLine").textContent = "";
        selector.querySelector(".battleSelector__timeLine").textContent = "";
        selectorItems.textContent = "";
        return;
    }
    setImage(selector.querySelector(".battleSelector__mapImage"), selected.mapImage);
    selector.querySelector(".battleSelector__mapName").textContent = selected.mapName;
    modeLine(selector.querySelector(".battleSelector__modeLine"), selected);
    selector.querySelector(".battleSelector__timeLine").textContent = `${selected.date} · ${selected.time}`;

    selectorItems.textContent = "";
    battles.forEach((battle) => {
        const item = element("div", "battleSelector__item");
        item.classList.toggle("battleSelector__itemSelected", battle === selected);
        item.appendChild(element("div", "battleSelector__itemBg"));
        const image = element("div", "battleSelector__itemImage");
        setImage(image, battle.mapImage);
        item.appendChild(image);
        const info = element("div", "battleSelector__itemInfo");
        info.appendChild(element("div", "battleSelector__itemMap", battle.mapName));
        const mode = element("div", "");
        modeLine(mode, battle);
        info.appendChild(mode);
        item.appendChild(info);
        const time = element("div", "battleSelector__itemTime");
        time.appendChild(element("div", "", battle.date));
        time.appendChild(element("div", "", battle.time));
        item.appendChild(time);
        item.addEventListener("click", (event) => {
            event.stopPropagation();
            setSelectorOpen(false);
            if (battle.id !== model.selectedId) {
                model.onSelect({ id: battle.id });
            }
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

engine.whenReady.then(() => {
    const callbackID = viewEnv.addDataChangedCallback("model", 0, true);
    engine.on("viewEnv.onDataChanged", (data, indexes, callbackIDs) => {
        if (callbackIDs.includes(callbackID)) {
            drawBattleSelector();
        }
    });
    drawBattleSelector();
});
