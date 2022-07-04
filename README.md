# Valentine's Day Ticketing System Backend
## Setup
- Requires Python
- Requires Django
- Requires ReportLab
## Function
1. Prefects generates codes for tickets using the website.
2. Prefects physically sell the codes to students.
3. Students visit the website to redeem the code. They generate a ticket by choosing a recipient and period (if special serenade).
4. Prefects use the website to generate a PDF/Word file using the inputted tickets by inputting the number of serenading/non-serenading groups. 
5. The website automatically sorts the tickets (using an algorithm which minimises travel distance and total number of visits required, while also maximising the number of visits an individual receives) and assigns them into a group.
6. Prefects print the generated tickets and give them to the corresponding groups.
7. On Valentine's Day, the prefects and groups distribute the items and do the serenades!
