/* Variables */
const PLACEHOLDER_TEXT = "Type something...";
const PLACEHOLDER_TEXT_OPACITY = 0.25;
const PLACEHOLDER_TEXT_WIDTH = 220;
const MIN_SCALE_LIMIT = 0.6;
const ALLOWED_CHARACTERS = `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!"#$%&'()*,-./:;<=>?@[]_{|}`;

/* Loading Template */
function load_background_image(template_src) {
    return new Promise((resolve) => {
        fabric.Image.fromURL(template_src, (img) => {
            fabric_canvas.setBackgroundImage(img, () => {
                fabric_canvas.renderAll.bind(fabric_canvas);
                resolve();
            }, {
                scaleX: fabric_canvas.width / img.width,
                scaleY: fabric_canvas.height / img.height
            });
        });
    })
}

async function initialise_template() {
    fabric_canvas.clear();

    const template = document.getElementById('typed_template').value;

    if (template === "Blank" || Object.keys(templates).includes(template)) {
        let textBoxOptions;
        if (template === "Blank") {
            textBoxOptions = [
                {"left": 18, "top": 20, "fontSize": 30},
                {"left": 18, "top": 120, "fontSize": 30},
                {"left": 18, "top": 220, "fontSize": 30},
            ];
        } else {
            const filename = (templates[template].filenameRedeem) ? templates[template].filenameRedeem : templates[template].filename;
            const filePath = `${static_path}templates/${filename}`;
            await load_background_image(filePath);
            textBoxOptions = templates[template].textPosition;
        }

        const textBoxes = [];
        for (let textBoxOption of textBoxOptions) {
            textBoxOption["minScaleLimit"] = MIN_SCALE_LIMIT;
            textBoxOption["opacity"] = PLACEHOLDER_TEXT_OPACITY;
            textBoxOption["width"] = PLACEHOLDER_TEXT_WIDTH;
            textBoxes.push(new fabric.Textbox(PLACEHOLDER_TEXT, textBoxOption));
        }

        fabric_canvas.add(...textBoxes);
    } else {
        console.error(`Template ${template} not found.`);
    }
    await load_font();
}

document.getElementById('typed_template').addEventListener('change', async (event) => {
    await initialise_template();
});

const templateFilenameMap = {};
for (let template of Object.keys(templates)) {
    templateFilenameMap[templates[template].filename] = template;
    if (templates[template].filenameRedeem) {
        templateFilenameMap[templates[template].filenameRedeem] = template;
    }
}


/* Undo, Reset & Clear */
let fabric_canvas_data;
let undo_history = [];

function save_fabric() {    // saves the canvas state into undo history
    if (fabric_canvas_data) {
        undo_history.push(fabric_canvas_data);
    }
    fabric_canvas_data = JSON.stringify(fabric_canvas);
}

// reset button
document.getElementById("fabric_reset").addEventListener("click", async () => {
    clearFabricErrors();
    await initialise_template();
});

// clear button
document.getElementById("fabric_clear").addEventListener("click", () => {
    clearFabricErrors();
    fabric_canvas.remove(...fabric_canvas.getObjects());  // delete all objects but not background
    save_fabric();
});

// undo button
document.getElementById("fabric_undo").addEventListener("click", (event) => {
    clearFabricErrors();
    if (undo_history.length > 0) {
        fabric_canvas_data = undo_history.pop();
        event.target.disabled = true;
        fabric_canvas.clear();
        fabric_canvas.loadFromJSON(fabric_canvas_data, () => {
            fabric_canvas.renderAll();

            // update font selector to match canvas
            document.getElementById('font_selector').value = fabric_canvas.item(0).fontFamily;

            // update template selector to match canvas
            let template_name;
            if (fabric_canvas.backgroundImage) {
                let template_src = fabric_canvas.backgroundImage.src;
                template_src = template_src.substring(template_src.lastIndexOf("/") + 1);

                if (Object.keys(templateFilenameMap).includes(template_src)) {
                    template_name = templateFilenameMap[template_src];
                } else {
                    template_name = document.getElementById('typed_template').value;    // does nothing
                    console.error(`Tried to restore unknown template loaded from ${template_src}.`);
                }
            } else {
                template_name = "Blank";
            }
            document.getElementById('typed_template').value = template_name;

            event.target.disabled = false;
        });
    }
});

/* Init */
const fabric_canvas = new fabric.Canvas('fabric');

fabric_canvas.on('object:modified', function() {
    save_fabric();
});

/* Load Fonts */
async function load_font() {
    const font = document.getElementById("font_selector").value;
    let myFont = new FontFaceObserver(font);
    await myFont.load();
    fabric_canvas.getObjects().forEach((object) => {object.set("fontFamily", font);})
    fabric_canvas.requestRenderAll();
    save_fabric();
}

