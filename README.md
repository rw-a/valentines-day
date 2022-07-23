# Valentine's Day Ticketing System Backend
## Requirements
- Python 3.8+
- Django 4.0+
- ReportLab 3.6+
- CairoSVG 2.5+
- lxml 4.9+
- Intall custom fonts found in [the fonts folder](ticketing/static/fonts) into the OS font library.
## How the System Works
1. Prefects generate codes for tickets using the website.
2. Prefects physically sell the codes to students.
3. Students visit the website to redeem the code. They generate a ticket by choosing a recipient and period (if special serenade). 
4. The website automatically sorts the tickets and assigns them into a group.
5. The website generates PDFs of the tickets for each group.
6. Prefects cut out the tickets from the PDFs and give them to the corresponding group.
7. On Valentine's Day, the delivery groups distribute the items and do the serenades!
## Details
 - When printing the ticket PDFs, make sure to print double-sided **flipped along the horizontal edge**.
 - When cutting out the tickets, cut along the long vertical line in the middle first, then the smaller horizontal ones so that the order is maintained.
