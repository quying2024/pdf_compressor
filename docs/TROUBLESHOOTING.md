# æ•…éšœæŽ’é™¤æŒ‡å—

## å®‰è£…ç›¸å…³é—®é¢˜

### 1. pipxç›¸å…³é—®é¢˜

#### é—®é¢˜ï¼šæ‰¾ä¸åˆ°recode_pdfå‘½ä»¤
```bash
bash: recode_pdf: command not found
```

**è§£å†³æ–¹æ¡ˆï¼š**
```bash
# æ–¹æ³•1ï¼šç¡®ä¿pipxè·¯å¾„åœ¨PATHä¸­
pipx ensurepath
source ~/.bashrc

# æ–¹æ³•2ï¼šæ‰‹åŠ¨æ·»åŠ åˆ°PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# æ–¹æ³•3ï¼šé‡æ–°å®‰è£…
pipx uninstall archive-pdf-tools
pipx install archive-pdf-tools
```

#### é—®é¢˜ï¼špipxæœªå®‰è£…
```bash
bash: pipx: command not found
```

**è§£å†³æ–¹æ¡ˆï¼š**
```bash
# Ubuntu 22.04+
sudo apt install pipx

# Ubuntu 20.04æˆ–æ›´æ—©ç‰ˆæœ¬
sudo apt install python3-pip
pip3 install --user pipx
export PATH="$HOME/.local/bin:$PATH"
```

#### é—®é¢˜ï¼špipxå®‰è£…å¤±è´¥
```bash
pipx install archive-pdf-tools
# å‡ºçŽ°æƒé™æˆ–ä¾èµ–é”™è¯¯
```

**å¤‡é€‰æ–¹æ¡ˆï¼š**
```bash
# ä½¿ç”¨pipç”¨æˆ·å®‰è£…
pip3 install --user archive-pdf-tools

# ä½¿ç”¨è™šæ‹ŸçŽ¯å¢ƒ
python3 -m venv ~/pdf_env
source ~/pdf_env/bin/activate
pip install archive-pdf-tools
```

### 2. ç³»ç»Ÿå·¥å…·é—®é¢˜

#### é—®é¢˜ï¼štesseractè¯­è¨€åŒ…é—®é¢˜
```bash
Error: Tesseract couldn't load any languages!
```

**è§£å†³æ–¹æ¡ˆï¼š**
```bash
# é‡æ–°å®‰è£…è¯­è¨€åŒ…
sudo apt install --reinstall tesseract-ocr-chi-sim tesseract-ocr-chi-tra

# æ£€æŸ¥è¯­è¨€åŒ…
tesseract --list-langs

# å¦‚æžœä»æœ‰é—®é¢˜ï¼Œå®‰è£…æ‰€æœ‰è¯­è¨€åŒ…
sudo apt install tesseract-ocr-all
```

#### é—®é¢˜ï¼špoppler-utilsç‰ˆæœ¬é—®é¢˜
```bash
pdftoppm: error while loading shared libraries
```

**è§£å†³æ–¹æ¡ˆï¼š**
```bash
# æ›´æ–°ç³»ç»Ÿå’Œé‡æ–°å®‰è£…
sudo apt update && sudo apt upgrade
sudo apt install --reinstall poppler-utils

# æ£€æŸ¥ç‰ˆæœ¬
pdftoppm -v
```

### 3. æƒé™é—®é¢˜

#### é—®é¢˜ï¼šæ— æ³•å†™å…¥è¾“å‡ºç›®å½•
```bash
Permission denied: '/path/to/output'
```

**è§£å†³æ–¹æ¡ˆï¼š**
```bash
# æ£€æŸ¥ç›®å½•æƒé™
ls -la /path/to/output

# ä¿®æ”¹æƒé™
chmod 755 /path/to/output

# æˆ–ä½¿ç”¨ç”¨æˆ·ä¸»ç›®å½•
python3 main.py --input test.pdf --output ~/output --allow-splitting
```

#### é—®é¢˜ï¼šä¸´æ—¶æ–‡ä»¶æƒé™é—®é¢˜
```bash
PermissionError: [Errno 13] Permission denied: '/tmp/...'
```

**è§£å†³æ–¹æ¡ˆï¼š**
```bash
# æ¸…ç†ä¸´æ—¶æ–‡ä»¶
sudo rm -rf /tmp/pdf_compressor_*

# æ£€æŸ¥/tmpæƒé™
ls -la /tmp | grep pdf_compressor

# è®¾ç½®çŽ¯å¢ƒå˜é‡ä½¿ç”¨å…¶ä»–ä¸´æ—¶ç›®å½•
export TMPDIR=~/tmp
mkdir -p ~/tmp
```

## è¿è¡Œæ—¶é—®é¢˜

### 1. å†…å­˜ä¸è¶³

#### ç—‡çŠ¶ï¼š
- è¿›ç¨‹è¢«æ€æ­»
- ç³»ç»Ÿå˜æ…¢
- "Killed"æ¶ˆæ¯

**è§£å†³æ–¹æ¡ˆï¼š**
```bash
# æ£€æŸ¥å†…å­˜ä½¿ç”¨
free -h
htop

# å¤„ç†å°æ–‡ä»¶æˆ–å‡å°‘å¹¶å‘
python3 main.py --input small_file.pdf --output ./output

# å¢žåŠ swapç©ºé—´ï¼ˆå¦‚æžœå¯èƒ½ï¼‰
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 2. ç£ç›˜ç©ºé—´ä¸è¶³

#### ç—‡çŠ¶ï¼š
- "No space left on device"
- å¤„ç†ä¸­æ–­

**è§£å†³æ–¹æ¡ˆï¼š**
```bash
# æ£€æŸ¥ç£ç›˜ç©ºé—´
df -h

