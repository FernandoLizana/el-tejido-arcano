# Guía de desarrollo

1. Python ≥ 3.11. Instalación rápida: `.\setup.ps1` (Windows) o `./setup.sh` (Linux/macOS).
2. Añade ADN en `data/cards/` y valida.
3. No uses `print` en core; usa `logging`.
4. Type hints + Pydantic en bordes.
5. Tests en `tests/` sin red.
6. Config en YAML, no hardcode.
7. Cache embeddings por hash de contenido.
8. Documenta decisiones en `docs/`.
9. Scripts `extract_*.py` usan env vars / CLI para PDFs locales; no hardcodees rutas personales.
10. No commits de `.env`, PDFs ni extractos crudos de libros (ver `.gitignore`).

## Comandos útiles

```powershell
.\setup.ps1
.\env\Scripts\python.exe -m pytest tests -q
.\env\Scripts\python.exe scripts\validate_card_data.py
.\env\Scripts\python.exe scripts\rebuild_graph.py
.\env\Scripts\python.exe -m uvicorn api.main:app --reload
.\env\Scripts\python.exe -m streamlit run ui/app.py
```
