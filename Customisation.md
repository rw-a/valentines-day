# Customising the Tickets
If you make a mistake, it's usually quite easy to revert back to a previous state. If you need to do so, please contact me. If you successfully make any changes, also please contact me so that I can save them - that way, if someone else down the line wants to make changes, they can revert back to the changes you made (so all the progress you made isn't wasted).

## Adding/Changing Pickup Lines
The pickup lines are stored at *ticketing/static/pickup_lines.txt*. Each new line in the text file corresponds to a different pickup line. If you are adding new pickup lines, simply add each one to a new line. Ensure that they aren't too long or else they may cause weird formatting when printed. To remove pickup lines, simply delete the entire line in the text file. Ensure that there are no empty rows (check the last line in particular for a sneaky blank row), or else some tickets may be blank.

Once you have made your changes, go to the [pythonanywhere](https://www.pythonanywhere.com/user/statehigh/) and press the *$Bash* button below the *New console* heading. Then type the following into the bash console:
```
cd valentines-day/
python manage.py collectstatic
yes
```

## Adding/Changing Fonts
1. Download the font you want as a .tff file.
2. Add the file to *ticketing/static/fonts/*.
3. Open *ticketing/static/css/redeem.css* and register the font file by adding the following piece of code somewhere. Note that font-family is the name of the font is, and src is the name of the file (spaces need to have a backslash before them, as shown).

```
@font-face {
    font-family: "New Font";
    src: url("../fonts/New\ Font.ttf");
}
```

4. Open *ticketing/templates/ticketing/redeem.html* and navigate to the JavaScript section. Locate the variable that is a of fonts and add your new font to the list (the name that you chose for font-family, not the filename).

```
...
let fonts = ["Calibri", "Chasing Hearts", "Delique", "Heartales", "Hello Valentine", "La Rosse", "Love Letters", "Roschetta", "New Font"];
...
```

## Adding/Changing Ticket Templates
1. Download [this Word document](https://github.com/rw-a/valentines-day/blob/master/Classic%20Template.docx), which was used to create the classic template.
2. Modify the template to create your own! Note: It's very important that you don't change the size of each cell in the table (actually, the size isn't critical but the width must be exactly 1.68x longer than the height).
3. Export the Word document as a PDF.
4. After this point, things get a little more technical, so feel free to ask me to do the rest.
5. Convert the PDF into an SVG file using [Inkscape](https://inkscape.org/).
6. Add the SVG file to the templates folder, which is located at *ticketing/static/templates/*
7. Update the code to load in this new template. These next steps will be in separate headings below:

#### Step 8: Add the template to the list of options on the redeem website
Open *ticketing/forms.py* and locate *TicketForm* class. Then locate the *templates* field of this class. Add your new template to the list. Note that the number represents the ID of the template and should be ascending. In subsequent steps, the ID will be used to identify the template, not the name.

Before:
```
class TicketForm(forms.Form):
    ...
    templates = [
        (1, "Classic Ticket"),
    ]
    ...
```
After (assuming you want your new template to be called *Modern Ticket*):
```
class TicketForm(forms.Form):
    ...
    templates = [
        (1, "Classic Ticket"),
        (2, "Modern Ticket"),
    ]
    ...
```
#### Step 9: Register the template to the options for handwriting
Open *ticketing/templates/ticketing/redeem.html* and navigate to the JavaScript section. Add the template to the *if else* chain. Note that you use the ID of the template. You need to update the filename accordingly.

Before:
```
...
document.getElementById('id_handwriting_template').addEventListener('change', (event) => {
    let template = event.target.value;
        if (template == "0") {
            document.getElementById('signature_pad').style.background = "#fdfdfd";
        } else if (template == "1") {
            document.getElementById('signature_pad').style.background = "url({% static 'templates/classic_template.svg' %}) 0% 0%/600px 356px";
        }
})
...
```

After (assuming you named your file *modern_template.svg*):
```
...
document.getElementById('id_handwriting_template').addEventListener('change', (event) => {
    let template = event.target.value;
        if (template == "0") {
            document.getElementById('signature_pad').style.background = "#fdfdfd";
        } else if (template == "1") {
            document.getElementById('signature_pad').style.background = "url({% static 'templates/classic_template.svg' %}) 0% 0%/600px 356px";
        } else if (template == "2") {
            document.getElementById('signature_pad').style.background = "url({% static 'templates/modern_template.svg' %}) 0% 0%/600px 356px";
        }
})
...
```

#### Step 10: Add the positions of customisable text to the template
Open *ticketing/templates/ticketing/redeem.html* and update the JavaScript. Add a new function below the function named *initialise_classic_template*. You will need to adjust the position of the text objects to fit your template by adjusting the numbers next to *left* and *top*. You may also need to decrease or increase the number of text objects. Follow the pattern shown for the classic template. You need to update the filename accordingly.

Before:
```
...
function initialise_classic_template() {
    load_background_image("{% static 'templates/classic_template.svg' %}", 'Calibri');
    let text1 = new fabric.IText('Placeholder', {left: 18, top: 60, fontSize: 30});
    let text2 = new fabric.IText('Placeholder', {left: 170, top: 164, fontSize: 30})
    let text3 = new fabric.IText('Placeholder', {left: 102, top: 212, fontSize: 30})
    let text4 = new fabric.IText('Placeholder', {left: 102, top: 260, fontSize: 30})
    let text5 = new fabric.IText('Placeholder', {left: 157, top: 308, fontSize: 30})
    fabric_canvas.add(text1, text2, text3, text4, text5);
}
...
```

After (assuming you named your file *modern_template.svg*):
```
...
function initialise_modern_template() {
    load_background_image("{% static 'templates/classic_template.svg' %}", 'Calibri');
    let text1 = new fabric.IText('Placeholder', {left: 18, top: 60, fontSize: 30});
    let text2 = new fabric.IText('Placeholder', {left: 170, top: 164, fontSize: 30});
    let text3 = new fabric.IText('Placeholder', {left: 102, top: 212, fontSize: 30});
    let text4 = new fabric.IText('Placeholder', {left: 102, top: 260, fontSize: 30});
    let text5 = new fabric.IText('Placeholder', {left: 157, top: 308, fontSize: 30});
    fabric_canvas.add(text1, text2, text3, text4, text5);
}

function initialise_modern_template() {
    load_background_image("{% static 'templates/modern_template.svg' %}", 'Calibri');
    let text1 = new fabric.IText('Placeholder', {left: 20, top: 80, fontSize: 30});
    let text2 = new fabric.IText('Placeholder', {left: 180, top: 154, fontSize: 30});
    let text3 = new fabric.IText('Placeholder', {left: 122, top: 192, fontSize: 30});
    let text4 = new fabric.IText('Placeholder', {left: 152, top: 230, fontSize: 30});
    let text5 = new fabric.IText('Placeholder', {left: 177, top: 270, fontSize: 30});
    let text6 = new fabric.IText('Placeholder', {left: 207, top: 310, fontSize: 30});
    fabric_canvas.add(text1, text2, text3, text4, text5, text6);
}
...
```

#### Step 11: Register the template to the options for keyboard input
Add the function you just created above to the list within the *initialise_template* function.

What it looks like before:
```
...
function initialise_template() {
    template = document.getElementById('id_typed_template').value;
    if (template == 1) {
        initialise_classic_template();
    }
}
...
```

Example (assuming that you named the function above as *initialise_modern_template*):
```
...
function initialise_template() {
    template = document.getElementById('id_typed_template').value;
    if (template == 1) {
        initialise_classic_template();
    } else if (template == 2) {
        initialise_modern_template();
    }
}
...
```

#### Step 12: Register the template to the ticket-to-pdf converter
Open *ticketing/ticket_printer.py* and locate the *TicketsToPDF* class. Then locate the *_init_* method inside it (should be the first one). Locate the attribute for the classic template, and create another attribute corresponding to the new template. You need to update the filename accordingly.

Before:
```
...
class TicketsToPDF:
    def __init__(self, tickets, pdf_output_path: str, pdf_name: str):
        ...
        self.CLASSIC_TEMPLATE = PIL.Image.open(io.BytesIO(cairosvg.svg2png(
            url=f"{DirectoryLocations.STATIC}/templates/classic_template.svg", write_to=None,
            output_width=self.CANVAS_WIDTH * self.RATIO, output_height=self.CANVAS_HEIGHT * self.RATIO)))
        ...
...
```

After (assuming you named your file *modern_template.svg*):
```
...
class TicketsToPDF:
    def __init__(self, tickets, pdf_output_path: str, pdf_name: str):
        ...
        self.CLASSIC_TEMPLATE = PIL.Image.open(io.BytesIO(cairosvg.svg2png(
            url=f"{DirectoryLocations.STATIC}/templates/classic_template.svg", write_to=None,
            output_width=self.CANVAS_WIDTH * self.RATIO, output_height=self.CANVAS_HEIGHT * self.RATIO)))
        
        self.MODERN_TEMPLATE = PIL.Image.open(io.BytesIO(cairosvg.svg2png(
            url=f"{DirectoryLocations.STATIC}/templates/modern_template.svg", write_to=None,
            output_width=self.CANVAS_WIDTH * self.RATIO, output_height=self.CANVAS_HEIGHT * self.RATIO)))
        ...
...
```

#### Step 13: Register the template to the ticket-to-pdf converter (part 2)
Now scroll down to the *create_images* method inside the *TicketsToPDF* class. Add the attribute you just created above to the *if else* chain.

Before:
```
if ticket.template == 1:
    combined_image.alpha_composite(self.CLASSIC_TEMPLATE)
else:
    raise KeyError(f"Template number {ticket.template} does not exist.")
```

After (assuming that you named the attribute *self.MODERN_TEMPLATE* in the step above):
```
if ticket.template == 1:
    combined_image.alpha_composite(self.CLASSIC_TEMPLATE)
elif ticket.template == 2:
    combined_image.alpha_composite(self.MODERN_TEMPLATE)
else:
    raise KeyError(f"Template number {ticket.template} does not exist.")
```

**Whew! You're done!**