const font_selector = document.getElementById("font_selector");
const fontStyles = document.createElement('style');
for (let font of Object.keys(fonts)) {
    const option = document.createElement('option');
    option.innerHTML = font;
    option.value = font;
    font_selector.appendChild(option);

    fontStyles.appendChild(document.createTextNode(`\
        @font-face {\
            font-family: '${font}';\
            src: url('${static_path}fonts/${fonts[font]}.woff2') format('woff2'),\
                 url('${static_path}fonts/${fonts[font].replace(" ", "\ ")}.ttf');\
        }\
    `));
}
document.head.appendChild(fontStyles);

font_selector.onchange = async function() {
    await load_font();
}

initialise_template();

/* Delete text box button */
const deleteImg = document.createElement('img');
deleteImg.src = `${static_path}icons/cancel.svg`;
function renderIcon(icon) {
    return function renderIcon(ctx, left, top, styleOverride, fabricObject) {
      let size = this.cornerSize;
      ctx.save();
      ctx.translate(left, top);
      ctx.rotate(fabric.util.degreesToRadians(fabricObject.angle));
      ctx.drawImage(icon, -size/2, -size/2, size, size);
      ctx.restore();
    }
}

function deleteObject(eventData, transform) {
    let target = transform.target;
    let canvas = target.canvas;
    canvas.remove(target);
    canvas.requestRenderAll();
    clearFabricErrors();
    save_fabric();
}

fabric.Textbox.prototype.controls.deleteControl = new fabric.Control({
    x: 0.5,
    y: -0.5,
    offsetY: -16,
    offsetX: 16,
    cursorStyle: 'pointer',
    mouseUpHandler: deleteObject,
    render: renderIcon(deleteImg),
    cornerSize: 20
});

/* Add text box button */
document.getElementById('fabric_add').addEventListener('click', () => {
    const objects = fabric_canvas.getObjects();
    if (objects.length >= 10) {
        document.getElementById('tooManyTextBoxesError').hidden = false;
        return;
    }

    // default coordinates to place new text boxes
    const left_default = 340;
    const top_default = 20;
    let left = left_default;
    let top = top_default;

    // determine a place which is free
    let spaceAvailable = false;
    while (!spaceAvailable) {
        spaceAvailable = true;
        for (let object of objects) {
            if (object.left === left && object.top === top) {
                spaceAvailable = false;
                top += 40;
                if (top > 300) {
                    // if not enough vertical space, move left and restart
                    left -= 40;
                    top = top_default;
                    if (left <= 20) {
                        // if entire board is full, restart entirely
                        left = left_default;
                    }
                }
                break;
            }
        }
    }

    fabric_canvas.add(new fabric.Textbox(PLACEHOLDER_TEXT, {"left": left, "top": top, "fontSize": 30, "minScaleLimit": MIN_SCALE_LIMIT, "opacity": PLACEHOLDER_TEXT_OPACITY, "width": PLACEHOLDER_TEXT_WIDTH, "fontFamily": document.getElementById("font_selector").value}));
    save_fabric();
});

function clearFabricErrors() {
    document.getElementById('tooManyTextBoxesError').hidden = true;
    document.getElementById('weirdCharactersError').hidden = true;
    document.getElementById('typedError').hidden = true;
}

/* Implement Placeholder Text */
function onPlaceholderTextDeselect(event) {
    if (Object.keys(event).includes("deselected")) {
        if (event.deselected.length === 1) {
            const element = event.deselected[0];
            if (element.text === "") {
                element.set({text: PLACEHOLDER_TEXT, opacity: PLACEHOLDER_TEXT_OPACITY});
            } else if (element.text !== PLACEHOLDER_TEXT) {
                element.set({opacity: 1, width: 0});    // setting with to zero makes textbox width collapse to text
                for (let char of element.text) {
                    if (!ALLOWED_CHARACTERS.includes(char)) {
                        // only shows warning, won't prevent redemption
                        document.getElementById('weirdCharactersError').hidden = false;
                    }
                }
            }
        }
    }
}

function onPlaceholderTextEditing(event) {
    if (event.target === null) return;
    if (event.target === fabric_canvas.getActiveObject()) {
        document.getElementById('weirdCharactersError').hidden = true;
        const element = event.target;
        if (element.text === PLACEHOLDER_TEXT) {
            element.set({text: "", opacity: 1});
        }
    }
}

fabric_canvas.on('selection:cleared', onPlaceholderTextDeselect);
fabric_canvas.on('selection:updated', onPlaceholderTextDeselect);
fabric_canvas.on('mouse:down:before', onPlaceholderTextEditing);