# Wplace Timelaps

This is a simple python project to generate wplace timelapeses, it requires FFmpeg to be installed

Sample config: 
```json
{
    "interval" : 1800,
    "imageSaveDir": "images/",
    "videoSaveDir": "videos/",
    "location": {
        "start": [1017, 626, 189, 373],
        "end": [1019, 627, 380, 961]
    }
}
```


Running:
Verify you have all packages required
```bash
pip install --requirements
```
Then, just run the main file:
```bash
python main.py
```