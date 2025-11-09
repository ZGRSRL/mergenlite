# GitHub'a Yükleme Talimatları

## 📤 Projeyi GitHub'a Yükleme

### 1. Git Repository'yi Başlatma (Eğer başlatılmadıysa)

```bash
cd d:\Mergenlite
git init
```

### 2. Remote Repository Ekleme

```bash
git remote add origin https://github.com/ZGRSRL/mergenlite.git
```

Eğer remote zaten varsa:
```bash
git remote set-url origin https://github.com/ZGRSRL/mergenlite.git
```

### 3. Dosyaları Stage'e Ekleme

```bash
# Tüm dosyaları ekle
git add .

# Veya belirli dosyaları ekle
git add Dockerfile docker-compose.yml .dockerignore DOCKER_README.md .env.example README.md
```

### 4. Commit Oluşturma

```bash
git commit -m "Add Docker support and update documentation"
```

### 5. GitHub'a Push Etme

```bash
# İlk push (master branch için)
git push -u origin master

# Veya main branch kullanıyorsanız
git branch -M main
git push -u origin main
```

### 6. Eğer Remote'ta Değişiklikler Varsa

```bash
# Önce pull edin
git pull origin master --allow-unrelated-histories

# Sonra push edin
git push -u origin master
```

## 🔐 Authentication

GitHub'a push için authentication gereklidir:

### Personal Access Token (Önerilen)

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" tıklayın
3. `repo` scope'unu seçin
4. Token'ı kopyalayın
5. Push sırasında password yerine token kullanın

### SSH Key (Alternatif)

```bash
# SSH key oluştur
ssh-keygen -t ed25519 -C "your_email@example.com"

# Public key'i GitHub'a ekle
# GitHub → Settings → SSH and GPG keys → New SSH key
```

Sonra remote URL'i değiştirin:
```bash
git remote set-url origin git@github.com:ZGRSRL/mergenlite.git
```

## 📋 Yüklemeden Önce Kontrol Listesi

- [ ] `.env` dosyası `.gitignore`'da (sensitive data)
- [ ] `.env.example` dosyası oluşturuldu
- [ ] `Dockerfile` ve `docker-compose.yml` hazır
- [ ] `README.md` güncel
- [ ] Gereksiz dosyalar `.gitignore`'da
- [ ] API key'ler `.env` dosyasında (commit edilmeyecek)

## 🚀 GitHub Actions (CI/CD) - Opsiyonel

`.github/workflows/docker-build.yml` dosyası oluşturarak otomatik build ekleyebilirsiniz:

```yaml
name: Docker Build

on:
  push:
    branches: [ master, main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t mergenlite .
```

## 📝 Commit Mesajları İçin Öneriler

- `feat: Add Docker support`
- `docs: Update README with Docker instructions`
- `fix: Fix database connection in Docker`
- `chore: Add .dockerignore file`

## 🔄 Sonraki Adımlar

1. GitHub repository'yi kontrol edin: https://github.com/ZGRSRL/mergenlite
2. README.md'nin düzgün render edildiğini kontrol edin
3. Docker image'ı GitHub Container Registry'ye push edebilirsiniz (opsiyonel)
4. GitHub Pages veya başka bir hosting servisi kullanabilirsiniz

## 🐳 Docker Image'ı GitHub Container Registry'ye Push

```bash
# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build
docker build -t ghcr.io/zgrsrl/mergenlite:latest .

# Push
docker push ghcr.io/zgrsrl/mergenlite:latest
```

