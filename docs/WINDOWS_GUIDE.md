# Windows ç”¨æˆ·ä½¿ç”¨æŒ‡å—

## WSLçŽ¯å¢ƒéƒ¨ç½²è¯´æ˜Ž

ç”±äºŽæ­¤PDFåŽ‹ç¼©å·¥å…·ä¾èµ–çš„å‘½ä»¤è¡Œå·¥å…·ï¼ˆ`pdftoppm`, `tesseract`, `recode_pdf`, `qpdf`ï¼‰ä¸»è¦åœ¨LinuxçŽ¯å¢ƒä¸­å¯ç”¨ï¼ŒWindowsç”¨æˆ·éœ€è¦é€šè¿‡WSLï¼ˆWindows Subsystem for Linuxï¼‰æ¥ä½¿ç”¨æœ¬å·¥å…·ã€‚

## 1. å®‰è£…WSL

### æ–¹æ³•ä¸€ï¼šä½¿ç”¨Windows 11/10çš„å†…ç½®å‘½ä»¤
```powershell
# åœ¨ç®¡ç†å‘˜PowerShellä¸­è¿è¡Œ
wsl --install

# æˆ–å®‰è£…æŒ‡å®šçš„Ubuntuç‰ˆæœ¬
wsl --install -d Ubuntu-24.04
```

### æ–¹æ³•äºŒï¼šé€šè¿‡Microsoft Store
1. æ‰“å¼€Microsoft Store
2. æœç´¢"Ubuntu 24.04 LTS"
3. ç‚¹å‡»å®‰è£…

## 2. é…ç½®WSL

### å¯åŠ¨WSL
```powershell
# å¯åŠ¨é»˜è®¤çš„Linuxå‘è¡Œç‰ˆ
wsl

# æˆ–å¯åŠ¨æŒ‡å®šç‰ˆæœ¬
wsl -d Ubuntu-24.04
```

### æ›´æ–°ç³»ç»Ÿ
```bash
sudo apt update && sudo apt upgrade -y
```

## 3. å®‰è£…é¡¹ç›®ä¾èµ–

### åœ¨WSLä¸­å®‰è£…Pythonå’Œpip
```bash
sudo apt install python3 python3-pip
```

### å¤åˆ¶é¡¹ç›®åˆ°WSL
```bash
# æ–¹æ³•1ï¼šç›´æŽ¥è®¿é—®Windowsæ–‡ä»¶ç³»ç»Ÿ
cd /mnt/c/Users/quying/Projects/pdf_compressor

# æ–¹æ³•2ï¼šå¤åˆ¶åˆ°WSLæ–‡ä»¶ç³»ç»Ÿï¼ˆæŽ¨èï¼‰
cp -r /mnt/c/Users/quying/Projects/pdf_compressor ~/pdf_compressor
cd ~/pdf_compressor
```

### è¿è¡Œå®‰è£…è„šæœ¬
```bash
# ç»™è„šæœ¬æ‰§è¡Œæƒé™
chmod +x install_dependencies.sh

# è¿è¡Œå®‰è£…è„šæœ¬
./install_dependencies.sh
```

## 4. éªŒè¯å®‰è£…

```bash
# æ£€æŸ¥ä¾èµ–
python3 main.py --check-deps

# è¿è¡Œæµ‹è¯•å·¥å…·
python3 test_tool.py
```

## 5. ä½¿ç”¨ç¤ºä¾‹

### å¤„ç†Windowsæ–‡ä»¶ç³»ç»Ÿä¸­çš„PDF
```bash
# å¤„ç†Cç›˜ä¸­çš„PDFæ–‡ä»¶
python3 main.py --input /mnt/c/Users/quying/Documents/test.pdf --output ./output --allow-splitting

# æ‰¹é‡å¤„ç†Windowsç›®å½•
python3 main.py --input /mnt/c/Users/quying/Documents/PDFs --output ./processed --allow-splitting
```

### ä½¿ç”¨å¿«é€Ÿè„šæœ¬
```bash
# ç»™å¿«é€Ÿè„šæœ¬æ‰§è¡Œæƒé™
chmod +x run.sh

# ä½¿ç”¨å¿«é€Ÿè„šæœ¬
./run.sh -s /mnt/c/Users/quying/Documents/test.pdf
./run.sh -s -o ./processed /mnt/c/Users/quying/Documents/PDFs
```

## 6. æ–‡ä»¶è·¯å¾„è¯´æ˜Ž

### Windowså’ŒWSLæ–‡ä»¶ç³»ç»Ÿå¯¹åº”å…³ç³»
- Windows `C:\` â†’ WSL `/mnt/c/`
- Windows `D:\` â†’ WSL `/mnt/d/`
- WSLä¸»ç›®å½• `~` â†’ Windows `\\wsl$\Ubuntu-24.04\home\username`

### ç¤ºä¾‹è·¯å¾„è½¬æ¢
```bash
# Windowsè·¯å¾„: C:\Users\quying\Projects\pdf_compressor\test.pdf
# WSLè·¯å¾„:     /mnt/c/Users/quying/Projects/pdf_compressor/test.pdf

