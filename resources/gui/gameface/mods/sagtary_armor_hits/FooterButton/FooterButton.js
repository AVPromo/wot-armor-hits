// Armor Hits button in the hangar footer, before the game menu button.
// Injected into the footer page by OpenWG Gameface; the model is the footer button view model in Python.
import { MediaContext } from "../../libs/media.js";
import { ModelObserver } from "../../libs/model.js";
import { playSound } from "../../libs/sound.js";
import { showTooltip, hideTooltip } from "../../libs/views.js";

const BUTTON_CLASS = "armorHitsButton";

const media = MediaContext(false);
const model = ModelObserver("SagtaryArmorHitsFooterButton");

// Same right margin as the other footer buttons; with a fractional interface scale (between 1x and 2x)
// the footer adds space, so does the button.
const updateMargin = (button) => {
    if (media.scale > 1 && media.scale < 2) {
        const offset = media.width * media.scale < 1366 ? 30 : 15;
        button.style.marginRight = `${6 + offset / media.scale}rem`;
    } else {
        button.style.marginRight = "6rem";
    }
};

const createButton = () => {
    const button = document.createElement("div");
    button.className = BUTTON_CLASS;
    button.addEventListener("click", () => {
        playSound("play");
        hideTooltip();
        model.model.onClick();
    });
    button.addEventListener("mouseenter", () => {
        playSound("highlight");
        showTooltip(model.model.title, model.model.description);
    });
    button.addEventListener("mouseleave", () => hideTooltip());
    updateMargin(button);
    return button;
};

engine.whenReady.then(() => {
    media.onUpdate(() => {
        const button = document.querySelector(`.${BUTTON_CLASS}`);
        if (button) updateMargin(button);
    });
    media.subscribe();
    model.subscribe();

    // The footer is a React page and can rebuild its DOM; put the button back whenever it is gone.
    const observer = new MutationObserver(() => {
        const menuButton = document.querySelector('div[data-test-id="menu"]');
        const section = menuButton?.parentNode;
        if (section && !section.querySelector(`.${BUTTON_CLASS}`)) {
            section.insertBefore(createButton(), menuButton);
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
});
