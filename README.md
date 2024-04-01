# bib-generator

Automatically generate DIN A5 (148 x 210) bibs for sports events. Text size is automatically adjusted to fit the bib. Supports custom fonts, headers and footers.

## Using csv file

- [Example file](data.dsv)



```bash
python3 .\main.py --data .\example\data.csv --footer .\example\footer.png  --output .\example\output\ --font .\example\agency_fb.ttf --header-offset 60 --seperator ';'
```

## Manual input

```bash
python3 .\bib.py --text LYLES --output .\example\output\Lyles.png --header .\example\globus.png --font .\example\agency_fb.ttf  --footer .\example\footer.png --header-offset 60--footer .\example\footer.png --header-offset 60
```

![image](https://github.com/nimarion/bib-generator/assets/23435250/5a7272fb-e5bb-4117-b3e0-b769daf06912)

