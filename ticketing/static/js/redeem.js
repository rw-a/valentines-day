/* INPUT VALIDATION */
let is_special = false;
async function submit_form(event) {
    document.getElementById('errors').hidden = true;

    // these are stored in variables first to prevent short-circuiting
    let valid_code = await is_valid_code(null);
    let valid_period = is_valid_period();
    let valid_recipient = is_valid_recipient();
    let valid_content;
    if (document.getElementById('is_handwritten').value === "True") {
        valid_content = is_valid_handwriting();
    } else {
        valid_content = is_valid_typed();
    }

    if (valid_code && valid_period && valid_recipient && valid_content) {
        let template;
        let message;
        if (document.getElementById('is_handwritten').value === "True") {
            template = document.getElementById('handwriting_template').value;
            message = await dataURLToBlob(signaturePad.toDataURL("image/svg+xml")).text();
        } else {
            fabric_canvas.backgroundImage = null;

            // remove placeholder text
            for (let object of fabric_canvas.getObjects()) {
                if (object.text === PLACEHOLDER_TEXT) {
                    object.set({text: ""});
                }
            }

            template = document.getElementById('typed_template').value;
            message = fabric_canvas.toSVG();
        }

        const response = await fetch(redeem_api_path, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                "X-CSRFToken": csrf_token
        },
            credentials: 'same-origin',
            body: JSON.stringify({
                recipient_id: document.getElementById('recipient').value,
                is_handwritten: document.getElementById('is_handwritten').value,
                template: template,
                code: document.getElementById('code').value,
                message: message,
                period: document.getElementById('period').value,
            }),
        });
        if (!response.ok) {
            document.getElementById('errors').innerText = `Error ${response.status}: ${response.statusText}.\n 
                Please try again in private/incognito browsing mode. If that doesn't work, you can contact ${contact_email}`;
            document.getElementById('errors').hidden = false;
            return;
        }
        const data = await response.json();
        if (data["success"] === "true") {
            window.location.href = redeemed_url;
        } else {
            document.getElementById('errors').innerText = `Error: ${data['error']}`;
            document.getElementById('errors').hidden = false;
        }
    }
}

// btw this is also verified in the backend
async function is_valid_code(event) {
    document.getElementById('codeError').hidden = false;
    is_special = false;

    let inputted_code = document.getElementById('code').value;
    if (inputted_code.length === 10) {
        let response = await fetch(validate_code_url + "?" + new URLSearchParams({inputted_code}))
        let data = await response.json();
        if (data.is_exists) {
            if (data.is_unconsumed) {
                document.getElementById('codeError').innerText = data.item_type;
                document.getElementById('codeError').style.color = '#71d16d';
                if (data.item_type === "Special Serenade") is_special = true;
                updatePeriodSelector();
                return true;
            } else {
                document.getElementById('codeError').innerText = "Code has already been used.";
                document.getElementById('codeError').style.color = 'red';
                updatePeriodSelector();
                return false;
            }
        } else {
            document.getElementById('codeError').innerText = "Code doesn't exist.";
            document.getElementById('codeError').style.color = 'red';
            updatePeriodSelector();
            return false;
        }
    } else {
        document.getElementById('codeError').innerText = "Code must be exactly 10 characters long.";
        document.getElementById('codeError').style.color = 'red';
        updatePeriodSelector();
    }
}

function updatePeriodSelector() {
    document.getElementById('periodForm').hidden = !is_special;
}

function is_valid_period() {
    if (is_special) {
        let period = document.getElementById('period').value;
        if (period >= 1 && period <= 4) {
            document.getElementById('periodError').hidden = true;
            return true;
        } else {
            document.getElementById('periodError').hidden = false;
            return false;
        }
    } else {
        return true;
    }
}

function is_valid_recipient() {
    // check if the user actually inputted someone
    let recipient = document.getElementById('recipient').value;
    if (recipient.length > 3) {
        document.getElementById('recipientError').hidden = true;
        return true;
    } else {
        document.getElementById('recipientError').hidden = false;
        return false;
    }
}

function is_valid_handwriting() {
    if (signaturePad.isEmpty()) {
        document.getElementById('handwritingError').hidden = false;
        return false;
    } else {
        document.getElementById('handwritingError').hidden = true;
        return true;
    }
}

function is_valid_typed() {
    fabric_canvas.discardActiveObject();
    // typing is valid if there is at least one text box that isn't placeholder text
    for (let object of fabric_canvas.getObjects()) {
        if (object.text !== PLACEHOLDER_TEXT) {
            clearFabricErrors();
            return true;
        }
    }
    document.getElementById('typedError').hidden = false;
    return false;
}

function dataURLToBlob(dataURL) {
  const parts = dataURL.split(';base64,');
  const contentType = parts[0].split(":")[1];
  const raw = window.atob(parts[1]);
  const rawLength = raw.length;
  const uInt8Array = new Uint8Array(rawLength);

  for (let i = 0; i < rawLength; ++i) {
    uInt8Array[i] = raw.charCodeAt(i);
  }

  return new Blob([uInt8Array], { type: contentType });
}

// only allow letters in code input and automatically make uppercase
document.getElementById('code').addEventListener('input', (event) => {
    let inputted_code = event.target.value;
    inputted_code = inputted_code.toUpperCase();
    inputted_code = inputted_code.replace(/[^a-z]/gi, '');
    event.target.value = inputted_code;
});

document.getElementById('code').addEventListener('input', is_valid_code);
document.getElementById('redeem').addEventListener('click', submit_form);

/* CHOOSING CONTENT MODE AND TEMPLATE*/
document.getElementById('is_handwritten').addEventListener('change', () => {
    if (event.target.value === "True") {
        document.getElementById('formTyped').hidden = true;
        document.getElementById('formHandwriting').hidden = false;
    } else {
        document.getElementById('formTyped').hidden = false;
        document.getElementById('formHandwriting').hidden = true;
    }
})

const students_selector = document.getElementById('recipient');
const option = document.createElement("option");
option.value = "";
students_selector.add(option);
for (let student of students) {
    const option = document.createElement("option");
    option.value = student;
    students_selector.add(option);
}

const choices = new Choices('#recipient', {
    placeholderValue: "Select a person...",
    searchPlaceholderValue: "Search for a person...",
    itemSelectText: '',
    renderChoiceLimit: 100,
    shouldSort: false,
    searchResultLimit: 10,
});

const typed_template_selector = document.getElementById('typed_template');
const handwritten_template_selector = document.getElementById('handwriting_template');
for (let template of Object.keys(templates)) {
    const option_handwritten = document.createElement("option");
    option_handwritten.value = template;
    option_handwritten.innerText = template;
    handwritten_template_selector.add(option_handwritten);

    const option_typed = document.createElement("option");
    option_typed.value = template;
    option_typed.innerText = template;
    typed_template_selector.add(option_typed);
}