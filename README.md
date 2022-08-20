# Valentine's Day Ticketing System
## Requirements
- Python 3.8+
- Django 4.0+
- ReportLab 3.6+
- CairoSVG 2.5+
- lxml 4.9+
- Intall custom fonts found in [the fonts folder](ticketing/static/fonts) into the OS font library.

## Overview of System
1. Prefects load the student timetables into the website.
2. Prefects generate codes for tickets using the website.
3. Prefects physically sell the codes to students.
4. Students visit the website to redeem the code. They generate a ticket by choosing a recipient and period (if special serenade), and writing a message (digital handwriting or typed). 
5. The website automatically sorts the tickets and assigns them into a group.
6. The website generates PDFs of the tickets for each group.
7. Prefects cut out the tickets from the PDFs and give them to the corresponding group.
8. On Valentine's Day, the delivery groups distribute the items and do the serenades!

## Step 1: Load the timetables of each year level
1. Ask a teacher to go on OneSchool and download the PDF timetables for each year level (and also teachers if necessary).
2. Convert PDFs to Excel files (using Adobe Acrobat is recommended).
3. Convert Excel files into CSV files.
4. Go to /students and upload the CSV files.
5. Refresh the website.

## Step 2: Create and Sell Ticket Codes
1. Go the /admin and create a new TicketPDF object (pick the item type and the number of codes you want for that item).
2. Ensure you pick an appropriate number of ticket codes to generate for each item (in 2022, there were ~800 chocolates, ~1500 roses, ~400 serenades, ~120 special serenades).
3. You should be redirected to a page of a PDF.
4. Print out all the PDFs and cut them out.
5. Repeat this for all item types (Chocolate, Rose, Serenade, Special Serenades)
6. Sell the individual ticket codes to the students.

## Step 3: Redeem Tickets (this step is for students not prefects)
1. Buy a ticket code from the prefects for the item type that you want (e.g. if you want a serenade, buy a serenade code).
2. Go to /redeem and enter your code.
3. If it's a special serenade, pick which period you want it in.
4. Find the recipient you want from the list.
5. Choose whether to handwrite or type your message.
6. In either case, pick which template you want to use.
7. If handwriting, just handwrite on the screen (Apple pens should work).
8. If typing, edit the "Placeholder" text on the template. You can resize and drag them around (but can't create more). To delete them, just remove all the text.
9. Press the redeem button!

## Step 4: Sort the Tickets
1. Go to /admin and create a TicketSortRequest object (with the settings you want). 
2. The website will automatically pick the optimal period for each ticket to be delivered in, and will distribute the tickets to each delivery group (i.e. the groups of serenaders and prefects who hand out the roses/chocolates).
3. You should be redirected to page listing all the delivery groups.
4. Here you generate the PDF for each group.
5. Down the PDFs for each group and print them all out (IMPORTANT: make sure to print double-sided flipped along the **horizontal** edge).
6. Cut them out and assign them to the corresponding delivery group (Recommended: when cutting out the tickets, cut along the long vertical line in the middle first, then the smaller horizontal ones so that the order is maintained).

## Step 5: VDay has arrived!
1. You know what to do.