# Windowsè·¯å¾„: D:\Documents\PDFs
# WSLè·¯å¾„:     /mnt/d/Documents/PDFs
```

## 7. æ€§èƒ½ä¼˜åŒ–å»ºè®®

### æ–‡ä»¶å­˜å‚¨ä½ç½®
```bash
# æŽ¨èï¼šå°†é¡¹ç›®å¤åˆ¶åˆ°WSLæ–‡ä»¶ç³»ç»Ÿä»¥èŽ·å¾—æ›´å¥½æ€§èƒ½
cp -r /mnt/c/Users/quying/Projects/pdf_compressor ~/pdf_compressor

# å¤„ç†å¤§æ–‡ä»¶æ—¶ï¼Œå»ºè®®è¾“å‡ºä¹Ÿåœ¨WSLæ–‡ä»¶ç³»ç»Ÿ
python3 main.py --input /mnt/c/path/to/large.pdf --output ~/output --allow-splitting
```

### å†…å­˜å’Œå­˜å‚¨
- ç¡®ä¿WSLæœ‰è¶³å¤Ÿçš„å†…å­˜åˆ†é…ï¼ˆåœ¨`.wslconfig`ä¸­é…ç½®ï¼‰
- ä¸ºä¸´æ—¶æ–‡ä»¶é¢„ç•™è¶³å¤Ÿçš„ç£ç›˜ç©ºé—´

## 8. æ•…éšœæŽ’é™¤

### WSLç›¸å…³é—®é¢˜
```powershell
# é‡å¯WSL
wsl --shutdown
wsl

# æŸ¥çœ‹WSLçŠ¶æ€
wsl --list --verbose

# è®¾ç½®é»˜è®¤ç‰ˆæœ¬
wsl --set-default Ubuntu-24.04
```

### æƒé™é—®é¢˜
```bash
# ç¡®ä¿æ–‡ä»¶æœ‰æ­£ç¡®æƒé™
chmod +x *.sh
chmod +x *.py
```

### è·¯å¾„é—®é¢˜
```bash
# ä½¿ç”¨ç»å¯¹è·¯å¾„é¿å…è·¯å¾„é”™è¯¯
python3 main.py --input "$(pwd)/test.pdf" --output "$(pwd)/output"
```

## 9. WSLé…ç½®æ–‡ä»¶

### åˆ›å»º `.wslconfig` æ–‡ä»¶
åœ¨Windowsç”¨æˆ·ç›®å½•ä¸‹åˆ›å»º `C:\Users\quying\.wslconfig`ï¼š

```ini
[wsl2]
memory=4GB
processors=2
swap=2GB
```

### åº”ç”¨é…ç½®
```powershell
# é‡å¯WSLä»¥åº”ç”¨æ–°é…ç½®
wsl --shutdown
wsl
```

## 10. å®Œæ•´å·¥ä½œæµç¨‹ç¤ºä¾‹

```bash
# 1. è¿›å…¥WSL
wsl

# 2. åˆ‡æ¢åˆ°é¡¹ç›®ç›®å½•
cd ~/pdf_compressor

# 3. æ£€æŸ¥ä¾èµ–ï¼ˆåº”è¯¥å…¨éƒ¨é€šè¿‡ï¼‰
python3 main.py --check-deps

# 4. å¤„ç†Windowsä¸­çš„PDFæ–‡ä»¶
python3 main.py --input /mnt/c/Users/quying/Documents/ç”³æŠ¥ææ–™.pdf \
                --output ~/output \
                --allow-splitting \
                --verbose

# 5. æŸ¥çœ‹ç»“æžœ
ls -la ~/output/

# 6. å¤åˆ¶ç»“æžœåˆ°Windows
cp ~/output/* /mnt/c/Users/quying/Documents/åŽ‹ç¼©åŽ/
```

## 11. è‡ªåŠ¨åŒ–è„šæœ¬

åˆ›å»ºä¸€ä¸ªWindowsæ‰¹å¤„ç†æ–‡ä»¶æ¥ç®€åŒ–æ“ä½œï¼š

```batch
@echo off
echo å¯åŠ¨PDFåŽ‹ç¼©å·¥å…·...
wsl -d Ubuntu-24.04 -e bash -c "cd ~/pdf_compressor && python3 main.py %*"
```

ä¿å­˜ä¸º `pdf_compress.bat`ï¼Œç„¶åŽå¯ä»¥åœ¨Windowsä¸­è¿™æ ·ä½¿ç”¨ï¼š
```cmd
pdf_compress.bat --input C:\path\to\file.pdf --output C:\path\to\output --allow-splitting
```

è¿™æ ·å°±å¯ä»¥åœ¨WindowsçŽ¯å¢ƒä¸­æ— ç¼ä½¿ç”¨WSLä¸­çš„PDFåŽ‹ç¼©å·¥å…·äº†ï¼