# æ¸…ç†æ—§çš„æ—¥å¿—å’Œä¸´æ—¶æ–‡ä»¶
rm -rf logs/*.log.old
rm -rf /tmp/pdf_compressor_*

# ä½¿ç”¨å…¶ä»–ç£ç›˜ä½ç½®
python3 main.py --input test.pdf --output /mnt/d/output
```

### 3. å¤„ç†è¶…æ—¶

#### ç—‡çŠ¶ï¼š
- é•¿æ—¶é—´æ— å“åº”
- è¿›ç¨‹æŒ‚èµ·

**è§£å†³æ–¹æ¡ˆï¼š**
```bash
# ä½¿ç”¨è¯¦ç»†æ¨¡å¼ç›‘æŽ§è¿›åº¦
python3 main.py --input test.pdf --output ./output --verbose

# å‡å°æ–‡ä»¶æˆ–é¢„å…ˆæ‹†åˆ†
# æ£€æŸ¥æ–‡ä»¶æ˜¯å¦æŸå
pdfinfo test.pdf
```

## WSLç‰¹å®šé—®é¢˜

### 1. æ–‡ä»¶è·¯å¾„é—®é¢˜

#### é—®é¢˜ï¼šæ‰¾ä¸åˆ°Windowsæ–‡ä»¶
```bash
No such file or directory: '/mnt/c/...'
```

**è§£å†³æ–¹æ¡ˆï¼š**
```bash
# æ£€æŸ¥WSLæŒ‚è½½
ls /mnt/c/

# ç¡®ä¿WSL2é…ç½®æ­£ç¡®
wsl --list --verbose

# ä½¿ç”¨æ­£ç¡®çš„è·¯å¾„æ ¼å¼
python3 main.py --input "/mnt/c/Users/username/Documents/file.pdf"
```

### 2. æ€§èƒ½é—®é¢˜

#### é—®é¢˜ï¼šè·¨æ–‡ä»¶ç³»ç»Ÿè®¿é—®æ…¢

**è§£å†³æ–¹æ¡ˆï¼š**
```bash
# å¤åˆ¶æ–‡ä»¶åˆ°WSLæ–‡ä»¶ç³»ç»Ÿ
cp /mnt/c/path/to/file.pdf ~/input/
python3 main.py --input ~/input/file.pdf --output ~/output

# å¤„ç†å®ŒæˆåŽå¤åˆ¶å›žWindows
cp ~/output/* /mnt/c/Users/username/Documents/
```

### 3. ç¼–ç é—®é¢˜

#### é—®é¢˜ï¼šä¸­æ–‡æ–‡ä»¶åä¹±ç 

**è§£å†³æ–¹æ¡ˆï¼š**
```bash
# è®¾ç½®æ­£ç¡®çš„locale
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# æ°¸ä¹…è®¾ç½®
echo 'export LANG=zh_CN.UTF-8' >> ~/.bashrc
echo 'export LC_ALL=zh_CN.UTF-8' >> ~/.bashrc
```

## è°ƒè¯•æŠ€å·§

### 1. å¯ç”¨è¯¦ç»†æ—¥å¿—
```bash
python3 main.py --input test.pdf --output ./output --verbose
```

### 2. æ£€æŸ¥ä¸­é—´æ–‡ä»¶
```bash
# ä¿®æ”¹ä»£ç ä¸­çš„KEEP_INTERMEDIATE_FILESä¸ºTrue
# åœ¨config.pyä¸­è®¾ç½®ï¼š
KEEP_INTERMEDIATE_FILES = True
```

### 3. é€æ­¥è°ƒè¯•
```bash
# å…ˆæµ‹è¯•å•ä¸ªç»„ä»¶
pdftoppm -tiff -r 300 test.pdf page
tesseract page-01.tif output -l chi_sim hocr
```

### 4. ä½¿ç”¨æµ‹è¯•å·¥å…·
```bash
# è¿è¡Œå®Œæ•´çš„å·¥å…·æ£€æŸ¥
python3 test_tool.py

# æ£€æŸ¥ç‰ˆæœ¬ä¿¡æ¯
python3 test_tool.py --versions

# åˆ›å»ºæµ‹è¯•çŽ¯å¢ƒ
python3 test_tool.py --create-test
```

## èŽ·å–å¸®åŠ©

### 1. æŸ¥çœ‹æ—¥å¿—
```bash
# æŸ¥çœ‹æœ€æ–°æ—¥å¿—
tail -f logs/process.log

# æœç´¢é”™è¯¯ä¿¡æ¯
grep ERROR logs/process.log
```

### 2. æ”¶é›†ç³»ç»Ÿä¿¡æ¯
```bash
# ç³»ç»Ÿç‰ˆæœ¬
lsb_release -a

# å·¥å…·ç‰ˆæœ¬
python3 test_tool.py --versions

# çŽ¯å¢ƒå˜é‡
echo $PATH
echo $TMPDIR
```

### 3. é‡ç½®çŽ¯å¢ƒ
```bash
# å®Œå…¨é‡æ–°å®‰è£…
pipx uninstall archive-pdf-tools
sudo apt remove --purge tesseract-ocr poppler-utils qpdf
sudo apt autoremove

# é‡æ–°è¿è¡Œå®‰è£…è„šæœ¬
./install_dependencies.sh
```
