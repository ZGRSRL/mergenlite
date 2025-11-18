# ⚠️ Alembic Config Fix (Manuel)

## Sorun

`mergen/api/alembic.ini` dosyasında `version_num_format = %04d` satırı Windows'ta sorun yaratabilir.

## Çözüm

Dosyayı açın ve 37. satırı şu şekilde değiştirin:

**Önce**:
```ini
version_num_format = %04d
```

**Sonra**:
```ini
version_num_format = %%04d
```

Veya tamamen kaldırın (default değer kullanılır):
```ini
# version_num_format = %04d
```

## Alternatif

Eğer hata devam ederse, `docker-compose.yml`'deki API komutunu şu şekilde değiştirin:

```yaml
command: bash -c "alembic upgrade head 2>/dev/null || echo 'Migration skipped' && uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

Bu şekilde migration hatası API'yi durdurmaz.

