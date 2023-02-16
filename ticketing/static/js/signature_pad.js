const canvas = document.getElementById("signature_pad");
const signaturePad = new SignaturePad(canvas, {
  minDistance: 1,
  minWidth: 0.7,
  maxWidth: 1.5
});

let signaturePadData = {};
let signaturePadDataBackup = {};    // to allow you to undo clearing
signaturePad.addEventListener("endStroke", () => {
    signaturePadData = signaturePad.toData();
});

// scale canvas for retina display
function resizeCanvas() {
    const ratio = 5;
    canvas.width = canvas.offsetWidth * ratio;
    canvas.height = canvas.offsetHeight * ratio;
    canvas.getContext("2d").scale(ratio, ratio);
    signaturePad.clear();
    if (Object.keys(signaturePadData).length) {
        signaturePad.fromData(signaturePadData);
    }
}
window.onresize = resizeCanvas;
resizeCanvas();

// clear button
document.getElementById("signature_pad_clear").addEventListener("click", () => {
    signaturePad.clear();
    if (Object.keys(signaturePadData).length) signaturePadDataBackup = signaturePadData;
    signaturePadData = {};
});

// undo button
document.getElementById("signature_pad_undo").addEventListener("click", () => {
    if (Object.keys(signaturePadData).length) {
        signaturePadData.pop(); // remove the last dot or line
        signaturePad.fromData(signaturePadData);
    } else if (Object.keys(signaturePadDataBackup).length) {
        signaturePad.fromData(signaturePadDataBackup);
    }
});

// choosing handwritten template
document.getElementById('handwriting_template').addEventListener('change', (event) => {
    let template = event.target.value;
    if (Object.keys(templates).includes(template)) {
        const filename = (templates[template].filenameRedeem) ? templates[template].filenameRedeem : templates[template].filename;
        const filePath = `${static_path}templates/${filename}`;
        document.getElementById('signature_pad').style.background = `url("${filePath}") 0% 0%/600px 356px`;
    } else {
        document.getElementById('signature_pad').style.background = "#fdfdfd";
    }
})